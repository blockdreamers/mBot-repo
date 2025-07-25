import re
import os
from datetime import datetime

def format_questions(file_path):
    """문제를 깔끔하게 포맷팅합니다 (v3.0 - 본문 유실 버그 수정)"""
    
    print(f"=== {file_path} 문제 포맷팅 시작 ===")
    
    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False
    
    print(f"원본 파일 크기: {len(content)}자")
    
    # 헤더와 별표 구분선 제거
    content = re.sub(r'★+', '', content)
    content = re.sub(r'Questions \d+ to \d+ — Difficulty: \w+', '', content)
    
    # 줄 단위로 분리해서 처리
    lines = content.split('\n')
    
    # 문제 번호로 시작하는 줄 찾기 (141부터)
    question_starts = []
    for i, line in enumerate(lines):
        line = line.strip()
        # 141번부터 289번까지의 문제 번호 패턴
        if re.match(r'^(14[1-9]|1[5-9]\d|2[0-8]\d)\.', line):
            question_num = int(re.match(r'^(\d+)\.', line).group(1))
            if 141 <= question_num <= 289:
                question_starts.append((i, question_num))
                print(f"문제 {question_num} 발견: 라인 {i+1}")
    
    print(f"총 {len(question_starts)}개 문제 발견")
    
    formatted_questions = []
    
    # 각 문제를 개별적으로 처리
    for idx, (start_line, question_num) in enumerate(question_starts):
        # 다음 문제의 시작점 찾기
        if idx < len(question_starts) - 1:
            end_line = question_starts[idx + 1][0]
        else:
            end_line = len(lines)
        
        # 현재 문제의 내용 추출
        question_lines = lines[start_line:end_line]
        
        # 문제 포맷팅
        formatted_question = format_single_question(question_num, question_lines)
        if formatted_question:
            formatted_questions.append(formatted_question)
            
        # 처음 3개와 마지막 3개 미리보기
        if idx < 3 or idx >= len(question_starts) - 3:
            print(f"\n--- 문제 {question_num} 미리보기 ---")
            preview = formatted_question[:400] + "..." if len(formatted_question) > 400 else formatted_question
            print(preview)
            print("-" * 50)
    
    # 포맷팅된 내용 합치기
    formatted_content = '\n\n'.join(formatted_questions)
    
    # 백업 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    
    try:
        # 원본 백업
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"백업 생성: {backup_path}")
        
        # 포맷팅된 내용 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print(f"\n✅ 포맷팅 완료!")
        print(f"  처리된 문제 수: {len(formatted_questions)}개")
        print(f"  파일 크기: {len(original_content)}자 → {len(formatted_content)}자")
        
        return True
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False

