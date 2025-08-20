import re
import os

def format_og_cr_problems():
    input_file = "questionbank/OG_CR_2025/OG_CR_clean.txt"
    answers_file = "questionbank/OG_CR_2025/답.txt"
    output_file = "questionbank/OG_CR_2025/OG_CR_clean_answer.txt"

    # 답.txt 파일에서 답변 로드
    answers = {}
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2:
                        question_num = parts[0].strip()
                        answer = parts[1].strip()
                        answers[question_num] = answer
        print(f"✅ 답변 파일 로드 완료: {len(answers)}개 답변")
    except Exception as e:
        print(f"❌ 답변 파일 로드 오류: {str(e)}")
        return

    try:
        # 라인별로 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_question = None
        current_content = []
        questions_data = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 문제 번호 패턴 확인 (620. 621. 등)
            question_match = re.match(r'^(\d{3})\.\s*(.*)', line)
            if question_match:
                # 이전 문제 저장
                if current_question and current_content:
                    questions_data[current_question] = '\n'.join(current_content)

                # 새 문제 시작
                current_question = question_match.group(1)
                current_content = [question_match.group(2)]
            else:
                # 현재 문제에 내용 추가
                if current_question:
                    current_content.append(line)

        # 마지막 문제 저장
        if current_question and current_content:
            questions_data[current_question] = '\n'.join(current_content)

        print(f"📝 파싱된 문제 수: {len(questions_data)}개")

        # 620-801 범위만 처리하고 형식화
        formatted_content = []

        for question_num in sorted(questions_data.keys()):
            if 620 <= int(question_num) <= 801:
                content = questions_data[question_num]

                # 보기 패턴으로 분리
                parts = re.split(r'^([A-E])\.\s*', content, flags=re.MULTILINE)
                passage = parts[0].strip()

                # 문제 번호와 지문 추가
                formatted_content.append(f"{question_num}. {passage}")

                # 보기들 처리
                choices = []
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        choice_letter = parts[i]
                        choice_text = parts[i + 1].strip()
                        choices.append(f"{choice_letter}. {choice_text}")

                # 보기들 추가 (A, B, C, D, E만)
                for choice in choices[:5]:
                    formatted_content.append(choice)

                # 답변 추가
                if question_num in answers:
                    formatted_content.append(f"{question_num}정답. {answers[question_num]}")
                else:
                    formatted_content.append(f"{question_num}정답. 답변 없음")

                # 문제 사이에 빈 줄 추가
                formatted_content.append("")

        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_content))

        processed_count = len([q for q in questions_data.keys() if 620 <= int(q) <= 801])
        print(f"✅ 정리 완료: {output_file}")
        print(f"   처리된 문제 수: {processed_count}개 (620-801)")

    except Exception as e:
        print(f"❌ 파일 처리 오류: {str(e)}")

if __name__ == "__main__":
    format_og_cr_problems()
