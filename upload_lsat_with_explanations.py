import os
import re
import openai
from supabase import create_client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not openai.api_key:
    print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
    exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
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
                # 보기 추출 (A), (B), (C), (D), (E) 패턴으로
                choices = []
                choice_pattern = r'\(([A-E])\)\s*(.*?)(?=\([A-E]\)|$)'
                matches = re.findall(choice_pattern, problem_content, re.DOTALL)
                
                if len(matches) == 5:
                    # 보기 부분을 정확히 제거하기 위해 정규식으로 찾은 위치를 기준으로 분리
                    first_choice_start = problem_content.find(f"({matches[0][0]})")
                    if first_choice_start != -1:
                        passage_and_question = problem_content[:first_choice_start].strip()
                    else:
                        # 보기 시작 위치를 찾을 수 없으면 전체에서 보기 텍스트 제거
                        choices_text = '\n'.join([f"({letter}) {text}" for letter, text in matches])
                        passage_and_question = problem_content.replace(choices_text, '').strip()
                    
                    # 보기 텍스트 정리 (A) 뒷부분만 저장
                    for letter, choice_text in matches:
                        clean_choice = choice_text.strip()
                        choices.append(clean_choice)
                    
                    parsed_problems.append({
                        'number': problem_num,
                        'passage': passage_and_question,  # 본문 + 질문 모두 포함
                        'choices': choices
                    })
                    print(f"✅ 문제 {problem_num} 파싱 완료")
                else:
                    print(f"⚠️ 문제 {problem_num} 보기 수 오류: {len(matches)}개")
    
    return parsed_problems