def format_single_question(question_num, lines):
    """개별 문제를 포맷팅합니다 (v3.0 - 본문 유실 방지)"""
    
    # 빈 줄 제거하고 정리
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    if not cleaned_lines:
        return None
    
    # 첫 번째 줄에서 문제 번호 제거
    first_line = cleaned_lines[0]
    first_line = re.sub(r'^\d+\.\s*', '', first_line)
    cleaned_lines[0] = first_line
    
    # A~E 보기 찾기 (줄 단위로 정확히)
    choice_starts = {}  # {letter: line_index}
    for i, line in enumerate(cleaned_lines):
        # 정확히 "A. ", "B. ", "C. ", "D. ", "E. "로 시작하는 줄 찾기
        match = re.match(r'^([A-E])\.\s+', line)
        if match:
            letter = match.group(1)
            choice_starts[letter] = i
    
    print(f"  문제 {question_num}: 발견된 보기 위치 {choice_starts}")
    
    # 전체 텍스트 연결 (개선된 방법)
    full_text = ' '.join(cleaned_lines)
    
    # 보기 부분과 본문 분리
    if choice_starts:
        # 첫 번째 보기 시작점 찾기
        first_choice_line = min(choice_starts.values())
        
        # 본문 부분 (첫 번째 보기 이전까지의 줄들)
        main_content_lines = cleaned_lines[:first_choice_line]
        main_content = ' '.join(main_content_lines)
        
        print(f"  문제 {question_num}: 본문 길이 {len(main_content)}자")
        print(f"  문제 {question_num}: 본문 시작 '{main_content[:100]}...'")
        
        # 보기 추출 (개선된 방법)
        choices = {}
        choice_letters = sorted(choice_starts.keys())
        
        for i, letter in enumerate(choice_letters):
            start_line = choice_starts[letter]
            
            # 다음 보기의 시작점 찾기
            if i < len(choice_letters) - 1:
                next_letter = choice_letters[i + 1]
                end_line = choice_starts[next_letter]
            else:
                end_line = len(cleaned_lines)
            
            # 해당 보기의 모든 줄 합치기
            choice_lines = []
            for line_idx in range(start_line, end_line):
                line = cleaned_lines[line_idx]
                if line_idx == start_line:
                    # 첫 줄에서 "A. " 부분 제거
                    line = re.sub(r'^[A-E]\.\s+', '', line)
                choice_lines.append(line)
            
            choices[letter] = ' '.join(choice_lines).strip()
        
        print(f"  문제 {question_num}: 추출된 보기 {list(choices.keys())}")
        
    else:
        # 보기가 없는 경우 (전체가 본문)
        main_content = full_text
        choices = {}
        print(f"  문제 {question_num}: 보기 없음, 전체를 본문으로 처리")
    
    # 질문 부분 식별 (본문 내에서)
    question_patterns = [
        r'Which of the following[^?]*\?',
        r'What is the assumption[^?]*\?', 
        r'What can be concluded[^?]*\?',
        r'What strengthens[^?]*\?',
        r'What weakens[^?]*\?',
        r'What explains[^?]*\?',
        r'What supports[^?]*\?',
        r'What undermines[^?]*\?',
        r'The argument assumes[^?]*\?',
        r'The argument depends[^?]*\?',
        r'most logically completes[^?]*\?',
        r'provides the most logical completion[^?]*\?'
    ]
    
    question_part = ""
    story_part = main_content
    
    for pattern in question_patterns:
        match = re.search(pattern, main_content, re.IGNORECASE)
        if match:
            question_part = match.group(0)
            story_part = main_content[:match.start()].strip()
            print(f"  문제 {question_num}: 질문 부분 발견 - '{question_part[:50]}...'")
            print(f"  문제 {question_num}: 스토리 부분 길이 {len(story_part)}자")
            break
    
    # 만약 질문 부분이 없다면 전체를 스토리로 처리
    if not question_part:
        print(f"  문제 {question_num}: 질문 패턴 미발견, 전체를 스토리로 처리")
    
    # 포맷팅된 문제 구성
    formatted = f"{question_num}. {story_part}"
    
    # 질문 부분이 있으면 추가
    if question_part:
        formatted += f"\n\n{question_part}"
    
    # 보기 추가 (A, B, C, D, E 순서로)
    if len(choices) >= 5:  # A~E가 모두 있는 경우
        formatted += "\n"
        for letter in ['A', 'B', 'C', 'D', 'E']:
            if letter in choices:
                choice_text = choices[letter]
                # 문장 끝 정리
                if choice_text and not choice_text.endswith('.') and not choice_text.endswith('?'):
                    choice_text += "."
                formatted += f"\n{letter}. {choice_text}"
        print(f"  ✅ 문제 {question_num}: 보기 5개 모두 처리됨")
    elif choices:  # 일부 보기만 있는 경우
        print(f"  ⚠️ 문제 {question_num}: 보기 부족 ({len(choices)}개만 발견) - {list(choices.keys())}")
        formatted += "\n"
        for letter in ['A', 'B', 'C', 'D', 'E']:
            if letter in choices:
                choice_text = choices[letter]
                if choice_text and not choice_text.endswith('.') and not choice_text.endswith('?'):
                    choice_text += "."
                formatted += f"\n{letter}. {choice_text}"
    else:
        print(f"  ⚠️ 문제 {question_num}: 보기가 발견되지 않음")
    
    return formatted

def main():
    print("=" * 60)
    print("CR 문제 포맷팅 스크립트 v3.0 (본문 유실 버그 수정)")
    print("=" * 60)
    
    file_path = 'questionbank/cr/CR문제.txt'
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    if format_questions(file_path):
        print("✅ 문제 포맷팅이 완료되었습니다!")
        
        # 검증: 몇 개 문제 샘플링해서 확인
        print("\n🔍 결과 검증 중...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 각 문제가 올바르게 포맷팅되었는지 확인
        problem_count = len(re.findall(r'^\d{3}\.', content, re.MULTILINE))
        print(f"최종 문제 수: {problem_count}개")
        
        # 본문이 비어있는 문제가 있는지 확인
        empty_problems = re.findall(r'^(\d{3})\.\s*\n\nWhich', content, re.MULTILINE)
        if empty_problems:
            print(f"⚠️ 본문이 비어있는 문제들: {[p for p in empty_problems]}")
        else:
            print("✅ 모든 문제에 본문이 있습니다!")
            
    else:
        print("❌ 문제 포맷팅에 실패했습니다.")

if __name__ == "__main__":
    main() 