import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

# Create the Flask app
app = Flask(__name__)

# Initialize the Telegram Application
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል! (Bot is working on the cloud!)")

# Add your handlers here
application.add_handler(CommandHandler("start", start))

@app.route('/', methods=['POST'])
async def webhook():
    """Process incoming Telegram updates."""
    if request.headers.get('content-type') == 'application/json':
        # Parse the update
        req_json = request.get_json(force=True)
        update = Update.de_json(req_json, application.bot)
        
        # Process the update
        await application.initialize()
        await application.process_update(update)
        await application.shutdown()
        
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/')
def index():
    return "Webhook is active"