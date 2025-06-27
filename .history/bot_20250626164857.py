# bot.py
import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler
from db import get_random_cr_question

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_cr(update, context):
    q = get_random_cr_question()
    if not q:
        update.message.reply_text("❌ 문제를 불러올 수 없습니다.")
        return

    choices = "\n".join([f"{i+1}. {c}" for i, c in enumerate(q['choices'])])
    message = f"🧠 *GMAT CR 문제*\n\n{q['question']}\n\n{choices}\n\n_정답은 /answer 입력 시 공개됩니다._"
    context.user_data["last_question"] = q
    update.message.reply_text(message, parse_mode='Markdown')

def send_answer(update, context):
    q = context.user_data.get("last_question")
    if not q:
        update.message.reply_text("먼저 /cr 명령어로 문제를 요청해주세요.")
        return
    update.message.reply_text(f"✅ 정답: *{q['answer']}*\n📘 해설: {q['explanation']}", parse_mode='Markdown')

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)  # <-- 여기가 핵심
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("cr", send_cr))
    dp.add_handler(CommandHandler("answer", send_answer))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
