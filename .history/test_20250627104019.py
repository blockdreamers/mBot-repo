import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

user_id = "debug_test_user"
question_id = "uuid-여기에-questions테이블의-실제-id값을-넣어줘"  # 꼭 진짜 UUID 넣어야 해!
now = datetime.utcnow().isoformat()

print("📡 Attempting insert...")

try:
    result = supabase.table("user_answers").insert({
        "user_id": user_id,
        "question_id": question_id,
        "user_answer": 3,
        "is_correct": True,
        "started_at": now,
        "submitted_at": now,
        "answered_at": now
    }).execute()
    print("✅ Insert success!")
    print(result)
except Exception as e:
    print("❌ Insert failed:")
    print(e)
