import re
import os
from datetime import datetime

def clean_lsat_junk_data(input_file, output_file):
    """LSAT 파일에서 잡데이터를 제거합니다"""
    
    print(f"=== {input_file} → {output_file} 잡데이터 정리 시작 ===")
    
    # 파일 읽기
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return False
    
    print(f"원본 파일 크기: {len(content)}자")
    
    # 줄 단위로 분리
    lines = content.split('\n')
    
    # 제거할 패턴들
    patterns_to_remove = [
        r'^PrepTest$',
        r'^-\d+$',  # -1989 같은 패턴
        r'^\(Nov$',
        r'^\d{4}\)$',  # 2019) 같은 패턴
        r'^GO ON TO THE NEXT PAGE\.$',
        r'^\d+ Questions$',
        r'^Directions:.*$',
        r'^A$',  # 단독 A, B, C 등
        r'^B$',
        r'^C$',
        r'^D$',
        r'^E$',
        r'^[A-Z]$',  # 단독 대문자
        r'^\d+$',  # 단독 숫자 (문제 번호 제외)
        r'^-\d+-$',  # -22- 같은 패턴
        r'^\s*$',  # 빈 줄들
    ]
    
    # 정리된 줄들
    cleaned_lines = []
    removed_count = 0
    
    for line in lines:
        line = line.strip()
        
        # 제거할 패턴인지 확인
        should_remove = False
        for pattern in patterns_to_remove:
            if re.match(pattern, line, re.IGNORECASE):
                should_remove = True
                removed_count += 1
                print(f"제거: '{line}'")
                break
        
        if not should_remove and line:
            cleaned_lines.append(line)
    
    # 정리된 내용 합치기
    cleaned_content = '\n'.join(cleaned_lines)
    
    try:
        # 정리된 내용 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"\n✅ 잡데이터 정리 완료!")
        print(f"  제거된 줄 수: {removed_count}개")
        print(f"  파일 크기: {len(content)}자 → {len(cleaned_content)}자")
        print(f"  저장된 파일: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"파일 저장 오류: {e}")
        return False

def main():
    print("=" * 60)
    print("LSAT 파일 잡데이터 정리 스크립트 (1단계)")
    print("PrepTest, 페이지 번호, 날짜 등 제거")
    print("=" * 60)
    
    input_file = 'questionbank/lsat/LSAT.txt'
    output_file = 'questionbank/lsat/LSAT_1.txt'
    
    if not os.path.exists(input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        return
    
    if clean_lsat_junk_data(input_file, output_file):
        print("✅ LSAT 파일 잡데이터 정리가 완료되었습니다!")
        
        # 결과 확인
        print("\n🔍 정리 결과 확인...")
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 문제 번호 확인
        problem_count = len(re.findall(r'^\d+\.', content, re.MULTILINE))
        print(f"문제 수: {problem_count}개")
        
        # (A) 패턴 확인
        choice_count = len(re.findall(r'\([A-E]\)', content))
        print(f"보기 패턴 수: {choice_count}개")
        
        # 처음 몇 줄 미리보기
        lines = content.split('\n')
        print(f"\n처음 10줄 미리보기:")
        for i, line in enumerate(lines[:10]):
            print(f"{i+1:2d}: {line}")
            
    else:
        print("❌ LSAT 파일 잡데이터 정리에 실패했습니다.")

if __name__ == "__main__":
    main()