import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from supabase import create_client, Client

# 🔐 Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🔗 Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🧾 Telegram 명령어 등록
def set_bot_commands(updater: Updater):
    commands = [
        BotCommand("start", "봇 시작 및 명령어 안내"),
        BotCommand("q", "다음 문제 풀기"),
        BotCommand("wrong", "틀린 문제 목록 보기"),
        BotCommand("stats", "내 문제 풀이 통계 보기"),
        BotCommand("help", "전체 명령어 설명 보기")
    ]
    updater.bot.set_my_commands(commands)

# 🟢 /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "안녕하세요! GMAT CR 문제풀이 봇입니다.\n"
        "아래 명령어들을 사용해보세요:\n"
        "/q - 문제 받기\n"
        "/q12 - 특정 문제 번호로\n"
        "/wrong - 틀린 문제 보기\n"
        "/stats - 통계 보기\n"
        "/help - 명령어 전체 보기"
    )

# 🆘 /help
def help_command(update: Update, context: CallbackContext) -> None:
    text = (
        "📚 사용 가능한 명령어 목록:\n\n"
        "/q - 다음 문제 받기\n"
        "/q12 - 12번 문제처럼 특정 번호로 이동\n"
        "/wrong - 내가 틀린 문제들\n"
        "/stats - 문제 풀이 통계\n"
        "/help - 이 도움말 보기"
    )
    update.message.reply_text(text)

# ❓ /q 또는 /q<number>
def send_question(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    message = update.message.text.strip()

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

        question = None
        if message.startswith("/q") and len(message) > 2:
            try:
                num = int(message[2:])
                question = next((q for q in questions.data if q["question_number"] == num), None)
                if not question:
                    update.message.reply_text(f"{num}번 문제를 찾을 수 없습니다.")
                    return
            except:
                update.message.reply_text("문제 번호를 잘못 입력했습니다. 예: /q12")
                return
        else:
            question = next((q for q in questions.data if q["id"] not in answered_ids), None)
            if not question:
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
        update.message.reply_text(f"문제를 불러오는 중 오류 발생\n{str(e)}")

# 🔘 버튼 선택
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
    qn = question.get("question_number", "?")
    explanation = question.get("explanation", "설명 없음")
    correct_letter = chr(64 + correct)
    duration = submitted_at - start_time
    duration_sec = duration.total_seconds()

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
        print(f"❌ DB Insert Failed: {str(e)}")

    # 진척도
    try:
        total = len(supabase.table("questions").select("id").execute().data)
        answered = supabase.table("user_answers") \
            .select("question_id") \
            .eq("user_id", user_id).execute().data
        progress = len({row["question_id"] for row in answered})
    except:
        progress = "?"

    mins, secs = divmod(int(duration_sec), 60)
    result_text = (
        f"📘 문제 {qn}번\n"
        f"당신의 선택: {chr(64+selected)}\n"
        f"{'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}\n\n"
        f"📝 해설: {explanation.strip()}\n\n"
        f"(풀이 시간: {mins}분 {secs}초)\n"
        f"(현재 {progress}/{total} 문제 풀이 완료)"
    )
    query.edit_message_text(query.message.text_markdown_v2, parse_mode='MarkdownV2')
    query.message.reply_text(result_text)

# ❌ /wrong
def wrong_answers(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    try:
        rows = supabase.table("user_answers") \
            .select("question_id") \
            .eq("user_id", user_id) \
            .eq("is_correct", False) \
            .execute().data

        if not rows:
            update.message.reply_text("🥳 틀린 문제가 없습니다!")
            return

        q_numbers = []
        for row in rows:
            result = supabase.table("questions").select("question_number").eq("id", row["question_id"]).execute().data
            if result:
                q_numbers.append(f"문제 {result[0]['question_number']}")

        update.message.reply_text("❌ 틀린 문제 목록:\n" + "\n".join(q_numbers))
    except Exception as e:
        update.message.reply_text("오류 발생: " + str(e))

# 📊 /stats
def stats(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    try:
        rows = supabase.table("user_answers").select("is_correct").eq("user_id", user_id).execute().data
        total = len(rows)
        correct = sum(1 for r in rows if r["is_correct"])
        percent = round((correct / total) * 100)
        update.message.reply_text(f"✅ 맞은 문제: {correct}/{total} ({percent}%)")
    except:
        update.message.reply_text("통계 조회 중 오류가 발생했습니다.")

# ▶️ main
def main():
    print("🤖 GMAT CR 봇 시작...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    set_bot_commands(updater)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("q", send_question))
    dp.add_handler(CommandHandler("wrong", wrong_answers))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(handle_button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
