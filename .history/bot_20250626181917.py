import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
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

# ❓ /q - 다음 안 푼 문제 제공
def send_question(update: Update, context: CallbackContext) -> None:
    try:
        # 🔍 이미 푼 문제 번호 가져오기
        answered_response = supabase.table("answers").select("question_number").execute()
        answered_numbers = {row["question_number"] for row in answered_response.data if row["question_number"]}

        # 🔍 아직 안 푼 문제 중 가장 번호가 낮은 문제
        q_response = (
            supabase.table("questions")
            .select("*")
            .eq("type", "CR")
            .order("question_number", asc=True)
            .execute()
        )

        for q in q_response.data:
            qn = q.get("question_number")
            if qn and qn not in answered_numbers:
                question = q
                break
        else:
            update.message.reply_text("👏 모든 문제를 푸셨습니다!")
            return

    except Exception as e:
        update.message.reply_text(f"문제를 불러오는 중 오류가 발생했습니다.\n{str(e)}")
        return

    context.user_data["current_question"] = question
    context.user_data["start_time"] = datetime.now()

    # 🧹 문제 텍스트 정리
    q_number = question.get("question_number", "?")
    q_text = question['question'].replace('\n', '').strip()
    text = f"*문제 {q_number}:*\n{q_text}\n\n"

    choices = question["choices"]
    for i, choice in enumerate(choices):
        text += f"{chr(65+i)}. {choice.strip()}\n"

    # 🔘 답변 버튼
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

    correct_answer = int(question["answer"])
    is_correct = selected == correct_answer
    elapsed_sec = (datetime.now() - start_time).seconds
    question_number = question.get("question_number", None)

    # 🧾 기록 저장
    supabase.table("answers").insert({
        "question_number": question_number,
        "is_correct": is_correct,
        "elapsed_sec": elapsed_sec,
        "timestamp": datetime.now().isoformat()
    }).execute()

    result_text = (
        f"📘 문제 {question_number}번\n"
        f"당신의 선택: {chr(64+selected)}\n"
        f"{'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}"
    )
    query.edit_message_text(result_text)

# ✅ /a - 정답 보기
def send_answer(update: Update, context: CallbackContext) -> None:
    question = context.user_data.get("current_question")
    if not question:
        update.message.reply_text("먼저 /q 로 문제를 받아주세요.")
        return

    correct_letter = chr(65 + int(question["answer"]) - 1)
    explanation = question.get("explanation", "설명 없음")
    question_number = question.get("question_number", "?")

    update.message.reply_text(
        f"📘 문제 {question_number}번\n"
        f"정답: *{correct_letter}*\n\n"
        f"📝 해설: {explanation}",
        parse_mode='Markdown'
    )

# ▶️ 메인 실행
def main():
    print("🤖 GMAT CR 봇 시작 중...")
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
