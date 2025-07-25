import re
import os
from datetime import datetime

def load_answers(answer_file):
    """정답 파일에서 정답들을 로드합니다"""
    answers = {}
    
    try:
        with open(answer_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 문제번호. 정답 패턴 찾기
        pattern = r'(\d+)\.\s*([A-E])'
        matches = re.findall(pattern, content)
        
        for question_num, answer in matches:
            answers[int(question_num)] = answer
        
        print(f"정답 로드 완료: {len(answers)}개")
        print(f"정답 범위: {min(answers.keys())}번 ~ {max(answers.keys())}번")
        
        return answers
        
    except Exception as e:
        print(f"정답 파일 읽기 오류: {e}")
        return {}

def add_answers_to_questions(questions_file, answers):
    """문제 파일에 정답을 추가합니다"""
    
    print(f"\n=== {questions_file} 정답 추가 시작 ===")
    
    # 파일 읽기
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"문제 파일 읽기 오류: {e}")
        return False
    
    print(f"원본 파일 크기: {len(content)}자")
    
    lines = content.split('\n')
    new_lines = []
    
    current_question = None
    need_to_add_answer = False  # E 보기 다음에 정답을 추가해야 하는지 표시
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 정답을 추가해야 하는 상황인지 먼저 확인
        if need_to_add_answer and current_question and current_question in answers:
            # 현재 줄이 다음 문제 시작인지 확인
            if not re.match(r'^\d+\.', line.strip()):
                # 다음 문제가 아니면 정답 추가
                answer = answers[current_question]
                answer_line = f"{current_question}. 정답 : {answer}"
                new_lines.append(answer_line)
                new_lines.append("")  # 빈 줄 추가
                print(f"  → 정답 추가: {answer_line}")
                need_to_add_answer = False
        
        new_lines.append(line)
        
        # 문제 번호 찾기
        question_match = re.match(r'^(\d+)\.', line.strip())
        if question_match:
            question_num = int(question_match.group(1))
            if 141 <= question_num <= 289:
                current_question = question_num
                need_to_add_answer = False
                print(f"문제 {current_question} 처리 중...")
        
        # E. 보기 찾기 (마지막 보기)
        choice_match = re.match(r'^E\.', line.strip())
        if choice_match and current_question:
            need_to_add_answer = True
            print(f"  문제 {current_question}의 E 보기 발견")
        
        i += 1
    
    # 마지막 문제 처리 (파일 끝에서 정답 추가가 필요한 경우)
    if need_to_add_answer and current_question and current_question in answers:
        answer = answers[current_question]
        answer_line = f"{current_question}. 정답 : {answer}"
        new_lines.append(answer_line)
        print(f"  → 마지막 문제 정답 추가: {answer_line}")
    
    # 결과 저장
    new_content = '\n'.join(new_lines)
    
    # 백업 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{questions_file}.backup_{timestamp}"
    
    try:
        # 원본 백업
        with open(questions_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"백업 생성: {backup_path}")
        
        # 정답이 추가된 내용 저장
        with open(questions_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"\n✅ 정답 추가 완료!")
        print(f"  파일 크기: {len(original_content)}자 → {len(new_content)}자")
        
        return True
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False

def main():
    print("=" * 60)
    print("CR 문제에 정답 추가 스크립트")
    print("=" * 60)
    
    answer_file = 'questionbank/cr/CR 정답.txt'
    questions_file = 'questionbank/cr/CR문제.txt'
    
    # 파일 존재 확인
    if not os.path.exists(answer_file):
        print(f"❌ 정답 파일을 찾을 수 없습니다: {answer_file}")
        return
    
    if not os.path.exists(questions_file):
        print(f"❌ 문제 파일을 찾을 수 없습니다: {questions_file}")
        return
    
    # 정답 로드
    answers = load_answers(answer_file)
    if not answers:
        print("❌ 정답을 로드할 수 없습니다.")
        return
    
    # 문제에 정답 추가
    if add_answers_to_questions(questions_file, answers):
        print("✅ 모든 작업이 완료되었습니다!")
        
        # 샘플 확인
        print("\n📋 결과 샘플:")
        with open(questions_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        sample_count = 0
        for i, line in enumerate(lines):
            if "정답 :" in line:
                print(f"  {line.strip()}")
                sample_count += 1
                if sample_count >= 5:  # 처음 5개만 표시
                    break
        
        print(f"\n총 {sample_count}개의 정답이 추가되었습니다.")
    else:
        print("❌ 정답 추가에 실패했습니다.")

if __name__ == "__main__":
    main() 