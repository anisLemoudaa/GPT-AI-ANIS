import logging
import openai
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# التوكنات مباشرة
TELEGRAM_TOKEN = "8020390642:AAH69eHEuZ9sC38CeS3q7oFZRBtt-IMNov4"
OPENAI_API_KEY = "6cce0987e9582cdfa09cf83948c433e1fd0628c649aa887db83ad2c63ee6bbf8"

openai.api_key = OPENAI_API_KEY

# إعداد اللوق
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chat_history = {}  # لتتبع المحادثات لكل مستخدم

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في بوت Gptldarckbot الذكي!\n"
        "أرسل لي أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي 💬"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": "user", "content": message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # يمكنك تغييره إلى "gpt-4" لو أردت
            messages=chat_history[user_id]
        )
        reply = response.choices[0].message.content.strip()
        chat_history[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة سؤالك. حاول مرة أخرى لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
