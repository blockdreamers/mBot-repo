import os
import time
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# ✅ 환경변수 로딩
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")

# ✅ 클라이언트 설정
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)


def generate_explanation_ko(question, choices, answer_index, retries=3):
    prompt = f"""
다음은 GMAT CR 유형의 문제입니다.

[문제]
{question}

[보기]
(A) {choices[0]}
(B) {choices[1]}
(C) {choices[2]}
(D) {choices[3]}
(E) {choices[4]}

정답은 ({chr(64 + answer_index)})입니다.

이 문제에 대한 해설을 작성해 주세요.
- 각 보기를 논리적으로 간단히 분석해 주세요.
- 정답이 왜 타당한지, 오답이 왜 틀렸는지 설명해 주세요.
- 최대 5줄 이내로 핵심만 요약해 주세요.
- 튜터가 학생에게 설명하듯이 쓰되, 어려운 용어는 피하고 논리 흐름 중심으로 해설해 주세요.
"""

    for attempt in range(1, retries + 1):
        try:
            response = openai.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 GMAT CR 전문가 튜터입니다."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Retry {attempt}/{retries} failed: {e}")
            time.sleep(2)

    raise Exception(f"❌ Failed after {retries} retries.")


def update_missing_or_placeholder_explanations_ko():
    print("🔍 Supabase에서 questions 테이블 가져오는 중...")
    rows = supabase.table("questions").select("*").execute().data
    total = len(rows)
    success, skipped, failed = 0, 0, []

    for idx, row in enumerate(rows, start=1):
        qid = row["id"]
        question = row.get("question", "")
        choices = row.get("choices", [])
        answer = row.get("answer", None)
        explanation = row.get("explanation", "")

        print(f"\n📄 [{idx}/{total}] 처리 중: {qid[:8]}")

        needs_update = (
            not explanation
            or "추론 흐름을 가장 강하게" in explanation
            or "보기입니다" in explanation
        )

        if not needs_update:
            print("⏭️ 적절한 해설이 이미 존재함. 건너뜀.")
            skipped += 1
            continue

        if not question or not choices or len(choices) != 5 or not answer:
            print("⚠️ 데이터 불완전. 건너뜀.")
            skipped += 1
            continue

        try:
            explanation_ko = generate_explanation_ko(question, choices, answer)
            supabase.table("questions").update({"explanation": explanation_ko}).eq("id", qid).execute()
            print("✅ 해설 업데이트 완료.")
            success += 1
            time.sleep(1.2)
        except Exception as e:
            print(f"❌ 실패: {qid[:8]} → {e}")
            failed.append(qid)

    print("\n✅ 전체 처리 완료")
    print(f"총 {total}개 중 성공 {success}, 건너뜀 {skipped}, 실패 {len(failed)}")

    if failed:
        print("\n❗ 실패한 항목 목록:")
        for fid in failed:
            print(f"  - {fid}")


if __name__ == "__main__":
    update_missing_or_placeholder_explanations_ko()
