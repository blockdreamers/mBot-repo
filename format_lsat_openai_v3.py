import os
import openai
import re
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
    exit(1)

def format_lsat_with_openai(input_file, output_file):
    """OpenAI API를 사용해서 LSAT 문제를 정리합니다 (본문 + 질문 + 보기 분리)"""
    
    print(f"=== {input_file} OpenAI로 정리 시작 (본문 + 질문 + 보기 분리) ===")
    
    # 파일 읽기
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False
    
    print(f"원본 파일 크기: {len(content)}자")
    
    # 문제별로 분리
    problems = re.split(r'(\d+\.)', content)
    
    formatted_problems = []
    
    for i in range(1, len(problems), 2):  # 문제 번호와 내용을 함께 처리
        if i + 1 < len(problems):
            problem_num = problems[i].strip()
            problem_content = problems[i + 1].strip()
            
            if problem_content:
                print(f"문제 {problem_num} 처리 중...")
                
                # OpenAI로 정리
                formatted_problem = format_single_problem_with_openai(problem_num, problem_content)
                if formatted_problem:
                    formatted_problems.append(formatted_problem)
    
    # 결과 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(formatted_problems))
        
        print(f"\n✅ 정리 완료!")
        print(f"  처리된 문제 수: {len(formatted_problems)}개")
        print(f"  저장된 파일: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False

def format_single_problem_with_openai(problem_num, problem_content):
    """OpenAI API를 사용해서 단일 문제를 정리합니다 (본문 + 질문 + 보기 분리)"""
    
    prompt = f"""다음은 LSAT 문제입니다. 본문, 질문, 보기를 정확히 분리해서 정리해주세요.

원본 문제:
{problem_num} {problem_content}

다음 형식으로 정리해주세요:

{problem_num}
[본문 내용 - 배경 정보, 상황 설명 등]

[질문 내용 - "Which one of the following..." 같은 실제 질문]

(A) [보기 A 내용]
(B) [보기 B 내용]
(C) [보기 C 내용]
(D) [보기 D 내용]
(E) [보기 E 내용]

중요한 규칙:
1. 원문을 번역하거나 수정하지 마세요
2. 영어 원문을 그대로 유지하세요
3. 본문과 질문을 분리하세요:
   - 본문: 배경 정보, 상황 설명, 논쟁 등
   - 질문: "Which one of the following..." 같은 실제 질문
4. 질문 부분이 빠지지 않도록 주의하세요
5. 각 보기는 완전한 문장으로 만들어주세요
6. 원본 단어와 문장을 그대로 보존하세요

정리된 결과:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 LSAT 문제 편집 전문가입니다. 원문을 번역하거나 수정하지 말고, 본문과 질문을 분리하여 정리하는 것이 목표입니다. 질문 부분이 빠지지 않도록 주의하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1  # 더 낮은 temperature로 일관성 확보
        )
        
        formatted_text = response.choices[0].message.content.strip()
        
        # 결과 검증
        if "(A)" in formatted_text and "(B)" in formatted_text and "(C)" in formatted_text:
            print(f"  ✅ 문제 {problem_num} 정리 완료")
            return formatted_text
        else:
            print(f"  ⚠️ 문제 {problem_num} 정리 실패 - 보기 형식 오류")
            return None
            
    except Exception as e:
        print(f"  ❌ 문제 {problem_num} OpenAI API 오류: {e}")
        return None

def main():
    print("=" * 60)
    print("LSAT 문제 OpenAI 정리 스크립트 v3")
    print("본문 + 질문 + 보기 정확한 분리")
    print("=" * 60)
    
    input_file = 'questionbank/lsat/LSAT.txt'
    output_file = 'questionbank/lsat/LSAT_03.txt'
    
    if not os.path.exists(input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return
    
    if format_lsat_with_openai(input_file, output_file):
        print("✅ LSAT 문제 정리가 완료되었습니다!")
        
        # 결과 확인
        print("\n📋 결과 확인...")
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 문제 수 확인
        problem_count = len(re.findall(r'^\d+\.', content, re.MULTILINE))
        print(f"최종 문제 수: {problem_count}개")
        
        # 보기 수 확인
        choice_count = len(re.findall(r'\([A-E]\)', content))
        print(f"총 보기 수: {choice_count}개")
        
        if choice_count >= problem_count * 5:
            print("✅ 보기들이 올바르게 정리되었습니다!")
        else:
            print(f"⚠️ 일부 보기가 누락되었을 수 있습니다. (예상: {problem_count * 5}개)")
            
    else:
        print("❌ LSAT 문제 정리에 실패했습니다.")

if __name__ == "__main__":
    main() 