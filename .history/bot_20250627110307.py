import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from supabase import create_client, Client

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

# ❓ /q 또는 /q<number> - Provide question
def send_question(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    message = update.message.text.strip()

    print(f"👤 User {user_id} requested a question...")

    try:
        # ✅ 유저가 이미 푼 문제 목록
        answered_rows = supabase.table("user_answers") \
            .select("question_id") \
            .eq("user_id", user_id) \
            .execute()
        answered_ids = {row["question_id"] for row in answered_rows.data if row["question_id"]}
        print(f"✅ User {user_id} has already solved {len(answered_ids)} questions.")

        # ✅ 전체 문제 목록
        questions = supabase.table("questions") \
            .select("*") \
            .order("question_number", desc=False) \
            .execute()

        question = None
        if message.startswith("/q") and len(message) > 2:
            try:
                num = int(message[2:])
                for q in questions.data:
                    if q["question_number"] == num:
                        question = q
                        break
                if not question:
                    update.message.reply_text(f"{num}번 문제를 찾을 수 없습니다.")
                    return
            except:
                update.message.reply_text("문제 번호를 잘못 입력했습니다. 예: /q12")
                return
        else:
            for q in questions.data:
                if q["id"] not in answered_ids:
                    question = q
                    break
            if not question:
                update.message.reply_text("👏 모든 문제를 푸셨습니다!")
                print(f"✅ User {user_id} completed all available questions.")
                return

        # 문제 전달
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
        print(f"📤 Sent question {q_number} to user {user_id}.")
        print(f"📌 DEBUG | selected question_id = {question['id']} ({type(question['id'])})")

    except Exception as e:
        update.message.reply_text(f"문제를 불러오는 중 오류가 발생했습니다.\n{str(e)}")
        print(f"❌ Error sending question to user {user_id}: {str(e)}")

# 🔘 Answer button handler
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
        print(f"⚠️ User {user_id} submitted an answer without a loaded question.")
        return

    correct = int(question["answer"])
    is_correct = selected == correct
    submitted_at = datetime.now()
    qn = question.get("question_number", "?")
    explanation = question.get("explanation", "설명 없음")
    correct_letter = chr(64 + correct)
    duration = submitted_at - start_time
    duration_sec = duration.total_seconds()

    print(f"📌 DEBUG | inserting question_id = {question_id} ({type(question_id)})")

    # ✅ 결과 기록
    try:
        print("📡 Attempting to insert user answer into Supabase...")
        insert_result = supabase.table("user_answers").insert({
            "user_id": user_id,
            "question_id": question_id,
            "user_answer": selected,
            "is_correct": is_correct,
            "started_at": start_time.isoformat(),
            "submitted_at": submitted_at.isoformat(),
            "answered_at": submitted_at.isoformat()
        }).execute()
        print(f"✅ DB Insert Success: {insert_result}")
    except Exception as e:
        print(f"❌ DB Insert Failed for user {user_id}, Q{qn}: {str(e)}")

    # ✅ 진척도 계산
    try:
        total_questions = supabase.table("questions").select("id").execute().data
        total_count = len(total_questions)

        answered = supabase.table("user_answers") \
            .select("question_id") \
            .eq("user_id", user_id) \
            .execute().data
        unique_answered = {str(row["question_id"]) for row in answered if row["question_id"]}
        progress = len(unique_answered)
    except Exception as e:
        print(f"⚠️ Failed to calculate progress for {user_id}: {str(e)}")
        progress, total_count = "?", "?"

    # ✅ 결과 메시지
    mins, secs = divmod(int(duration_sec), 60)
    duration_str = f"{mins}분 {secs}초" if mins else f"{secs}초"
    result_text = (
        f"📘 문제 {qn}번\n"
        f"당신의 선택: {chr(64+selected)}\n"
        f"{'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}\n\n"
        f"📝 해설: {explanation.strip()}\n\n"
        f"(풀이에 걸린 시간 {duration_str})\n"
        f"(현재 {progress}/{total_count} 문제 풀이 완료)"
    )
    try:
        query.edit_message_text(query.message.text_markdown_v2, parse_mode='MarkdownV2')
    except:
        query.edit_message_text(query.message.text, parse_mode='Markdown')  # fallback
    query.message.reply_text(result_text)

# 📉 /wrong - 틀린 문제 리스트
def wrong_answers(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    try:
        rows = supabase.table("user_answers") \
            .select("question_id, user_answer") \
            .eq("user_id", user_id) \
            .eq("is_correct", False) \
            .execute().data

        if not rows:
            update.message.reply_text("🥳 틀린 문제가 없습니다!")
            return

        question_numbers = []
        for row in rows:
            qid = row["question_id"]
            result = supabase.table("questions").select("question_number").eq("id", qid).execute().data
            if result:
                question_numbers.append(f"문제 {result[0]['question_number']}")

        text = "❌ 당신이 틀린 문제 목록:\n" + "\n".join(question_numbers)
        update.message.reply_text(text)
    except Exception as e:
        update.message.reply_text("문제 조회 중 오류 발생")
        print(f"❌ /wrong error: {str(e)}")

# 📊 /stats - 통계 보기
def stats(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    try:
        rows = supabase.table("user_answers") \
            .select("is_correct") \
            .eq("user_id", user_id) \
            .execute().data
        if not rows:
            update.message.reply_text("아직 푼 문제가 없습니다.")
            return
        total = len(rows)
        correct = sum(1 for r in rows if r["is_correct"])
        percent = round((correct / total) * 100)
        update.message.reply_text(f"✅ 맞은 문제: {correct}/{total} ({percent}%)")
    except Exception as e:
        update.message.reply_text("통계 조회 중 오류 발생")
        print(f"❌ /stats error: {str(e)}")

# ▶️ Main loop
def main():
    print("🤖 GMAT CR 봇 시작 중...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("wrong", wrong_answers))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CallbackQueryHandler(handle_button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
