from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace this with the token you got from BotFather
TOKEN = "8895388021:AAFHzNjKDfoN7tE30sUL0BZmkh-rRvaS3Hg"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    await update.message.reply_text(
        "👋 Welcome to the Equb Bot!\n"
        "Use /new_equb to create a new savings circle."
    )

async def new_equb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /new_equb command."""
    # In the future, this is where you will ask for amount, frequency, etc.
    await update.message.reply_text(
        "🔄 *New Equb Circle*\n"
        "This feature is under construction. Soon you will be able to set the amount and invite members here.",
        parse_mode="Markdown"
    )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("new_equb", new_equb))

    # Run the bot until you press Ctrl+C
    print("Equb Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
