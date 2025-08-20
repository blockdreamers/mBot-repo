import os
import re
from supabase import create_client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # 서비스 롤 키 사용

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
    print("   .env 파일에 SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY를 추가하세요.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_lsat_file(file_path):
    """LSAT 파일을 파싱하여 문제별로 분리합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return []
    
    # 문제별로 분리 (숫자. 패턴으로)
    problems = re.split(r'(\d+\.)', content)
    
    parsed_problems = []
    
    for i in range(1, len(problems), 2):
        if i + 1 < len(problems):
            problem_num = int(problems[i].strip().replace('.', ''))
            problem_content = problems[i + 1].strip()
            
            if problem_content:
                # 지문과 보기 분리
                parts = problem_content.split('\n\n')
                
                if len(parts) >= 2:
                    passage = parts[0].strip()
                    choices_text = '\n\n'.join(parts[1:]).strip()
                    
                    # 보기 추출 (A), (B), (C), (D), (E) 패턴으로
                    choices = []
                    choice_pattern = r'\(([A-E])\)\s*(.*?)(?=\([A-E]\)|$)'
                    matches = re.findall(choice_pattern, choices_text, re.DOTALL)
                    
                    for letter, choice_text in matches:
                        # 앞뒤 공백 제거하고 정리
                        clean_choice = choice_text.strip()
                        choices.append(clean_choice)
                    
                    if len(choices) == 5:
                        parsed_problems.append({
                            'number': problem_num,
                            'passage': passage,
                            'choices': choices
                        })
                        print(f"✅ 문제 {problem_num} 파싱 완료")
                    else:
                        print(f"⚠️ 문제 {problem_num} 보기 수 오류: {len(choices)}개")
                else:
                    print(f"⚠️ 문제 {problem_num} 구조 오류")
    
    return parsed_problems

def upload_to_supabase(problems, start_q_number=1000):
    """파싱된 문제들을 Supabase에 업로드합니다."""
    
    print(f"\n=== Supabase 업로드 시작 (q_number: {start_q_number}~{start_q_number + len(problems) - 1}) ===")
    
    success_count = 0
    error_count = 0
    
    for i, problem in enumerate(problems):
        q_number = start_q_number + i
        
        try:
            # Supabase에 삽입할 데이터
            question_data = {
                'q_number': q_number,
                'type': 'LSAT',
                'question': problem['passage'],
                'choices': problem['choices'],  # (A) 뒷부분 텍스트만 저장
                'answer': '',  # 나중에 답안 파일로 업데이트
                'explanation': ''
            }
            
            # Supabase에 삽입
            result = supabase.table('questions').insert(question_data).execute()
            
            if result.data:
                print(f"✅ 문제 {problem['number']} -> q_number {q_number} 업로드 성공")
                success_count += 1
            else:
                print(f"❌ 문제 {problem['number']} 업로드 실패")
                error_count += 1
                
        except Exception as e:
            print(f"❌ 문제 {problem['number']} 업로드 오류: {e}")
            error_count += 1
    
    print(f"\n=== 업로드 완료 ===")
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")
    
    return success_count, error_count

def update_answers(answers_file, start_q_number=1000):
    """답안 파일을 읽어서 Supabase의 answer 필드를 업데이트합니다."""
    
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 답안 파일 읽기 오류: {e}")
        return
    
    # 답안 파싱
    answer_pattern = r'(\d+)\.\s*([A-E])'
    answers = re.findall(answer_pattern, content)
    
    print(f"\n=== 답안 업데이트 시작 ===")
    
    success_count = 0
    error_count = 0
    
    for problem_num, answer in answers:
        q_number = start_q_number + int(problem_num) - 1
        
        try:
            # answer 필드 업데이트
            result = supabase.table('questions').update({
                'answer': answer
            }).eq('q_number', q_number).execute()
            
            if result.data:
                print(f"✅ q_number {q_number} 답안 '{answer}' 업데이트 성공")
                success_count += 1
            else:
                print(f"❌ q_number {q_number} 답안 업데이트 실패")
                error_count += 1
                
        except Exception as e:
            print(f"❌ q_number {q_number} 답안 업데이트 오류: {e}")
            error_count += 1
    
    print(f"\n=== 답안 업데이트 완료 ===")
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")

def main():
    print("=" * 60)
    print("LSAT 문제 Supabase 업로드 스크립트")
    print("=" * 60)
    
    # 파일 경로
    lsat_file = 'questionbank/lsat/LSAT_02.txt'
    answers_file = 'questionbank/lsat/answers.txt'
    
    # 1. LSAT 파일 파싱
    print(f"1. LSAT 파일 파싱: {lsat_file}")
    problems = parse_lsat_file(lsat_file)
    
    if not problems:
        print("❌ 파싱된 문제가 없습니다.")
        return
    
    print(f"파싱된 문제 수: {len(problems)}개")
    
    # 2. Supabase 업로드
    print(f"\n2. Supabase 업로드")
    success_count, error_count = upload_to_supabase(problems, start_q_number=1000)
    
    if success_count == 0:
        print("❌ 업로드에 실패했습니다.")
        return
    
    # 3. 답안 업데이트 (답안 파일이 있는 경우)
    if os.path.exists(answers_file):
        print(f"\n3. 답안 업데이트: {answers_file}")
        update_answers(answers_file, start_q_number=1000)
    else:
        print(f"\n⚠️ 답안 파일을 찾을 수 없습니다: {answers_file}")
        print("   답안은 나중에 수동으로 업데이트하세요.")
    
    print(f"\n✅ LSAT 문제 업로드 완료!")
    print(f"   q_number 범위: 1000 ~ {1000 + len(problems) - 1}")
    print(f"   총 문제 수: {len(problems)}개")

if __name__ == "__main__":
    main() 