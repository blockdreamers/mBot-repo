# db.py
import os
from supabase import create_client
from dotenv import load_dotenv
import random

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_random_cr_question():
    res = supabase.table("questions").select("*").eq("type", "CR").execute()
    data = res.data
    if not data:
        return None

    q = random.choice(data)
    return {
        "id": q["id"],
        "question": q["question"],
        "choices": q["choices"],
        "answer": q["answer"],
        "explanation": q["explanation"],
    }
