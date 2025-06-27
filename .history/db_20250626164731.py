import os
import random
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔹 랜덤 문제 불러오기
def get_random_question():
    response = supabase.table("questions").select("*").execute()
    questions = response.data

    if not questions:
        return None

    question = random.choice(questions)

    return {
        "id": question["id"],
        "type": question["type"],
        "question": question["question"],
        "choices": question["choices"],
        "answer": question["answer"],
        "explanation": question["explanation"]
    }

# 🔹 유저 정답 저장
def save_user_answer(user_id, question_id, user_answer, is_correct, duration):
    supabase.table("user_answers").insert({
        "user_id": user_id,
        "question_id": question_id,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "duration_seconds": duration
    }).execute()
