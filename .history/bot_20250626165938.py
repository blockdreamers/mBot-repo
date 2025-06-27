import os
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from supabase import create_client, Client

# 🔐 Load env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🔗 Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🟢 /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("안녕하세요! /q 를 입력하면 GMAT CR 문제를 드립니다.")

# ❓ /q - 문제 전송
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
    context.user_data["start_time"] = datetime.now()

    # 🧹 문제 텍스트 정리
    q_text = question['question'].replace('\n', '').strip()
    text = f"*문제:*\n{q_text}\n"

    choices = question["choices"]
    for i, choice in enumerate(choices):
        text += f"{chr(65+i)}. {choice.strip()}\n"

    # 🔘 답변 버튼 구성
    keyboard = [
        [InlineKeyboardButton(f"{chr(65+i)}", callback_data=str(i+1)) for i in range(5)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# 🔘 버튼 클릭 핸들러
def handle_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    selected = int(query.data)  # 1~5
    question = context.user_data.get("current_question")
    start_time = context.user_data.get("start_time")

    if not question or not start_time:
        query.edit_message_text("먼저 /q 명령어로 문제를 받아주세요.")
        return

    correct_answer = int(question["answer"])  # 1~5
    is_correct = selected == correct_answer
    elapsed_sec = (datetime.now() - start_time).seconds

    # 🧾 Supabase 기록
    supabase.table("answers").insert({
        "is_correct": is_correct,
        "elapsed_sec": elapsed_sec,
        "timestamp": datetime.now().isoformat()
    }).execute()

    result_text = f"당신의 선택: {chr(64+selected)}\n정답 여부: {'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}"
    query.edit_message_text(result_text)

# ✅ /a - 정답 보기
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
    print(f"📦 TELEGRAM_TOKEN = {TELEGRAM_TOKEN}")
    print(f"📦 SUPABASE_URL = {SUPABASE_URL}")
    print(f"📦 SUPABASE_KEY = {SUPABASE_KEY}")
    print("🤖 봇이 실행 중입니다...")

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("a", send_answer))
    dp.add_handler(CallbackQueryHandler(handle_button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
