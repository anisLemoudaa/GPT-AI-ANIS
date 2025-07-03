import os
import logging
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from dotenv import load_dotenv
from telegram import Update, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# تحميل المتغيرات من ملف .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# تسجيل اللوق
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# دالة لجلب الفصول من مواقع المانغا
def get_chapters(title):
    sites = []
    try:
        search_url = f"https://mangalek.com/?s={title.replace(' ', '+')}"
        r = requests.get(search_url)
        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.select_one(".story-item a")
        if link:
            manga_url = link.get("href")
            manga_page = requests.get(manga_url)
            soup = BeautifulSoup(manga_page.text, "html.parser")
            chapters = soup.select(".chapters li a")
            result = []
            for ch in chapters:
                text = ch.text.strip()
                if "Chapter" in text:
                    result.append(text.split("Chapter")[-1].strip())
            if result:
                return manga_url, sorted(result, key=lambda x: float(x))
    except: pass
    return None, []

# صنع PDF من الصور
def make_pdf(imgs, title_url, chapter, source):
    pdf = FPDF()
    pdf.set_auto_page_break(0)
    for img in imgs:
        img_url = img.get("data-src") or img.get("src")
        if not img_url:
            continue
        img_data = requests.get(img_url).content
        with open("page.jpg", "wb") as f:
            f.write(img_data)
        pdf.add_page()
        pdf.image("page.jpg", x=0, y=0, w=210, h=297)
    filename = f"{title_url}_ch{chapter}_{source}.pdf"
    pdf.output(filename)
    return filename

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton("📚 أفضل 10 مانهوات", callback_data="top10")]]
    await update.message.reply_text(
        "👋 أهلاً بك في بوت المانغا والذكاء الاصطناعي!\n\n"
        "أرسل اسم المانغا أو المانهوا وسأعرض لك الفصول.\n"
        "أو اختر من الزر أدناه 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# التعامل مع الرسائل
user_manga_search = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        title = update.message.text.strip()
        manga_url, chapters = get_chapters(title)
        if not chapters:
            await update.message.reply_text("❌ لم أجد المانغا أو لا تحتوي على فصول.")
            return
        user_manga_search[update.effective_chat.id] = title
        buttons = [[InlineKeyboardButton(f"الفصل {ch}", callback_data=f"{title}|{ch}")] for ch in chapters[:30]]
        await update.message.reply_text("📖 اختر الفصل المراد تحميله:", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("⚠️ حدث خطأ أثناء معالجة طلبك.")

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "top10":
        top_list = [
            "1. Solo Leveling",
            "2. Nano Machine",
            "3. The Beginning After The End",
            "4. Eleceed",
            "5. The World After the Fall",
            "6. Regressor Instruction Manual",
            "7. Return of the Mount Hua Sect",
            "8. Murim Login",
            "9. Damn Reincarnation",
            "10. Helmut: The Forsaken Child"
        ]
        await query.edit_message_text("🔥 أفضل 10 مانهوات:\n\n" + "\n".join(top_list))
        return

    title, chapter = data.split("|")
    await query.edit_message_text("📥 جاري تحميل الفصل...")
    title_url = title.strip().lower().replace(" ", "-")
    url = f"https://mangalek.com/manga/{title_url}/chapter-{chapter}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    imgs = soup.select("div.chapter-images img")
    if not imgs:
        await query.message.reply_text("❌ لم يتم العثور على صور.")
        return
    file = make_pdf(imgs, title_url, chapter, "mangalek")
    await query.message.reply_document(InputFile(file), caption=f"✅ الفصل {chapter}")
    os.remove(file)

# أمر /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧙‍♂️ أرسل اسم أي مانغا/مانهوا وسأعرض الفصول المتوفرة!\n"
        "اختر الفصل لتحميله كملف PDF.\n"
        "اضغط /start لعرض القائمة مجددًا."
    )

# تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("🚀 Bot is running...")
    app.run_polling()
