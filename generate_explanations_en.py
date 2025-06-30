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


def generate_explanation_en(question, choices, answer_index, retries=3):
    prompt = f"""
You are a professional GMAT Critical Reasoning tutor.

Your task is to write a concise yet clear explanation for the following CR question.
You must explain:
1. Why the correct answer is logically valid.
2. Why each incorrect answer is a trap or logically flawed.
3. Use logical reasoning and critical thinking vocabulary (e.g., assumption, causal flaw, irrelevant, correlation ≠ causation, etc.)
4. Limit your explanation to a maximum of 5 sentences.

Do not rewrite the question or choices. Just write the explanation as if you are teaching a student.

The question is:
{question}

Choices:
(A) {choices[0]}
(B) {choices[1]}
(C) {choices[2]}
(D) {choices[3]}
(E) {choices[4]}

The correct answer is ({chr(64 + answer_index)}).
"""
    for attempt in range(1, retries + 1):
        try:
            response = openai.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional GMAT tutor."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Retry {attempt}/{retries} failed: {e}")
            time.sleep(2)

    raise Exception(f"❌ Failed after {retries} retries.")


def update_missing_explanations_en():
    print("🔍 Fetching questions from Supabase...")
    rows = supabase.table("questions").select("*").execute().data
    total = len(rows)
    success = 0
    skipped = 0
    failed = []

    for idx, row in enumerate(rows, start=1):
        qid = row["id"]
        question = row.get("question", "")
        choices = row.get("choices", [])
        answer = row.get("answer", None)
        explanation_en = row.get("explanation_en", None)

        print(f"\n📄 [{idx}/{total}] Processing row {qid[:8]}...")

        if explanation_en:
            print("⏭️ Already has explanation_en. Skipping.")
            skipped += 1
            continue

        if not question or not choices or len(choices) != 5 or not answer:
            print("⚠️ Incomplete data. Skipping.")
            skipped += 1
            continue

        try:
            explanation = generate_explanation_en(question, choices, answer)
            supabase.table("questions").update({"explanation_en": explanation}).eq("id", qid).execute()
            print("✅ Explanation saved.")
            success += 1
            time.sleep(1.2)
        except Exception as e:
            print(f"❌ Failed to generate explanation for row {qid[:8]}: {e}")
            failed.append(qid)

    print("\n✅ Processing complete.")
    print(f"Total: {total}, Success: {success}, Skipped: {skipped}, Failed: {len(failed)}")

    if failed:
        print("\n❗ Failed rows:")
        for fid in failed:
            print(f"  - {fid}")


if __name__ == "__main__":
    update_missing_explanations_en()
