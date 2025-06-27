import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from dotenv import load_dotenv
from db import (
    fetch_random_question, fetch_question_by_number, fetch_last_question_id,
    insert_user_answer, fetch_user_stats, fetch_wrong_questions
)
import time

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DEBUG_USER = os.getenv("DEBUG_USER_ID", "debug_test_user")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

user_sessions = {}  # user_id: {question_id, start_time}

# 📌 /start
def start(update: Update, context: CallbackContext):
    commands = """
안녕하세요! GMAT CR 연습 봇입니다 🤖

다음 명령어를 사용해보세요:

✅ /q → 랜덤 문제 받기
✅ /q12 → 12번 문제 받기
✅ /a → 마지막 문제 다시 보기
✅ /stats → 정답률 통계 보기
✅ /wrong → 틀린 문제 목록 보기
✅ /help → 도움말 다시 보기
"""
    keyboard = [
        [InlineKeyboardButton("📝 문제 받기", callback_data="get_question")],
        [InlineKeyboardButton("📊 통계 보기", callback_data="show_stats")],
        [InlineKeyboardButton("❌ 틀린 문제", callback_data="show_wrong")],
        [InlineKeyboardButton("❓ 도움말", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(commands.strip(), reply_markup=reply_markup)

# 📌 /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("""
📘 *도움말*

/q → 아직 안 푼 문제 랜덤 출제  
/q12 → 12번 문제 직접 출제  
/a → 마지막 문제 다시 보기  
/stats → 정답률 및 맞은 개수  
/wrong → 내가 틀린 문제 보기  
/help → 도움말 다시 보기  
""", parse_mode="Markdown")

# 📌 /q
def send_question(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    question = fetch_random_question(user_id)
    if not question:
        update.message.reply_text("🎉 모든 문제를 푸셨습니다!")
        return

    user_sessions[user_id] = {"question_id": question["id"], "start_time": time.time()}
    text = f"📘 문제 {question['number']}\n{question['question']}\n\n"
    for idx, choice in enumerate(question['choices'], start=1):
        text += f"{chr(64+idx)}. {choice}\n"
    update.message.reply_text(text)

# 📌 /q{num}
def send_question_by_number(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    try:
        num = int(update.message.text[2:])
        question = fetch_question_by_number(num)
        if not question:
            update.message.reply_text("❗ 해당 번호의 문제가 없습니다.")
            return
        user_sessions[user_id] = {"question_id": question["id"], "start_time": time.time()}
        text = f"📘 문제 {question['number']}\n{question['question']}\n\n"
        for idx, choice in enumerate(question['choices'], start=1):
            text += f"{chr(64+idx)}. {choice}\n"
        update.message.reply_text(text)
    except:
        update.message.reply_text("❗ 번호를 인식하지 못했습니다.")

# 📌 /a (이전 문제 보기)
def show_last_question(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    question = fetch_last_question_id(user_id)
    if not question:
        update.message.reply_text("📭 최근 문제 기록이 없습니다.")
        return
    text = f"📘 문제 {question['number']}\n{question['question']}\n\n"
    for idx, choice in enumerate(question['choices'], start=1):
        text += f"{chr(64+idx)}. {choice}\n"
    update.message.reply_text(text)

# 📌 답안 처리
def handle_answer(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip().upper()
    if msg not in ["A", "B", "C", "D", "E"]:
        return
    if user_id not in user_sessions:
        update.message.reply_text("❗ 먼저 문제를 받아주세요: /q")
        return

    selected = ord(msg) - 64
    session = user_sessions[user_id]
    qid = session["question_id"]
    elapsed = int(time.time() - session["start_time"])

    result = insert_user_answer(user_id, qid, selected, elapsed)
    correct = result["is_correct"]
    explanation = result["explanation"]
    q_num = result["number"]

    minutes = elapsed // 60
    seconds = elapsed % 60
    answer_text = (
        f"📘 문제 {q_num}번\n"
        f"당신의 선택: {msg}\n"
        f"{'✅ 정답입니다!' if correct else '❌ 오답입니다!'}\n\n"
        f"📝 해설: {explanation}\n\n"
        f"(풀이에 걸린 시간 {minutes}분 {seconds}초)\n"
        f"(현재 {result['solved_count']}/25 문제 풀이 완료)"
    )
    update.message.reply_text(answer_text)

# 📌 /wrong
def show_wrong(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    wrongs = fetch_wrong_questions(user_id)
    if not wrongs:
        update.message.reply_text("😎 틀린 문제가 없습니다!")
        return
    numbers = sorted([q["number"] for q in wrongs])
    update.message.reply_text("❌ 틀린 문제 번호: " + ", ".join(map(str, numbers)))

# 📌 /stats
def show_stats(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    stats = fetch_user_stats(user_id)
    text = f"✅ 맞은 문제: {stats['correct_count']}/{stats['total']}\n🎯 정답률: {stats['accuracy']}%"
    update.message.reply_text(text)

# 📌 버튼 클릭 처리
def handle_menu_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    query.answer()
    if data == "get_question":
        send_question(query, context)
    elif data == "show_stats":
        show_stats(query, context)
    elif data == "show_wrong":
        show_wrong(query, context)
    elif data == "show_help":
        help_command(query, context)

# ✅ 실행 메인
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("a", show_last_question))
    dp.add_handler(CommandHandler("wrong", show_wrong))
    dp.add_handler(CommandHandler("stats", show_stats))
    dp.add_handler(CallbackQueryHandler(handle_menu_buttons))

    for i in range(1, 100):  # /q1 ~ /q99
        dp.add_handler(CommandHandler(f"q{i}", send_question_by_number))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))

    print("🤖 GMAT CR 봇 시작 중...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
