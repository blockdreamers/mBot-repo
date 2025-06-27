import os
import time
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from db import get_random_question, save_user_answer

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 유저별 타이머 저장
user_sessions = {}

logging.basicConfig(level=logging.INFO)

# /start 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 GMAT Quiz Bot에 오신 걸 환영합니다!\n/quiz 입력 시 문제를 풀 수 있어요.")

# /quiz 핸들러
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    question = get_random_question()

    if not question:
        await update.message.reply_text("⚠️ 문제를 불러오지 못했습니다.")
        return

    # 보기 버튼 생성
    buttons = [
        [InlineKeyboardButton(text=choice, callback_data=f"{i}")]
        for i, choice in enumerate(question["choices"], 1)
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    # 세션 저장 (문제 + 시작 시간)
    context.user_data["current_question"] = question
    user_sessions[user_id] = time.time()

    await update.message.reply_text(f"📖 {question['question']}", reply_markup=reply_markup)

# 답변 콜백 핸들러
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    selected = int(query.data)
    question = context.user_data.get("current_question")
    start_time = user_sessions.get(user_id, time.time())
    duration = time.time() - start_time

    is_correct = selected == question["answer"]

    # 결과 전송
    if is_correct:
        result = "✅ 정답입니다!"
    else:
        correct = question["choices"][question["answer"] - 1]
        result = f"❌ 오답입니다. 정답: {correct}"

    await query.edit_message_text(
        f"{result}\n🕒 소요 시간: {int(duration)}초\n\n{question.get('explanation', '')}"
    )

    # 기록 저장
    save_user_answer(
        user_id=user_id,
        question_id=question["id"],
        user_answer=selected,
        is_correct=is_correct,
        duration=duration
    )

# 메인 실행
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(handle_answer))

    print("✅ Bot is running...")
    app.run_polling()
