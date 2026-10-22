import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

# Create the application at the module level
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል!")

telegram_app.add_handler(CommandHandler("start", start))

async def process_update(update_data):
    # Initialize, process, and shut down within the same event loop
    await telegram_app.initialize()
    update = Update.de_json(update_data, telegram_app.bot)
    await telegram_app.process_update(update)
    await telegram_app.shutdown()

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update_data = request.get_json(force=True)
        try:
            # asyncio.run() creates a fresh event loop to execute the async tasks
            asyncio.run(process_update(update_data))
        except Exception as e:
            print(f"Error processing update: {e}")
            return 'Error', 500
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Webhook is active"