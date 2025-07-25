import os
import re
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

class CRQuestionUploader:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.uploaded_count = 0
        self.failed_count = 0
        self.total_questions = 0
        
    def parse_cr_questions(self, file_path: str) -> List[Dict]:
        """CR문제.txt 파일을 파싱하여 문제 리스트로 변환"""
        
        print(f"📖 {file_path} 파일 파싱 중...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 문제별로 분리 (141. ~ 289.)
        questions = []
        # 정답이 포함된 패턴: "문제번호. 내용... 문제번호. 정답 : X"
        question_pattern = r'(\d+)\.\s+(.+?)\1\.\s*정답\s*:\s*([A-E])'
        matches = re.findall(question_pattern, content, re.DOTALL)
        
        print(f"🔍 총 {len(matches)}개 문제 발견")
        
        for i, (question_num, question_content, answer_letter) in enumerate(matches):
            question_num = int(question_num)
            
            # 정답은 이미 패턴에서 추출됨
            print(f"✅ {question_num}번 문제 파싱 중... (정답: {answer_letter})")
            
            # 보기 추출
            choices = []
            choice_pattern = r'([A-E])\.\s+(.+?)(?=[A-E]\.\s+|$)'
            choice_matches = re.findall(choice_pattern, question_content, re.DOTALL)
            
            if len(choice_matches) != 5:
                print(f"⚠️ {question_num}번 문제의 보기가 5개가 아닙니다: {len(choice_matches)}개")
                continue
            
            # 보기 텍스트 정리
            for letter, choice_text in choice_matches:
                choices.append(f"{letter}. {choice_text.strip()}")
            
            # 문제 본문 추출 (보기 제거)
            question_text = question_content
            for letter, choice_text in choice_matches:
                question_text = question_text.replace(f"{letter}. {choice_text}", "")
            question_text = question_text.strip()
            
            # 정답을 문자 그대로 저장 (A, B, C, D, E)
            questions.append({
                'original_number': question_num,
                'question': question_text,
                'choices': choices,
                'answer': answer_letter,  # 문자로 저장
                'answer_letter': answer_letter
            })
            
            # print(f"✅ {question_num}번 문제 파싱 완료 (정답: {answer_letter})")  # 중복 제거
        
        self.total_questions = len(questions)
        print(f"📊 총 {self.total_questions}개 문제 파싱 완료")
        return questions
    
    def generate_explanation(self, question: str, choices: List[str], answer_letter: str) -> Dict[str, str]:
        """OpenAI를 사용하여 한글/영문 설명 생성"""
        
        choices_text = "\n".join(choices)
        
        prompt = f"""다음은 Critical Reasoning 문제입니다. 정답과 그 이유를 간략하게 설명해주세요.

문제: {question}

보기:
{choices_text}

정답: {answer_letter}

요구사항:
1. 한국어 설명: 3줄 이내로 정답인 이유를 명확하게 설명
2. 영어 설명: 3줄 이내로 정답인 이유를 명확하게 설명
3. 형식은 반드시 다음과 같이 해주세요:

KOR:
[한국어 설명]

ENG:
[영어 설명]"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 GMAT Critical Reasoning 문제 해설 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            explanation_text = response.choices[0].message.content.strip()
            
            # KOR/ENG 부분 분리
            kor_match = re.search(r'KOR:\s*(.+?)(?=ENG:|$)', explanation_text, re.DOTALL)
            eng_match = re.search(r'ENG:\s*(.+?)$', explanation_text, re.DOTALL)
            
            explanation_kor = kor_match.group(1).strip() if kor_match else "설명 생성 실패"
            explanation_eng = eng_match.group(1).strip() if eng_match else "Explanation generation failed"
            
            return {
                'korean': explanation_kor,
                'english': explanation_eng
            }
            
        except Exception as e:
            print(f"❌ OpenAI API 오류: {e}")
            return {
                'korean': "설명 생성 중 오류가 발생했습니다.",
                'english': "An error occurred while generating explanation."
            }
    
    def upload_question(self, question_data: Dict, question_number: int) -> bool:
        """단일 문제를 Supabase에 업로드"""
        
        try:
            # OpenAI로 설명 생성
            print(f"🤖 {question_data['original_number']}번 문제 설명 생성 중...")
            explanations = self.generate_explanation(
                question_data['question'],
                question_data['choices'],
                question_data['answer_letter']
            )
            
            # Supabase에 삽입할 데이터 준비
            insert_data = {
                'type': 'cr',
                'question': question_data['question'],
                'choices': question_data['choices'],
                'answer': question_data['answer'],
                'explanation': explanations['korean'],
                'explanation_en': explanations['english'],
                'question_number': question_number,
                'image_url': None,
                'latex_formula': None
            }
            
            # Supabase에 삽입
            result = self.supabase.table('questions').insert(insert_data).execute()
            
            if result.data:
                self.uploaded_count += 1
                print(f"✅ {question_data['original_number']}번 문제 업로드 완료 (DB 번호: {question_number})")
                print(f"   한국어 설명: {explanations['korean'][:100]}...")
                print(f"   영어 설명: {explanations['english'][:100]}...")
                return True
            else:
                print(f"❌ {question_data['original_number']}번 문제 업로드 실패")
                self.failed_count += 1
                return False
                
        except Exception as e:
            print(f"❌ {question_data['original_number']}번 문제 처리 중 오류: {e}")
            self.failed_count += 1
            return False
    
    def upload_all_questions(self, questions: List[Dict]):
        """모든 문제를 순차적으로 업로드"""
        
        print(f"\n🚀 {len(questions)}개 문제 업로드 시작...")
        print("=" * 80)
        
        for i, question_data in enumerate(questions, 1):
            print(f"\n📝 진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
            print(f"원본 번호: {question_data['original_number']}번")
            
            # 업로드 시도
            success = self.upload_question(question_data, i)
            
            if success:
                print(f"✅ 성공")
            else:
                print(f"❌ 실패")
            
            # API 율제한 방지를 위한 대기
            time.sleep(1)
            
            # 10개마다 진행상황 요약
            if i % 10 == 0:
                print(f"\n📊 중간 집계 ({i}개 처리)")
                print(f"   성공: {self.uploaded_count}개")
                print(f"   실패: {self.failed_count}개")
                print(f"   성공률: {self.uploaded_count/i*100:.1f}%")
                print("-" * 40)
        
        # 최종 결과
        print(f"\n🎉 업로드 완료!")
        print("=" * 80)
        print(f"📊 최종 결과:")
        print(f"   총 문제 수: {len(questions)}개")
        print(f"   성공: {self.uploaded_count}개")
        print(f"   실패: {self.failed_count}개")
        print(f"   성공률: {self.uploaded_count/len(questions)*100:.1f}%")
        
        if self.failed_count > 0:
            print(f"\n⚠️ {self.failed_count}개 문제가 실패했습니다.")
            print("로그를 확인하여 수동으로 재시도하거나 문제를 수정해주세요.")

def main():
    print("=" * 80)
    print("🎯 CR 문제 Supabase 업로드 스크립트")
    print("=" * 80)
    
    # 환경 변수 확인
    if not openai.api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=sk-proj-... 형태로 추가하세요.")
        return
    
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL이 설정되지 않았습니다.")
        print("   .env 파일에 SUPABASE_URL=https://your-project-id.supabase.co 형태로 추가하세요.")
        return
    
    if not SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 SUPABASE_SERVICE_ROLE_KEY=eyJh... 형태로 추가하세요.")
        return
    
    print("✅ 모든 API 키 및 URL 확인 완료")
    print(f"   Supabase URL: {SUPABASE_URL}")
    print(f"   OpenAI API Key: {openai.api_key[:20]}...")
    print(f"   Supabase Key: {SUPABASE_SERVICE_KEY[:20]}...")
    
    # CR문제 파일 확인
    cr_file = 'questionbank/cr/CR문제.txt'
    if not os.path.exists(cr_file):
        print(f"❌ {cr_file} 파일을 찾을 수 없습니다.")
        return
    
    print(f"✅ {cr_file} 파일 확인 완료")
    
    # 업로더 초기화
    uploader = CRQuestionUploader()
    
    try:
        # 문제 파싱
        questions = uploader.parse_cr_questions(cr_file)
        
        if not questions:
            print("❌ 파싱된 문제가 없습니다.")
            return
        
        # 사용자 확인
        print(f"\n⚠️  {len(questions)}개 문제를 Supabase에 업로드하시겠습니까?")
        print("각 문제마다 OpenAI API를 호출하므로 시간과 비용이 소요됩니다.")
        
        # 자동 진행 (스크립트이므로)
        print("🚀 업로드를 시작합니다...\n")
        
        # 모든 문제 업로드
        uploader.upload_all_questions(questions)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
        print(f"📊 현재까지 진행 상황:")
        print(f"   성공: {uploader.uploaded_count}개")
        print(f"   실패: {uploader.failed_count}개")
    
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print(f"📊 현재까지 진행 상황:")
        print(f"   성공: {uploader.uploaded_count}개")
        print(f"   실패: {uploader.failed_count}개")

if __name__ == "__main__":
    main() 