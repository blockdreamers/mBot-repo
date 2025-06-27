import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from supabase import create_client, Client
import re

# 🔐 Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🔗 Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🟢 /start

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("안녕하세요! /q 를 입력하면 GMAT CR 문제를 드립니다.")

# ❓ /q - Provide next unanswered question

def send_question(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    print(f"👤 User {user_id} requested a question...")

    try:
        answered_rows = supabase.table("user_answers") \
            .select("question_id") \
            .eq("user_id", user_id) \
            .execute()
        answered_ids = {row["question_id"] for row in answered_rows.data if row["question_id"]}

        questions = supabase.table("questions") \
            .select("*") \
            .order("question_number", desc=False) \
            .execute()

        for q in questions.data:
            if q["id"] not in answered_ids:
                question = q
                break
        else:
            update.message.reply_text("👏 모든 문제를 푸셨습니다!")
            return

        context.user_data["current_question"] = question
        context.user_data["start_time"] = datetime.now()
        context.user_data["question_id"] = question["id"]

        q_number = question.get("question_number", "?")
        q_text = question['question'].replace('\n', ' ').strip()
        text = f"*문제 {q_number}:*\n{q_text}\n\n"

        choices = question["choices"]
        for i, choice in enumerate(choices):
            text += f"{chr(65+i)}. {choice.strip()}\n"

        keyboard = [[InlineKeyboardButton(f"{chr(65+i)}", callback_data=str(i+1)) for i in range(5)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

    except Exception as e:
        update.message.reply_text(f"문제를 불러오는 중 오류가 발생했습니다.\n{str(e)}")

# 🔘 Handle answer button

def handle_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    selected = int(query.data)
    user_id = str(query.from_user.id)
    question = context.user_data.get("current_question")
    start_time = context.user_data.get("start_time")
    question_id = context.user_data.get("question_id")

    if not question or not start_time:
        query.edit_message_text("먼저 /q 명령어로 문제를 받아주세요.")
        return

    correct = int(question["answer"])
    is_correct = selected == correct
    submitted_at = datetime.now()
    elapsed_sec = int((submitted_at - start_time).total_seconds())
    qn = question.get("question_number", "?")
    explanation = question.get("explanation", "설명 없음")
    correct_letter = chr(64 + correct)

    try:
        supabase.table("user_answers").insert({
            "user_id": user_id,
            "question_id": question_id,
            "user_answer": selected,
            "is_correct": is_correct,
            "started_at": start_time.isoformat(),
            "submitted_at": submitted_at.isoformat(),
            "answered_at": submitted_at.isoformat()
        }).execute()
    except Exception as e:
        print(f"❌ DB Insert Failed for user {user_id}, Q{qn}: {str(e)}")

    total = supabase.table("questions").select("id").execute().data
    solved = supabase.table("user_answers").select("question_id").eq("user_id", user_id).execute().data
    solved_ids = {str(row["question_id"]) for row in solved if row["question_id"]}

    mins, secs = divmod(elapsed_sec, 60)
    time_str = f"{mins}분 {secs}초" if mins else f"{secs}초"

    result_text = (
        f"📘 문제 {qn}번\n"
        f"당신의 선택: {chr(64+selected)}\n"
        f"{'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}\n\n"
        f"📝 해설: {explanation.strip()}\n\n"
        f"(풀이에 걸린 시간 {time_str})\n"
        f"(현재 {len(solved_ids)}/{len(total)} 문제 풀이완료)"
    )
    try:
        query.edit_message_text(result_text, parse_mode='Markdown')
    except:
        query.message.reply_text(result_text)

# ✅ /wrong - 틀린 문제 다시 보여주기

def show_wrong(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    wrongs = supabase.table("user_answers").select("question_id").eq("user_id", user_id).eq("is_correct", False).execute().data
    if not wrongs:
        update.message.reply_text("🎉 틀린 문제가 없습니다!")
        return

    question_ids = [row["question_id"] for row in wrongs[:3]]
    for qid in question_ids:
        q = supabase.table("questions").select("*").eq("id", qid).single().execute().data
        if q:
            qn = q.get("question_number", "?")
            qt = q.get("question", "").replace('\n', ' ').strip()
            ans = chr(64 + int(q.get("answer", 1)))
            update.message.reply_text(f"📘 문제 {qn}번\n{qt}\n정답: *{ans}*", parse_mode='Markdown')

# ✅ /stats - 정답률 요약

def show_stats(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    data = supabase.table("user_answers").select("is_correct").eq("user_id", user_id).execute().data
    total = len(data)
    correct = sum(1 for row in data if row["is_correct"])
    rate = round((correct / total) * 100, 1) if total else 0
    update.message.reply_text(f"📊 정답률: {rate}%\n맞힌 문제 수: {correct} / {total}")

# ✅ /q{번호} 지원

def handle_custom_q(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    match = re.match(r"/q(\d+)$", text)
    if not match:
        return

    number = int(match.group(1))
    q = supabase.table("questions").select("*").eq("question_number", number).single().execute().data
    if not q:
        update.message.reply_text("해당 번호의 문제가 없습니다.")
        return

    context.user_data["current_question"] = q
    context.user_data["start_time"] = datetime.now()
    context.user_data["question_id"] = q["id"]

    q_text = q['question'].replace('\n', ' ').strip()
    text = f"*문제 {number}:*\n{q_text}\n\n"
    choices = q["choices"]
    for i, choice in enumerate(choices):
        text += f"{chr(65+i)}. {choice.strip()}\n"

    keyboard = [[InlineKeyboardButton(f"{chr(65+i)}", callback_data=str(i+1)) for i in range(5)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ▶️ Main loop

def main():
    print("🤖 GMAT CR 봇 시작 중...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("a", send_answer))
    dp.add_handler(CommandHandler("wrong", show_wrong))
    dp.add_handler(CommandHandler("stats", show_stats))
    dp.add_handler(MessageHandler(Filters.regex(r"/q\\d+$"), handle_custom_q))
    dp.add_handler(CallbackQueryHandler(handle_button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
