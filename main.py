import os
from dotenv import load_dotenv
from telegram import Update, File
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI
from flask import Flask
import threading

# Flask AutoPing cho Render
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Lucy bot đang hoạt động."

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

# Load biến môi trường
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
user_conversations = {}

# Handler: Văn bản
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        if user_id not in user_conversations:
            user_conversations[user_id] = [
                {"role": "system", "content": "Bạn là Lucy, một Trợ Lý Báo Cáo cá nhân, xưng Em với người dùng là Anh, phong cách thân thiện, chuyên nghiệp, rõ ràng."}
            ]
        user_conversations[user_id].append({"role": "user", "content": update.message.text})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=user_conversations[user_id],
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        user_conversations[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = f"❗️Lỗi xử lý văn bản: {e}"
        print(f"[LỖI handle_text] {e}")
    await update.message.reply_text(reply)

# Handler: Tài liệu
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document
        file_name = doc.file_name

        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        new_file: File = await context.bot.get_file(doc.file_id)
        file_path = os.path.join("downloads", file_name)
        await new_file.download_to_drive(file_path)

        message = f"📁 Em đã tải xong file: {file_name}."
        if file_name.endswith(('.docx', '.xlsx')):
            message += " ✨ Anh muốn em phân tích nội dung hay trích thông tin gì từ file này ạ?"
        else:
            message += " ⚠️ Hiện tại em chưa đọc được định dạng này, nhưng nếu cần em có thể xử lý sau."
        await update.message.reply_text(message)
    except Exception as e:
        print(f"[LỖI handle_document] {e}")
        await update.message.reply_text(f"❗️Lỗi khi xử lý tài liệu: {e}")

# Error Handler toàn cục
async def error_handler(update, context):
    print(f"[LỖI GLOBAL] Update: {update}")
    print(f"[LỖI GLOBAL] Chi tiết: {context.error}")

# Khởi chạy
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)
    print("✅ Lucy bot đang chạy với Flask + AutoPing và logging lỗi đầy đủ!")
    app.run_polling()
