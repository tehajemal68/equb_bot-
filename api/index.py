import os
import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION
# Replace with actual Telegram Admin User IDs (integers)
ADMIN_USER_IDS = [1736356581]  

# BOT TOKEN (Set this in Vercel Environment Variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# In-memory global state (suitable for low-latency state sharing across warm serverless instances)
# For production scale with strict persistence, consider Vercel KV / Redis / Supabase.
STATE = {
    "status": "waiting",  # "waiting", "spinning", "finished"
    "winner": None,
    "winning_segment": None,
    "timestamp": time.time()
}


@app.route('/api/auth', methods=['POST'])
def check_auth():
    """Verify if the connected Telegram user is an Admin."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id format"}), 400

    is_admin = user_id in ADMIN_USER_IDS
    return jsonify({
        "user_id": user_id,
        "is_admin": is_admin
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint polled by all clients for live synchronization."""
    return jsonify(STATE)


@app.route('/api/spin', methods=['POST'])
def trigger_spin():
    """Admin endpoint to initiate a spin and determine the winner."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    # Authorization Check
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Unauthorized"}), 401

    if user_id not in ADMIN_USER_IDS:
        return jsonify({"error": "Forbidden: Admin access required"}), 403

    # Prevent concurrent spins
    if STATE["status"] == "spinning":
        return jsonify({"error": "Spin already in progress"}), 400

    # Pick a random winner from 1 to 100
    winning_number = random.randint(1, 100)

    # Update State to Spinning
    STATE["status"] = "spinning"
    STATE["winner"] = winning_number
    STATE["winning_segment"] = winning_number
    STATE["timestamp"] = time.time()

    return jsonify({
        "success": True,
        "status": STATE["status"],
        "winner": winning_number
    })


@app.route('/api/reset', methods=['POST'])
def reset_draw():
    """Admin endpoint to reset the wheel for the next round."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Unauthorized"}), 401

    if user_id not in ADMIN_USER_IDS:
        return jsonify({"error": "Forbidden"}), 403

    STATE["status"] = "waiting"
    STATE["winner"] = None
    STATE["winning_segment"] = None
    STATE["timestamp"] = time.time()

    return jsonify({"success": True, "status": "waiting"})


@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Handles incoming Telegram bot updates."""
    update = request.get_json(silent=True) or {}
    
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            welcome_text = (
                "🎉 **Welcome to the Digital Equb / Lottery Bot!** 🎉\n\n"
                "Tap the button below or open the Mini App menu to participate in live draws."
            )
            
            # Send message via Telegram Bot API
            if TELEGRAM_BOT_TOKEN:
                import requests
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(url, json={
                    "chat_id": chat_id,
                    "text": welcome_text,
                    "parse_mode": "Markdown"
                })

    return jsonify({"ok": True})


# Handler for Vercel Serverless Function
if __name__ == '__main__':
    app.run(debug=True)
