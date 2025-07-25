import re
import os
from datetime import datetime

def format_questions(file_path):
    """문제를 깔끔하게 포맷팅합니다 (v5.0 - 단순하고 안전한 방식)"""
    
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
        formatted_question = format_single_question_simple(question_num, question_lines)
        if formatted_question:
            formatted_questions.append(formatted_question)
            
        # 문제가 있던 문제들 특별 확인
        if question_num in [145, 146, 157, 171, 173, 174, 177, 188, 201, 210, 213, 225, 261, 288]:
            print(f"\n--- 문제 {question_num} (이전 문제) 미리보기 ---")
            preview = formatted_question[:600] + "..." if len(formatted_question) > 600 else formatted_question
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

def find_complete_choices_start(lines):
    """A, B, C, D, E가 연속으로 나오는 시작점을 찾습니다"""
    
    for i in range(len(lines) - 4):  # 최소 5줄은 있어야 A~E 체크 가능
        # A로 시작하는 줄 찾기
        if re.match(r'^A\.\s+', lines[i].strip()):
            # A 다음에 B, C, D, E가 순서대로 나오는지 확인
            found_sequence = ['A']
            current_line = i
            
            for next_letter in ['B', 'C', 'D', 'E']:
                # 다음 몇 줄에서 해당 글자 찾기 (최대 3줄 간격)
                found = False
                for j in range(current_line + 1, min(current_line + 4, len(lines))):
                    if re.match(rf'^{next_letter}\.\s+', lines[j].strip()):
                        found_sequence.append(next_letter)
                        current_line = j
                        found = True
                        break
                
                if not found:
                    break
            
            # A, B, C, D, E가 모두 발견되었으면 이 지점이 보기 시작
            if len(found_sequence) == 5 and found_sequence == ['A', 'B', 'C', 'D', 'E']:
                return i
    
    return None  # 완전한 A~E 보기를 찾지 못함

def format_single_question_simple(question_num, lines):
    """개별 문제를 포맷팅합니다 (v5.0 - 단순한 방식)"""
    
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
    
    print(f"  문제 {question_num}: 총 {len(cleaned_lines)}줄 처리")
    
    # A, B, C, D, E가 연속으로 나오는 지점 찾기
    choices_start = find_complete_choices_start(cleaned_lines)
    
    if choices_start is not None:
        print(f"  문제 {question_num}: 완전한 A~E 보기를 {choices_start}줄에서 발견")
        
        # 보기 이전까지가 모두 지문
        story_lines = cleaned_lines[:choices_start]
        story_text = ' '.join(story_lines).strip()
        
        print(f"  문제 {question_num}: 지문 길이 {len(story_text)}자")
        print(f"  문제 {question_num}: 지문 시작 '{story_text[:150]}...'")
        
        # 보기 추출
        choices = {}
        choice_lines = cleaned_lines[choices_start:]
        
        current_letter = None
        current_text = ""
        
        for line in choice_lines:
            # A., B., C., D., E.로 시작하는 줄인지 확인
            choice_match = re.match(r'^([A-E])\.\s+(.+)', line)
            if choice_match:
                # 이전 보기 저장
                if current_letter:
                    choices[current_letter] = current_text.strip()
                
                # 새 보기 시작
                current_letter = choice_match.group(1)
                current_text = choice_match.group(2)
            else:
                # 현재 보기의 계속
                if current_letter:
                    current_text += " " + line
        
        # 마지막 보기 저장
        if current_letter:
            choices[current_letter] = current_text.strip()
        
        print(f"  문제 {question_num}: 추출된 보기 {list(choices.keys())}")
        
    else:
        print(f"  문제 {question_num}: 완전한 A~E 보기 패턴을 찾지 못함, 전체를 지문으로 처리")
        story_text = ' '.join(cleaned_lines).strip()
        choices = {}
    
    # 포맷팅된 문제 구성
    formatted = f"{question_num}. {story_text}"
    
    # 보기 추가
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
    print("CR 문제 포맷팅 스크립트 v5.0 (단순하고 안전한 방식)")
    print("=" * 60)
    
    file_path = 'questionbank/cr/CR문제.txt'
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    if format_questions(file_path):
        print("✅ 문제 포맷팅이 완료되었습니다!")
        
        # 검증
        print("\n🔍 결과 검증 중...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 각 문제가 올바르게 포맷팅되었는지 확인
        problem_count = len(re.findall(r'^\d{3}\.', content, re.MULTILINE))
        print(f"최종 문제 수: {problem_count}개")
        
        # 본문이 비어있는 문제가 있는지 확인
        empty_problems = []
        for problem_num in range(141, 290):
            pattern = rf'^{problem_num}\.\s*\n\n[A-E]\.'
            if re.search(pattern, content, re.MULTILINE):
                empty_problems.append(str(problem_num))
        
        if empty_problems:
            print(f"⚠️ 본문이 비어있는 문제들: {empty_problems}")
        else:
            print("✅ 모든 문제에 본문이 있습니다!")
            
        # 이전 문제들 특별 확인
        problem_keywords = {
            157: "European wild deer",
            288: "Vebrol Corporation",
            145: "safety levers",
            173: "Thymosin beta-4"
        }
        
        for problem_num, keyword in problem_keywords.items():
            match = re.search(rf'^{problem_num}\. (.+?)(?={problem_num + 1}\.|$)', content, re.MULTILINE | re.DOTALL)
            if match:
                problem_text = match.group(1)[:300]
                if keyword in problem_text:
                    print(f"✅ {problem_num}번 문제 본문이 올바르게 복원되었습니다!")
                else:
                    print(f"❌ {problem_num}번 문제 본문이 여전히 누락되었습니다.")
        
    else:
        print("❌ 문제 포맷팅에 실패했습니다.")

if __name__ == "__main__":
    main() 