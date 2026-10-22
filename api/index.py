import os, json, asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል!")

telegram_app.add_handler(CommandHandler("start", start))

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        req_json = request.get_json(force=True)
        update = Update.de_json(req_json, telegram_app.bot)

        # 🚨 This bridge allows Vercel to run the async Telegram logic
        async def process():
            async with telegram_app:
                await telegram_app.process_update(update)

        asyncio.run(process())
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Webhook is active"