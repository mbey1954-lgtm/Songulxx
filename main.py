import os
import subprocess
import sys
import time
import re
from multiprocessing import Process
from flask import Flask # Render'ı kandırmak için gerekli
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8438897952:AAGIa251RWPHo99Goeu69Rn5w65CzlS2MVw"
BOT_DIR = "./bots"
os.makedirs(BOT_DIR, exist_ok=True)

# --- RENDER'I UYANIK TUTMA (WEB SERVER) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sistemi Aktif!" # Render bu sayfayı görecek

def run_flask():
    # Render PORT değişkenini otomatik atar
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- BOT YÖNETİM MANTIĞI ---
def install_and_run(file_path):
    while True:
        process = subprocess.Popen([sys.executable, file_path], stderr=subprocess.PIPE, text=True)
        _, stderr = process.communicate()
        
        if process.returncode != 0:
            # Eksik kütüphane hatası kontrolü
            if "ModuleNotFoundError" in stderr:
                module = re.search(r"No module named '([^']+)'", stderr).group(1)
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                continue
            break # Kritik hata varsa dur
        break

async def handle_py(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.file_name.endswith(".py"):
        file = await context.bot.get_file(doc.file_id)
        path = os.path.join(BOT_DIR, doc.file_name)
        await file.download_to_drive(path)
        
        # Botu arka planda başlat
        Process(target=install_and_run, args=(path,)).start()
        await update.message.reply_text(f"🚀 {doc.file_name} kuruluyor ve başlatılıyor!")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # 1. Web Sunucusunu Başlat (Render kapanmasın diye)
    Process(target=run_flask).start()
    
    # 2. Telegram Yönetici Botunu Başlat
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, handle_py))
    application.run_polling()
