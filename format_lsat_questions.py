import re
import os
from datetime import datetime

def format_lsat_questions(file_path):
    """LSAT 문제의 보기 문자와 텍스트를 매칭시켜 포맷팅합니다"""
    
    print(f"=== {file_path} LSAT 문제 포맷팅 시작 ===")
    
    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False
    
    print(f"원본 파일 크기: {len(content)}자")
    
    # 줄 단위로 분리
    lines = content.split('\n')
    
    # 문제 번호로 시작하는 줄 찾기
    question_starts = []
    for i, line in enumerate(lines):
        line = line.strip()
        # 숫자.으로 시작하는 줄 (문제 번호)
        if re.match(r'^\d+\.$', line):
            question_num = int(line.replace('.', ''))
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
        formatted_question = format_single_lsat_question(question_num, question_lines)
        if formatted_question:
            formatted_questions.append(formatted_question)
            
        # 처음 몇 개 문제 미리보기
        if idx < 3:
            print(f"\n--- 문제 {question_num} 미리보기 ---")
            preview = formatted_question[:500] + "..." if len(formatted_question) > 500 else formatted_question
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

def format_single_lsat_question(question_num, lines):
    """개별 LSAT 문제를 포맷팅합니다"""
    
    if not lines:
        return None
    
    # 빈 줄 제거하고 정리 (첫 줄 문제번호 제외)
    cleaned_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if i == 0:  # 첫 줄은 문제 번호이므로 건너뛰기
            continue
        if line:  # 빈 줄이 아닌 경우만 추가
            cleaned_lines.append(line)
    
    if not cleaned_lines:
        return None
    
    # (A), (B), (C), (D), (E) 패턴 찾기
    choice_pattern_indices = []
    for i, line in enumerate(cleaned_lines):
        if re.match(r'^\([A-E]\)$', line):
            choice_pattern_indices.append(i)
    
    print(f"  문제 {question_num}: 보기 패턴 발견 위치 {choice_pattern_indices}")
    
    if len(choice_pattern_indices) != 5:
        print(f"  ⚠️ 문제 {question_num}: 보기 패턴이 5개가 아닙니다 ({len(choice_pattern_indices)}개)")
        # 보기 패턴이 없으면 원본 그대로 반환
        return f"{question_num}.\n" + '\n'.join(cleaned_lines)
    
    # 보기 패턴 이전까지가 문제 본문
    first_choice_index = choice_pattern_indices[0]
    question_content = cleaned_lines[:first_choice_index]
    
    # 보기 패턴 이후의 텍스트들을 찾기
    last_choice_index = choice_pattern_indices[-1]
    choice_texts = []
    
    # 마지막 (E) 이후의 모든 텍스트를 수집
    remaining_lines = cleaned_lines[last_choice_index + 1:]
    
    # 불필요한 줄들 제거 (페이지 번호, GO ON TO THE NEXT PAGE 등)
    filtered_lines = []
    for line in remaining_lines:
        # 페이지 관련 텍스트 건너뛰기
        if re.match(r'^(GO ON TO THE NEXT PAGE|PrepTest|\d+|[A-Z]|\-\d+\-|\(Nov|\d{4}\))\.?$', line):
            continue
        if line:
            filtered_lines.append(line)
    
    # 보기 텍스트들을 순서대로 분리
    # 각 보기는 일반적으로 문단 단위로 구성됨
    choice_texts = extract_choice_texts(filtered_lines)
    
    print(f"  문제 {question_num}: {len(choice_texts)}개 보기 텍스트 추출됨")
    
    # 포맷팅된 문제 구성
    formatted = f"{question_num}.\n"
    formatted += '\n'.join(question_content)
    
    # 보기들을 (A) 텍스트 형태로 추가
    if len(choice_texts) >= 5:
        formatted += "\n"
        letters = ['A', 'B', 'C', 'D', 'E']
        for i, choice_text in enumerate(choice_texts[:5]):
            formatted += f"\n({letters[i]}) {choice_text}"
        print(f"  ✅ 문제 {question_num}: 보기 5개 모두 처리됨")
    else:
        print(f"  ⚠️ 문제 {question_num}: 보기 텍스트 부족 ({len(choice_texts)}개)")
        # 부족한 경우에도 있는 것들은 추가
        formatted += "\n"
        letters = ['A', 'B', 'C', 'D', 'E']
        for i, choice_text in enumerate(choice_texts):
            formatted += f"\n({letters[i]}) {choice_text}"
    
    return formatted

def extract_choice_texts(lines):
    """보기 텍스트들을 추출합니다"""
    
    if not lines:
        return []
    
    # 모든 텍스트를 하나로 합치기
    all_text = ' '.join(lines)
    
    # 문장 단위로 분리 (마침표, 물음표, 느낌표 기준)
    sentences = re.split(r'[.!?]\s+', all_text)
    
    # 빈 문장 제거
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 5개의 보기로 균등하게 분배
    if len(sentences) >= 5:
        # 5개 그룹으로 나누기
        group_size = len(sentences) // 5
        remainder = len(sentences) % 5
        
        choice_texts = []
        start_idx = 0
        
        for i in range(5):
            # 남은 문장이 있으면 앞쪽 그룹에 더 많이 배분
            current_group_size = group_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_group_size
            
            if start_idx < len(sentences):
                group_sentences = sentences[start_idx:end_idx]
                choice_text = '. '.join(group_sentences)
                
                # 마지막에 마침표가 없으면 추가
                if choice_text and not choice_text.endswith('.'):
                    choice_text += '.'
                
                choice_texts.append(choice_text)
                start_idx = end_idx
        
        return choice_texts
    else:
        # 문장이 5개 미만이면 각각을 하나의 보기로 처리
        choice_texts = []
        for sentence in sentences:
            if sentence and not sentence.endswith('.'):
                sentence += '.'
            choice_texts.append(sentence)
        
        # 부족한 부분은 빈 문자열로 채우기
        while len(choice_texts) < 5:
            choice_texts.append("")
        
        return choice_texts[:5]

def main():
    print("=" * 60)
    print("LSAT 문제 포맷팅 스크립트")
    print("보기 문자 (A), (B), ... 와 텍스트를 매칭")
    print("=" * 60)
    
    file_path = 'questionbank/lsat/LSAT.txt'
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    if format_lsat_questions(file_path):
        print("✅ LSAT 문제 포맷팅이 완료되었습니다!")
        
        # 검증
        print("\n🔍 결과 검증 중...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 각 문제가 올바르게 포맷팅되었는지 확인
        problem_count = len(re.findall(r'^\d+\.', content, re.MULTILINE))
        print(f"최종 문제 수: {problem_count}개")
        
        # (A) 패턴이 있는지 확인
        choice_count = len(re.findall(r'\([A-E]\)', content))
        print(f"총 보기 수: {choice_count}개")
        
        if choice_count >= problem_count * 5:
            print("✅ 보기들이 올바르게 매칭되었습니다!")
        else:
            print(f"⚠️ 일부 보기가 누락되었을 수 있습니다. (예상: {problem_count * 5}개)")
            
    else:
        print("❌ LSAT 문제 포맷팅에 실패했습니다.")

if __name__ == "__main__":
    main() 