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
async def show_equbs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows a list of open Equbs to join."""
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT equb_id, title, amount, frequency FROM equbs WHERE status = 'Open'")
    equbs = cursor.fetchall()
    conn.close()

    if not equbs:
        await update.message.reply_text("There are no open Equbs to join right now.")
        return

    # Create a button for each Equb
    keyboard = []
    for eq in equbs:
        eq_id, title, amount, freq = eq
        keyboard.append([InlineKeyboardButton(f"{title} ({amount} ETB/{freq})", callback_data=f"join_{eq_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an Equb to join:", reply_markup=reply_markup)

async def join_equb_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the button click when a user selects an Equb to join."""
    query = update.callback_query
    await query.answer()
    
    # Extract the equb_id from the callback_data (e.g., "join_1" -> 1)
    data = query.data.split("_")
    equb_id = int(data[1])
    user_id = update.effective_user.id

    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # Check if the user is already in this Equb
    cursor.execute("SELECT * FROM members WHERE equb_id = ? AND user_id = ?", (equb_id, user_id))
    existing_member = cursor.fetchone()

    if existing_member:
        await query.edit_message_text("⚠️ You have already joined this Equb!")
    else:
        # Save the user's name to the users table (if they don't exist)
        user_name = update.effective_user.first_name
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id, full_name) VALUES (?, ?)", (user_id, user_name))
    
        # Add user to the Equb
        cursor.execute("INSERT INTO members (equb_id, user_id) VALUES (?, ?)", (equb_id, user_id))
        conn.commit()
        await query.edit_message_text(f"✅ You have successfully joined Equb #{equb_id}!")
        
    conn.close()
async def equb_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the details and members of an Equb."""
    # For now, we will just show info for Equb #1. Later, you can make this dynamic.
    equb_id = 1 
    
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # Get Equb details
    cursor.execute("SELECT title, amount, frequency, status FROM equbs WHERE equb_id = ?", (equb_id,))
    equb = cursor.fetchone()
    
    if not equb:
        await update.message.reply_text("❌ Equb not found.")
        conn.close()
        return
        
    title, amount, freq, status = equb
    
    # Get list of members
    cursor.execute("""
        SELECT users.full_name 
        FROM members 
        JOIN users ON members.user_id = users.telegram_id 
        WHERE members.equb_id = ?
    """, (equb_id,))
    members = cursor.fetchall()
    conn.close()
    
    # Build the message
    message = f"📊 **{title}**\n"
    message += f"💰 Contribution: {amount} ETB\n"
    message += f"🗓 Frequency: {freq}\n"
    message += f"📌 Status: {status}\n\n"
    
    message += f"👥 **Members ({len(members)}/10):**\n"
    if not members:
        message += "No one has joined yet.\n"
    else:
        for i, member in enumerate(members, 1):
            message += f"{i}. {member[0]}\n"
            
    await update.message.reply_text(message, parse_mode="Markdown")
def main():
    application = Application.builder().token(TOKEN).build()

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
    
    application.add_handler(CommandHandler("join", show_equbs))
    application.add_handler(CallbackQueryHandler(join_equb_callback, pattern="^join_"))
    application.add_handler(CommandHandler("info", equb_info)) # <-- NEW LINE
    # ----------------------
   

    print("Equb Bot is running with Join logic...")
    application.run_polling()

if __name__ == "__main__":
    main()
