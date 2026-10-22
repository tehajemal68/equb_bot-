import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Replace this with your actual BotFather token
TOKEN = "8895388021:AAFHzNjKDfoN7tE30sUL0BZmkh-rRvaS3Hg"

# These are our conversation "states"
TITLE, AMOUNT, FREQUENCY = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Equb Bot!\n"
        "Use /new_equb to create a new savings circle."
    )

async def new_equb_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Let's create a new Equb! 📝\n\n"
        "First, what is the **name** of this Equb group? (e.g., 'Family Equb', 'Office Equb')\n\n"
        "Type /cancel at any time to stop.",
        parse_mode="Markdown"
    )
    return TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save the title in the bot's memory
    context.user_data['equb_title'] = update.message.text
    await update.message.reply_text(
        f"Great! The Equb is called: *{update.message.text}*.\n\n"
        "Next, what is the **amount** in Ethiopian Birr (ETB) each person will contribute? (e.g., 500 or 1000)",
        parse_mode="Markdown"
    )
    return AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        # Try to convert the text to a number
        amount = float(text)
        context.user_data['equb_amount'] = amount
        
        # Create buttons for frequency
        keyboard = [
            [
                InlineKeyboardButton("Daily", callback_data="Daily"),
                InlineKeyboardButton("Weekly", callback_data="Weekly"),
                InlineKeyboardButton("Monthly", callback_data="Monthly"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Amount set to *{amount} ETB*.\n\n"
            "Finally, how often will members contribute?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return FREQUENCY
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number (e.g., 500). Try again:")
        return AMOUNT

async def receive_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    frequency = query.data
    title = context.user_data['equb_title']
    amount = context.user_data['equb_amount']
    admin_id = update.effective_user.id
    
    # Save to Database!
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO equbs (admin_id, title, amount, frequency, max_members) VALUES (?, ?, ?, ?, ?)",
        (admin_id, title, amount, frequency, 10) # Defaulting max members to 10 for now
    )
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        f"✅ **Equb Created Successfully!**\n\n"
        f"📌 Name: {title}\n"
        f"💰 Amount: {amount} ETB\n"
        f"🗓 Frequency: {frequency}\n\n"
        f"Share this group with friends so they can join!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Action cancelled. Use /new_equb to start again.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    # We set up the ConversationHandler here
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_equb", new_equb_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
            FREQUENCY: [CallbackQueryHandler(receive_frequency)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    print("Equb Bot is running with database logic...")
    application.run_polling()

if __name__ == "__main__":
    main()
