import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Vercel will get this token from the Environment Variables we set later
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል! (Bot is working on the cloud!)")

async def webhook(request):
    """Handle incoming Telegram updates."""
    if request.method == "POST":
        # Initialize the bot
        application = Application.builder().token(TOKEN).build()
        
        # Add your handlers here
        application.add_handler(CommandHandler("start", start))
        
        # Process the update from Telegram
        req_json = await request.json()
        update = Update.de_json(req_json, application.bot)
        
        await application.initialize()
        await application.process_update(update)
        
        return {"statusCode": 200, "body": "OK"}
    
    return {"statusCode": 200, "body": "Webhook is active"}
