import sqlite3
import random
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove
)
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
AMOUNT, FREQUENCY = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Create a special keyboard button that asks for the phone number
    keyboard = [
        [KeyboardButton("📱 የስልክ ቁጥር አጋራ", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    welcome_text = (
        "👋 ወደ ሀላል እቁብ Bot እንኳን በደህና መጡ!\n\n"
        "ለመቀጠል ስልክ ቁጥርዎን ይጻፉ ወይም ከታች ያለውን ቁልፍ ተጭነው ስልክ ቁጥርዎን ያጋሩ።"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def new_equb_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Create buttons for standard amounts
    keyboard = [
        [InlineKeyboardButton("1000 Birr", callback_data="amt_1000"),
         InlineKeyboardButton("2000 Birr", callback_data="amt_2000")],
        [InlineKeyboardButton("5000 Birr", callback_data="amt_5000"),
         InlineKeyboardButton("10000 Birr", callback_data="amt_10000")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Let's create a new Equb! 📝\n\n"
        "First, select the **contribution amount**:\n\n"
        "Type /cancel at any time to stop.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Extract the amount from the button data (e.g., "amt_1000" -> 1000)
    amount = float(query.data.split("_")[1])
    context.user_data['equb_amount'] = amount
    
    # Create buttons for frequency
    keyboard = [
        [InlineKeyboardButton("Daily", callback_data="freq_Daily")],
        [InlineKeyboardButton("Weekly", callback_data="freq_Weekly")],
        [InlineKeyboardButton("Monthly", callback_data="freq_Monthly")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Amount set to **{int(amount)} Birr**.\n\n"
        "Now, how often will members contribute?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return FREQUENCY

async def receive_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Extract the frequency (e.g., "freq_Daily" -> "Daily")
    frequency = query.data.split("_")[1]
    amount = context.user_data['equb_amount']
    admin_id = update.effective_user.id
    
    # Automatically generate the title
    title = f"{int(amount)} Birr {frequency}"
    
    # Save to Database!
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO equbs (admin_id, title, amount, frequency, max_members) VALUES (?, ?, ?, ?, ?)",
        (admin_id, title, amount, frequency, 10)
    )
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        f"✅ **Equb Created Successfully!**\n\n"
        f"📌 Name: {title}\n"
        f"💰 Amount: {int(amount)} ETB\n"
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
        keyboard.append([InlineKeyboardButton(f"{title} (ID: {eq_id})", callback_data=f"join_{eq_id}")])
    
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
async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    equb_id = 1 # Hardcoded for now, just like /info
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # 1. Check if the person typing /draw is the Admin
    cursor.execute("SELECT admin_id, title FROM equbs WHERE equb_id = ?", (equb_id,))
    equb = cursor.fetchone()
    
    if not equb:
        await update.message.reply_text("❌ Equb not found.")
        conn.close()
        return
        
    admin_id, title = equb
    
    if user_id != admin_id:
        await update.message.reply_text("⚠️ Only the Admin of this Equb can draw the winner!")
        conn.close()
        return
        
    # 2. Find all members who haven't received a payout yet
    cursor.execute("""
        SELECT members.user_id, users.full_name 
        FROM members 
        JOIN users ON members.user_id = users.telegram_id 
        WHERE members.equb_id = ? AND members.has_received_payout = 0
    """, (equb_id,))
    eligible_members = cursor.fetchall()
    
    if not eligible_members:
        await update.message.reply_text("🏁 All members have already received their payout! The Equb cycle is complete.")
        conn.close()
        return
        
    # 3. Randomly select a winner
    winner = random.choice(eligible_members)
    winner_id = winner[0]
    winner_name = winner[1]
    
    # 4. Mark the winner in the database
    cursor.execute("UPDATE members SET has_received_payout = 1 WHERE equb_id = ? AND user_id = ?", (equb_id, winner_id))
    conn.commit()
    conn.close()
    
    # 5. Announce the winner
    message = (
        f"🎉 **PAYOUT TIME!** 🎉\n\n"
        f"🏆 The winner for **{title}** is...\n\n"
        f"✨ **{winner_name}** ✨\n\n"
        f"Congratulations! Please coordinate with the group to receive your funds."
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")
async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    full_name = update.effective_user.first_name
    phone_number = contact.phone_number
    
    # Save to database (INSERT OR REPLACE updates their number if they already exist)
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (telegram_id, full_name, phone_number) VALUES (?, ?, ?)",
        (user_id, full_name, phone_number)
    )
    conn.commit()
    conn.close()
    
    # Remove the phone number keyboard and send confirmation
    await update.message.reply_text(
        f"✅ ስልክ ቁጥርዎ በተሳካ ሁኔታ ተመዝግቧል: {phone_number}\n\n"
        "አሁን የሰማያዊውን 'Menu' ቁልፍ በመጫን /new_equb በመንካት አዲስ እቁብ መቀላቀል ይችላሉ!። ወይም /join በመጠቀም በመንካት ተጨማሪ እቁብ መቀላቀል ይችላሉ!",
        reply_markup=ReplyKeyboardRemove()
    )
async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows a list of Equbs the user is in to mark as paid."""
    user_id = update.effective_user.id
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # Find Equbs where the user is a member and hasn't paid yet
    cursor.execute("""
        SELECT equbs.equb_id, equbs.title, equbs.amount 
        FROM members 
        JOIN equbs ON members.equb_id = equbs.equb_id 
        WHERE members.user_id = ? AND members.has_paid = 0
    """, (user_id,))
    unpaid_equbs = cursor.fetchall()
    conn.close()
    
    if not unpaid_equbs:
        await update.message.reply_text("✅ እርስዎ ሁሉንም ክፍያዎች ከፍለዋል ወይም በምንም እቁብ ውስጥ አይደሉም!")
        return
        
    keyboard = []
    for eq in unpaid_equbs:
        eq_id, title, amount = eq
        keyboard.append([InlineKeyboardButton(f"Pay {int(amount)} ETB for {title}", callback_data=f"pay_{eq_id}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ለመክፈል የሚፈልጉትን እቁብ ይምረጡ (Select Equb to pay):", reply_markup=reply_markup)

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    equb_id = int(data[1])
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE members SET has_paid = 1 WHERE equb_id = ? AND user_id = ?", (equb_id, user_id))
    conn.commit()
    conn.close()
    
    await query.edit_message_text("✅ ክፍያዎ በተሳካ ሁኔታ ተመዝግቧል! (Payment recorded successfully!)")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows who has paid and who hasn't for a specific Equb."""
    try:
        equb_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Please specify an Equb ID. Example: `/status 1`", parse_mode="Markdown")
        return

    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # Get Equb name
    cursor.execute("SELECT title FROM equbs WHERE equb_id = ?", (equb_id,))
    eq = cursor.fetchone()
    if not eq:
        await update.message.reply_text("❌ Equb not found.")
        conn.close()
        return
    title = eq[0]
    
    # Get members and their payment status
    cursor.execute("""
        SELECT users.full_name, members.has_paid 
        FROM members 
        JOIN users ON members.user_id = users.telegram_id 
        WHERE members.equb_id = ?
    """, (equb_id,))
    members = cursor.fetchall()
    conn.close()
    
    message = f"📊 **Payment Status for {title}**\n\n"
    for m in members:
        name = m[0]
        paid = "✅ Paid" if m[1] == 1 else "❌ Not Paid"
        message += f"👤 {name}: {paid}\n"
        
    await update.message.reply_text(message, parse_mode="Markdown")

async def reset_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reset all payments for a new round."""
    try:
        equb_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Please specify an Equb ID. Example: `/reset 1`", parse_mode="Markdown")
        return

    user_id = update.effective_user.id
    conn = sqlite3.connect('equb.db')
    cursor = conn.cursor()
    
    # Check if Admin
    cursor.execute("SELECT admin_id FROM equbs WHERE equb_id = ?", (equb_id,))
    eq = cursor.fetchone()
    if not eq or eq[0] != user_id:
        await update.message.reply_text("⚠️ Only the Admin can reset payments.")
        conn.close()
        return
        
    cursor.execute("UPDATE members SET has_paid = 0 WHERE equb_id = ?", (equb_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"🔄 ሁሉም ክፍያዎች ለአዲሱ ዙር ተመልሰዋል! (All payments reset for the new round for Equb #{equb_id})")

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("new_equb", new_equb_start)],
    states={
        AMOUNT: [CallbackQueryHandler(receive_amount, pattern="^amt_")],
        FREQUENCY: [CallbackQueryHandler(receive_frequency, pattern="^freq_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, receive_contact))
    application.add_handler(conv_handler)
    
    application.add_handler(CommandHandler("join", show_equbs))
    application.add_handler(CallbackQueryHandler(join_equb_callback, pattern="^join_"))
    application.add_handler(CommandHandler("info", equb_info)) 
    application.add_handler(CommandHandler("draw", draw_winner)) 
    application.add_handler(CommandHandler("pay", pay_command))
    application.add_handler(CallbackQueryHandler(pay_callback, pattern="^pay_"))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("reset", reset_payments))
    # ----------------------
   

    print("Equb Bot is running with Join logic...")
    application.run_polling()

if __name__ == "__main__":
    main()
