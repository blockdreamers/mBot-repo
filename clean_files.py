import re
import os
from datetime import datetime

def clean_file_simple(file_path):
    """파일에서 불필요한 줄들을 제거하는 간단한 방법"""
    
    print(f"\n=== {file_path} 처리 시작 ===")
    
    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False
    
    original_lines = content.count('\n') + 1
    print(f"원본 파일: {original_lines}줄")
    
    # 삭제할 패턴들을 정규식으로 정의 (더 정확하게 수정)
    patterns_to_remove = [
        r'file:///C:/Users/Dell/[^\r\n]*[\r\n]+',  # 링크 줄 (개행문자 포함)
        r'^\s*\d+/\d+\s*$',  # 페이지 번호 (앞뒤 공백 허용)
        r'^\s*23/06/2024,\s*20:03\s*$',  # 날짜/시간 (공백 허용)
    ]
    
    # 각 패턴별로 삭제 전후 개수 확인
    for i, pattern in enumerate(patterns_to_remove):
        matches = re.findall(pattern, content, re.MULTILINE)
        print(f"패턴 {i+1} 발견: {len(matches)}개")
        for j, match in enumerate(matches[:3]):  # 처음 3개만 표시
            print(f"  예시 {j+1}: {repr(match[:50])}")
        if len(matches) > 3:
            print(f"  ... 총 {len(matches)}개")
    
    # 패턴 제거를 단계별로 수행 (더 확실하게)
    cleaned_content = content
    
    # 1단계: 링크 제거
    print(f"\n1단계: 링크 제거")
    before_links = len(re.findall(r'file:///C:/Users/Dell/', cleaned_content))
    cleaned_content = re.sub(r'file:///C:/Users/Dell/[^\r\n]*[\r\n]+', '', cleaned_content, flags=re.MULTILINE)
    after_links = len(re.findall(r'file:///C:/Users/Dell/', cleaned_content))
    print(f"  링크: {before_links}개 → {after_links}개")
    
    # 2단계: 페이지 번호 제거  
    print(f"2단계: 페이지 번호 제거")
    before_pages = len(re.findall(r'^\s*\d+/\d+\s*$', cleaned_content, re.MULTILINE))
    cleaned_content = re.sub(r'^\s*\d+/\d+\s*$[\r\n]*', '', cleaned_content, flags=re.MULTILINE)
    after_pages = len(re.findall(r'^\s*\d+/\d+\s*$', cleaned_content, re.MULTILINE))
    print(f"  페이지: {before_pages}개 → {after_pages}개")
    
    # 3단계: 날짜 제거
    print(f"3단계: 날짜 제거")
    before_dates = len(re.findall(r'23/06/2024,\s*20:03', cleaned_content))
    cleaned_content = re.sub(r'^\s*23/06/2024,\s*20:03\s*$[\r\n]*', '', cleaned_content, flags=re.MULTILINE)
    after_dates = len(re.findall(r'23/06/2024,\s*20:03', cleaned_content))
    print(f"  날짜: {before_dates}개 → {after_dates}개")
    
    # 4단계: 연속된 빈 줄 정리
    print(f"4단계: 빈 줄 정리")
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)
    
    cleaned_lines = cleaned_content.count('\n') + 1
    removed_lines = original_lines - cleaned_lines
    
    print(f"정리 후: {cleaned_lines}줄 (삭제: {removed_lines}줄)")
    
    # 백업 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    
    try:
        # 원본을 백업으로 복사
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"백업 생성: {backup_path}")
        
        # 정리된 내용을 원본 파일에 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"파일 저장 완료: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False

def verify_cleaning(file_path):
    """정리가 제대로 되었는지 확인"""
    print(f"\n=== {file_path} 정리 결과 확인 ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 남아있는 패턴 확인
        remaining_links = len(re.findall(r'file:///C:/Users/Dell/', content))
        remaining_pages = len(re.findall(r'^\s*\d+/\d+\s*$', content, re.MULTILINE))
        remaining_dates = len(re.findall(r'23/06/2024,\s*20:03', content))
        
        total_remaining = remaining_links + remaining_pages + remaining_dates
        
        if total_remaining == 0:
            print("✅ 모든 불필요한 패턴이 제거되었습니다!")
        else:
            print(f"⚠️ 아직 남은 패턴: 링크 {remaining_links}개, 페이지 {remaining_pages}개, 날짜 {remaining_dates}개")
            
            # 남은 패턴의 위치 표시 (처음 5개만)
            lines = content.split('\n')
            count = 0
            for i, line in enumerate(lines):
                if count >= 5:
                    break
                if ('file:///C:/Users/Dell/' in line or 
                    re.match(r'^\s*\d+/\d+\s*$', line) or 
                    '23/06/2024, 20:03' in line):
                    print(f"  라인 {i+1}: {repr(line[:50])}")
                    count += 1
        
        return total_remaining == 0
        
    except Exception as e:
        print(f"확인 중 오류: {e}")
        return False

def main():
    print("=" * 60)
    print("파일 정리 스크립트 v2.1 (개선된 버전)")
    print("=" * 60)
    
    files_to_clean = [
        'questionbank/cr/CR문제.txt',
        'questionbank/cr/CR 정답.txt',
        'questionbank/cr/CR 답 풀이.txt'
    ]
    
    success_count = 0
    
    for file_path in files_to_clean:
        if not os.path.exists(file_path):
            print(f"\n❌ 파일 없음: {file_path}")
            continue
        
        # 파일 정리
        if clean_file_simple(file_path):
            # 정리 결과 확인
            if verify_cleaning(file_path):
                success_count += 1
                print(f"✅ {file_path} 정리 완료!")
            else:
                print(f"⚠️ {file_path} 일부 패턴이 남아있음")
        else:
            print(f"❌ {file_path} 정리 실패")
    
    print(f"\n" + "=" * 60)
    print(f"전체 결과: {success_count}/{len(files_to_clean)} 파일 성공적으로 정리됨")
    print("=" * 60)

if __name__ == "__main__":
    main() 