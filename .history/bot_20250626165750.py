import os
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from supabase import create_client, Client

# 🔐 환경변수 로드
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🔗 Supabase 연결
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🟢 /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("안녕하세요! /q 를 입력하면 GMAT CR 문제를 드립니다.")

# ❓ /q 명령어
def send_question(update: Update, context: CallbackContext) -> None:
    try:
        response = supabase.table("questions").select("*").eq("type", "CR").execute()
        questions = response.data
    except Exception as e:
        update.message.reply_text(f"문제 불러오기 오류:\n{str(e)}")
        return

    if not questions:
        update.message.reply_text("문제가 없습니다.")
        return

    question = random.choice(questions)
    context.user_data["current_question"] = question
    context.user_data["start_time"] = datetime.utcnow()

    # 🔤 질문 텍스트 구성
    text = f"*문제:*\n{question['question'].replace('\\n', '').strip()}\n\n"
    for i, choice in enumerate(question["choices"]):
        text += f"{chr(65+i)}. {choice}\n"

    # ⌨️ 버튼 생성
    keyboard = [[InlineKeyboardButton(f"{chr(65+i)}", callback_data=f"answer_{i+1}")]
                for i in range(5)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ✅ 정답 버튼 처리
def handle_answer(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user = query.from_user
    user_id = user.id
    username = user.username or user.full_name or "Unknown"
    selected = int(query.data.split("_")[1])
    timestamp = datetime.utcnow()

    question = context.user_data.get("current_question")
    start_time = context.user_data.get("start_time")

    if not question or not start_time:
        query.edit_message_text("먼저 /q 명령어로 문제를 받아주세요.")
        return

    correct = int(question["answer"])
    explanation = question.get("explanation", "설명 없음")
    letter = chr(64 + selected)

    is_correct = selected == correct
    elapsed_sec = int((timestamp - start_time).total_seconds())

    # 🧾 응답 메시지
    result = "✅ 정답입니다!" if is_correct else f"❌ 오답입니다! (정답: {chr(64 + correct)})"
    reply_text = f"{result}\n\n*해설:* {explanation}"

    query.edit_message_text(reply_text, parse_mode='Markdown')

    # 💾 DB 기록
    try:
        supabase.table("answers").insert({
            "user_id": str(user_id),
            "username": username,
            "question_id": question["id"],
            "selected": selected,
            "is_correct": is_correct,
            "elapsed_sec": elapsed_sec,
            "timestamp": timestamp.isoformat(),
        }).execute()
        print(f"✅ 기록 완료: {username} - 선택 {letter} - {'정답' if is_correct else '오답'}")
    except Exception as e:
        print(f"❌ DB 저장 실패: {e}")

# ▶️ 메인 함수
def main():
    print(f"📦 TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
    print(f"📦 SUPABASE_URL = {SUPABASE_URL}")
    print(f"📦 SUPABASE_KEY = {SUPABASE_KEY}")
    print("🤖 봇이 실행 중입니다...")

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^answer_\d+$"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
