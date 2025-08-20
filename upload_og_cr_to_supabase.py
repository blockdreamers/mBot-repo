import os
import re
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload_og_cr.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    encoding='utf-8'
)

# 환경 변수 로드
load_dotenv()

# API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

class OGCRQuestionUploader:
    def __init__(self, start_question_number: int = 147):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.start_question_number = start_question_number
        self.uploaded_count = 0
        self.failed_count = 0
        self.total_questions = 0
        self.openai_calls = 0
        self.openai_failures = 0

    def parse_og_cr_file(self, file_path: str) -> List[Dict]:
        """OG_CR_clean_answer.txt 파일을 파싱하여 문제 리스트로 변환"""

        logging.info(f"[INFO] {file_path} 파일 파싱 시작...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"[ERROR] 파일 읽기 오류: {e}")
            return []

        questions = []

        # 문제별로 분리 (숫자. 패턴으로 시작)
        # 620. Arts advocate... 620정답. B 621. 다음문제... 621정답. B 형태
        pattern = r'(\d{3})\.\s*(.*?)\1정답\.\s*([A-E])(?=\s*\d{3}\.\s*|$|\n\n)'
        matches = re.findall(pattern, content, re.DOTALL)

        logging.info(f"🔍 총 {len(matches)}개 문제 패턴 발견")

        for i, (question_num, question_content, answer) in enumerate(matches):
            question_num = int(question_num)

            # 620-801 범위만 처리
            if not (620 <= question_num <= 801):
                continue

            logging.info(f"✅ {question_num}번 문제 파싱 중... (정답: {answer})")

            # 보기 추출 (A. B. C. D. E. 패턴)
            choices = []
            choice_pattern = r'([A-E])\.\s*(.*?)(?=[A-E]\.\s+|$)'
            choice_matches = re.findall(choice_pattern, question_content, re.DOTALL)

            if len(choice_matches) != 5:
                logging.warning(f"⚠️ {question_num}번 문제의 보기가 5개가 아닙니다: {len(choice_matches)}개")
                # 5개가 아니어도 계속 진행
                pass

            # 보기 텍스트 정리
            for letter, choice_text in choice_matches:
                choices.append(choice_text.strip())

            # 문제 본문 추출 (보기들 이전까지)
            question_text = question_content
            for letter, choice_text in choice_matches:
                question_text = question_text.replace(f"{letter}. {choice_text}", "")
            question_text = question_text.strip()

            questions.append({
                'original_number': question_num,
                'question': question_text,
                'choices': choices,
                'answer': answer
            })

            logging.info(f"✅ {question_num}번 문제 파싱 완료 - 보기 {len(choices)}개")

        self.total_questions = len(questions)
        logging.info(f"📊 총 {self.total_questions}개 문제 파싱 완료")
        return questions

    def generate_explanation(self, question: str, choices: List[str], answer: str) -> Dict[str, str]:
        """OpenAI를 사용하여 한글/영문 설명 생성"""

        self.openai_calls += 1
        choices_text = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])

        prompt = f"""다음은 GMAT Critical Reasoning 문제입니다. 정답과 그 이유를 간략하게 설명해주세요.

문제: {question}

보기:
{choices_text}

정답: {answer}

요구사항:
1. 한국어 설명: 10줄 이내로 정답인 이유를 명확하게 설명
2. 영어 설명: 10줄 이내로 정답인 이유를 명확하게 설명
3. 형식은 반드시 다음과 같이 해주세요:

KOR:
[한국어 설명]

ENG:
[영어 설명]"""

        try:
            logging.info(f"🤖 OpenAI API 호출 시작 (질문 {len(question)}자)")

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 GMAT Critical Reasoning 문제 해설 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            explanation_text = response.choices[0].message.content.strip()
            logging.info(f"✅ OpenAI API 호출 성공 - 응답 길이: {len(explanation_text)}자")

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
            self.openai_failures += 1
            logging.error(f"❌ OpenAI API 오류: {e}")
            return {
                'korean': "설명 생성 중 오류가 발생했습니다.",
                'english': "An error occurred while generating explanation."
            }

    def upload_question(self, question_data: Dict, question_number: int) -> bool:
        """단일 문제를 Supabase에 업로드"""

        original_num = question_data['original_number']

        try:
            logging.info(f"📝 {original_num}번 문제 업로드 시작 (DB 번호: {question_number})")

            # OpenAI로 설명 생성
            explanations = self.generate_explanation(
                question_data['question'],
                question_data['choices'],
                question_data['answer']
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
                logging.info(f"✅ {original_num}번 문제 업로드 완료 (DB 번호: {question_number})")
                logging.info(f"   한국어 설명 길이: {len(explanations['korean'])}자")
                logging.info(f"   영어 설명 길이: {len(explanations['english'])}자")
                return True
            else:
                logging.error(f"❌ {original_num}번 문제 업로드 실패 - 응답 없음")
                self.failed_count += 1
                return False

        except Exception as e:
            logging.error(f"❌ {original_num}번 문제 처리 중 오류: {e}")
            self.failed_count += 1
            return False

    def upload_all_questions(self, questions: List[Dict]):
        """모든 문제를 순차적으로 업로드"""

        logging.info(f"\n🚀 {len(questions)}개 문제 업로드 시작...")
        logging.info("=" * 80)

        for i, question_data in enumerate(questions, 1):
            current_question_number = self.start_question_number + i - 1

            logging.info(f"\n📝 진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
            logging.info(f"원본 번호: {question_data['original_number']}번")
            logging.info(f"DB 번호: {current_question_number}")

            # 업로드 시도
            success = self.upload_question(question_data, current_question_number)

            if success:
                logging.info(f"✅ 성공 - DB에 저장됨")
            else:
                logging.error(f"❌ 실패 - DB 저장 실패")

            # API 제한 방지 및 진행 상황 조절
            time.sleep(2)

            # 5개마다 진행상황 요약
            if i % 5 == 0:
                logging.info(f"\n📊 중간 집계 ({i}개 처리)")
                logging.info(f"   성공: {self.uploaded_count}개")
                logging.info(f"   실패: {self.failed_count}개")
                logging.info(f"   OpenAI 호출: {self.openai_calls}회")
                logging.info(f"   OpenAI 실패: {self.openai_failures}회")
                if i > 0:
                    logging.info(f"   성공률: {self.uploaded_count/i*100:.1f}%")
                logging.info("-" * 40)

        # 최종 결과
        logging.info(f"\n🎉 업로드 완료!")
        logging.info("=" * 80)
        logging.info(f"📊 최종 결과:")
        logging.info(f"   총 문제 수: {len(questions)}개")
        logging.info(f"   성공: {self.uploaded_count}개")
        logging.info(f"   실패: {self.failed_count}개")
        logging.info(f"   OpenAI 호출: {self.openai_calls}회")
        logging.info(f"   OpenAI 실패: {self.openai_failures}회")
        if len(questions) > 0:
            logging.info(f"   성공률: {self.uploaded_count/len(questions)*100:.1f}%")

        if self.failed_count > 0:
            logging.warning(f"\n⚠️ {self.failed_count}개 문제가 실패했습니다.")
            logging.warning("upload_og_cr.log 파일을 확인하여 수동으로 재시도하거나 문제를 수정해주세요.")

def main():
    print("=" * 80)
    print("🎯 OG CR 문제 Supabase 업로드 스크립트")
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

    # OG CR 파일 확인
    og_cr_file = 'questionbank/OG_CR_2025/OG_CR_clean_answer.txt'
    if not os.path.exists(og_cr_file):
        print(f"❌ {og_cr_file} 파일을 찾을 수 없습니다.")
        return

    print(f"✅ {og_cr_file} 파일 확인 완료")

    # 시작 question_number 입력 받기
    start_num = 147
    print(f"📝 첫 번째 문제의 question_number: {start_num}")

    # 업로더 초기화
    uploader = OGCRQuestionUploader(start_question_number=start_num)

    try:
        # 문제 파싱
        questions = uploader.parse_og_cr_file(og_cr_file)

        if not questions:
            print("❌ 파싱된 문제가 없습니다.")
            return

        # 사용자 확인
        print(f"\n⚠️  {len(questions)}개 문제를 Supabase에 업로드하시겠습니까?")
        print(f"   - 첫 번째 문제: {questions[0]['original_number']}번 → DB {start_num}번")
        print(f"   - 마지막 문제: {questions[-1]['original_number']}번 → DB {start_num + len(questions) - 1}번")
        print("   - 각 문제마다 OpenAI API를 호출하므로 시간과 비용이 소요됩니다.")
        print("   - 상세 로그는 upload_og_cr.log 파일에 저장됩니다.")

        # 자동 진행
        print("🚀 업로드를 시작합니다...\n")

        # 모든 문제 업로드
        uploader.upload_all_questions(questions)

    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
        print(f"📊 현재까지 진행 상황:")
        print(f"   성공: {uploader.uploaded_count}개")
        print(f"   실패: {uploader.failed_count}개")
        print(f"   OpenAI 호출: {uploader.openai_calls}회")

    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print(f"📊 현재까지 진행 상황:")
        print(f"   성공: {uploader.uploaded_count}개")
        print(f"   실패: {uploader.failed_count}개")

if __name__ == "__main__":
    main()
