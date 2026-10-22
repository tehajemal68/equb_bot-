import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል!")

async def process_telegram_update(update_data):
    # We build the Application inside the request to avoid event loop conflicts in Vercel
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    await application.initialize()
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
    await application.shutdown()

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update_data = request.get_json(force=True)
        try:
            # Force Vercel to wait for the async process to finish
            asyncio.run(process_telegram_update(update_data))
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            return 'Error', 500
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/', methods=['GET'])
def index():
    return "Webhook is active"