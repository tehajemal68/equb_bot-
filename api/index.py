import os
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል!")

async def process_telegram_update(update_data):
    # Build the application inside the async function
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    update = Update.de_json(update_data, application.bot)
    
    # Official serverless pattern: initialize, process, then shutdown
    await application.initialize()
    await application.process_update(update)
    await application.shutdown()

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update_data = request.get_json(force=True)
        
        # Run the async function
        asyncio.run(process_telegram_update(update_data))
        
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Webhook is active"