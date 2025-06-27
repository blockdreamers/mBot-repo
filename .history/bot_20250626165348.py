import os
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from supabase import create_client, Client
from pathlib import Path

# 🔐 환경 변수 로드
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ✅ 디버깅: 환경변수 제대로 불러오는지 확인
print(f"📦 TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
print(f"📦 SUPABASE_URL = {SUPABASE_URL}")
print(f"📦 SUPABASE_KEY = {SUPABASE_KEY[:6]}...(생략)")  # 키는 앞부분만 출력

# 🔗 Supabase 연결
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🟢 /start 명령어
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("안녕하세요! /q 를 입력하면 GMAT CR 문제를 드립니다.")

# ❓ /q 명령어 - 문제 전송
def send_question(update: Update, context: CallbackContext) -> None:
    try:
        response = supabase.table("questions").select("*").eq("type", "CR").execute()
        questions = response.data
    except Exception as e:
        update.message.reply_text(f"문제를 불러오는 중 오류가 발생했습니다.\n{str(e)}")
        return

    if not questions:
        update.message.reply_text("문제가 없습니다.")
        return

    question = random.choice(questions)
    context.user_data["current_question"] = question

    text = f"*문제:*\n{question['question']}\n\n"
    for i, choice in enumerate(question["choices"]):
        text += f"{chr(65+i)}. {choice}\n"

    text += "\n답을 원하시면 /a 를 입력하세요."
    update.message.reply_text(text, parse_mode='Markdown')

# ✅ /a 명령어 - 정답과 해설
def send_answer(update: Update, context: CallbackContext) -> None:
    question = context.user_data.get("current_question")
    if not question:
        update.message.reply_text("먼저 /q 로 문제를 받아주세요.")
        return

    correct_letter = chr(65 + int(question["answer"]) - 1)
    explanation = question.get("explanation", "설명 없음")

    update.message.reply_text(f"정답: *{correct_letter}*\n\n해설: {explanation}", parse_mode='Markdown')

# ▶️ 메인 실행
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN is missing or invalid")

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("a", send_answer))

    updater.start_polling()
    print("🤖 봇이 실행 중입니다...")
    updater.idle()

if __name__ == "__main__":
    main()
