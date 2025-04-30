import os
from telegram import Update, File
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
user_conversations = {}

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    content = update.message.text

    messages = user_conversations.get(user_id, [])
    messages.append({"role": "user", "content": content})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = f"Lỗi: {e}"

    user_conversations[user_id] = messages
    await update.message.reply_text(reply)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name
    file = await context.bot.get_file(doc.file_id)
    os.makedirs("downloads", exist_ok=True)
    path = os.path.join("downloads", file_name)
    await file.download_to_drive(path)

    message = f"📁 Em đã tải xong file: {file_name}."
    if file_name.endswith(('.docx', '.xlsx')):
        message += "\n➡️ Anh muốn em phân tích nội dung hay trích thông tin gì từ file này ạ?"
    else:
        message += "\n⚠️ Hiện tại em chưa đọc được định dạng này, nhưng nếu cần em có thể xử lý sau."

    await update.message.reply_text(message)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()
