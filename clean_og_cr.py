import re
import os

def clean_og_cr_file():
    input_file = "questionbank/OG_CR_2025/OG_CR_only.txt"
    output_file = "questionbank/OG_CR_2025/OG_CR_clean.txt"

    # 제거할 패턴들
    patterns_to_remove = [
        r'file:///C:/Users/Dell/Documents/eBook%20Converter/VitalSource%20Downloader/temp/9781394260058/epub/OPS/c08\.html',
        r'\b\d+/\d+\b',  # 페이지 번호 패턴 (예: 207/481)
        r'\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}',  # 날짜/시간 패턴 (예: 23/06/2024, 22:25)
        r'/\d{4}, \d{1,2}:\d{2}',  # 날짜/시간 패턴 (예: /2024, 22:25)
        r'^\s*$',  # 빈 줄
    ]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        original_line_count = len(content.split('\n'))
        print(f"원본 파일 라인 수: {original_line_count}")

        # 각 패턴 제거
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)

        # 여러 개의 빈 줄을 하나의 빈 줄로 통합
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # 앞뒤 공백 제거
        content = content.strip()

        # 새 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        cleaned_line_count = len(content.split('\n'))
        print(f"정리된 파일 라인 수: {cleaned_line_count}")
        print(f"제거된 라인 수: {original_line_count - cleaned_line_count}")
        print(f"✅ 정리 완료: {output_file}")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    clean_og_cr_file()