def generate_explanation_with_openai(question_data):
    """OpenAI를 사용해서 문제 해설을 생성합니다."""
    
    question = question_data['passage']
    choices = question_data['choices']
    answer = question_data['answer']
    
    # 정답 보기 찾기
    correct_choice = ""
    if answer and len(choices) >= ord(answer) - ord('A'):
        correct_choice = choices[ord(answer) - ord('A')]
    
    prompt = f"""다음은 LSAT 문제입니다. 정답과 오답에 대한 깊이 있는 해설을 국문과 영문으로 각각 10줄 이내로 작성해주세요.

문제: {question}

보기:
A) {choices[0] if len(choices) > 0 else ''}
B) {choices[1] if len(choices) > 1 else ''}
C) {choices[2] if len(choices) > 2 else ''}
D) {choices[3] if len(choices) > 3 else ''}
E) {choices[4] if len(choices) > 4 else ''}

정답: {answer}
정답 보기: {correct_choice}

다음 형식으로 해설을 작성해주세요:

[한국어 해설]
(정답에 대한 상세한 설명과 논리적 근거, 오답들이 틀린 이유, 문제 해결 과정 등을 10줄 이내로 깊이 있게 설명)

[English Explanation]
(Detailed explanation of the correct answer with logical reasoning, why other options are incorrect, problem-solving process, etc. within 10 lines)

중요한 점:
1. 정답이 왜 맞는지 논리적으로 설명
2. 오답들이 왜 틀렸는지 구체적으로 분석
3. 문제 해결에 필요한 핵심 개념이나 전략 설명
4. 10줄 이내로 깊이 있는 내용으로 작성
5. 국문과 영문 모두 동일한 수준의 상세함으로 작성

해설:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 LSAT 문제 해설 전문가입니다. 정답과 오답에 대한 깊이 있고 논리적인 해설을 제공하는 것이 목표입니다. 국문과 영문 모두 10줄 이내로 상세하게 설명하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content.strip()
        return explanation
        
    except Exception as e:
        print(f"❌ OpenAI API 오류: {e}")
        return None

def get_answers_from_file(answers_file):
    """답안 파일에서 답안을 읽어옵니다."""
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 답안 파일 읽기 오류: {e}")
        return {}
    
    # 답안 파싱
    answer_pattern = r'(\d+)\.\s*([A-E])'
    answers = re.findall(answer_pattern, content)
    
    answer_dict = {}
    for problem_num, answer in answers:
        answer_dict[int(problem_num)] = answer
    
    return answer_dict

def upload_to_supabase_with_explanations(problems, answers_dict, start_q_number=1000):
    """파싱된 문제들을 해설과 함께 Supabase에 업로드합니다."""
    
    print(f"\n=== Supabase 업로드 시작 (q_number: {start_q_number}~{start_q_number + len(problems) - 1}) ===")
    
    success_count = 0
    error_count = 0
    
    for i, problem in enumerate(problems):
        q_number = start_q_number + i
        problem_num = problem['number']
        
        print(f"\n처리 중: 문제 {problem_num} -> q_number {q_number}")
        
        # 답안 가져오기
        answer = answers_dict.get(problem_num, '')
        if not answer:
            print(f"⚠️ 문제 {problem_num} 답안을 찾을 수 없습니다.")
        
        # 해설 생성
        print(f"  해설 생성 중...")
        question_data = {
            'passage': problem['passage'],
            'choices': problem['choices'],
            'answer': answer
        }
        
        explanation = generate_explanation_with_openai(question_data)
        
        if not explanation:
            print(f"  ❌ 해설 생성 실패, 기본 해설 사용")
            explanation = f"[한국어 해설]\n정답: {answer}\n\n[English Explanation]\nAnswer: {answer}"
        
        try:
            # 해설을 한국어와 영문으로 분리
            korean_explanation = ""
            english_explanation = ""
            
            if explanation:
                # [한국어 해설]과 [English Explanation] 부분 분리
                if "[한국어 해설]" in explanation and "[English Explanation]" in explanation:
                    parts = explanation.split("[English Explanation]")
                    korean_explanation = parts[0].replace("[한국어 해설]", "").strip()
                    english_explanation = parts[1].strip()
                else:
                    # 분리할 수 없으면 전체를 한국어로
                    korean_explanation = explanation
                    english_explanation = f"Answer: {answer}"
            
            # Supabase에 삽입할 데이터 (올바른 스키마에 맞춤)
            question_data = {
                'question_number': q_number,  # q_number -> question_number
                'type': 'cr',  # LSAT -> cr로 변경
                'question': problem['passage'],
                'choices': problem['choices'],  # (A) 뒷부분 텍스트만 저장
                'answer': answer,
                'explanation': korean_explanation,  # 한국어 해설
                'explanation_en': english_explanation  # 영문 해설
            }
            
            # Supabase에 삽입
            result = supabase.table('questions').insert(question_data).execute()
            
            if result.data:
                print(f"  ✅ q_number {q_number} 업로드 성공")
                success_count += 1
            else:
                print(f"  ❌ q_number {q_number} 업로드 실패")
                error_count += 1
                
        except Exception as e:
            print(f"  ❌ q_number {q_number} 업로드 오류: {e}")
            error_count += 1
    
    print(f"\n=== 업로드 완료 ===")
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")
    
    return success_count, error_count

def main():
    print("=" * 60)
    print("LSAT 문제 Supabase 업로드 + 해설 생성 스크립트")
    print("LSAT_03.txt 사용, type: cr")
    print("=" * 60)
    
    # 파일 경로
    lsat_file = 'questionbank/lsat/LSAT_03.txt'
    answers_file = 'questionbank/lsat/answers.txt'
    
    # 1. LSAT 파일 파싱
    print(f"1. LSAT 파일 파싱: {lsat_file}")
    problems = parse_lsat_file(lsat_file)
    
    if not problems:
        print("❌ 파싱된 문제가 없습니다.")
        return
    
    print(f"파싱된 문제 수: {len(problems)}개")
    
    # 2. 답안 파일 읽기
    print(f"\n2. 답안 파일 읽기: {answers_file}")
    answers_dict = get_answers_from_file(answers_file)
    print(f"답안 수: {len(answers_dict)}개")
    
    # 3. Supabase 업로드 + 해설 생성
    print(f"\n3. Supabase 업로드 + 해설 생성")
    success_count, error_count = upload_to_supabase_with_explanations(problems, answers_dict, start_q_number=1000)
    
    if success_count == 0:
        print("❌ 업로드에 실패했습니다.")
        return
    
    print(f"\n✅ LSAT 문제 업로드 + 해설 생성 완료!")
    print(f"   q_number 범위: 1000 ~ {1000 + len(problems) - 1}")
    print(f"   총 문제 수: {len(problems)}개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {error_count}개")
    print(f"\n   Supabase에서 확인해보세요!")

if __name__ == "__main__":
    main() 