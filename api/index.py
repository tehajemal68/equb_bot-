import os
import json
import random
import urllib.request
import urllib.error
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

# --- IMPORTANT: PUT YOUR TELEGRAM ID HERE ---
ADMIN_ID = 8749216989  # Replace with your actual ID if different

# Global state (Since Vercel is serverless, this resets occasionally, 
# but it works perfectly for live events and testing)
GLOBAL_STATE = {
    "status": "waiting",
    "winner": None,
    "history": []
}

# --- 1. TELEGRAM BOT WEBHOOK ---
@app.route('/', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            if text == '/start':
                send_telegram_message(chat_id, "👋 እንኳን ደህና መጡ! ለመጫወት ከታች ያለውን 'Halal Equb' ሜኑ ቁልፍ ይጫኑ።")
            elif text == '/draw' and chat_id == ADMIN_ID:
                send_telegram_message(chat_id, "🎰 ዕጣውን ለመጣል የ Mini App ሜኑ ቁልፍን ይጫኑ!")
    except Exception as e:
        print(f"Webhook Error: {e}")
    return 'OK', 200

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

# --- 2. MINI APP API ENDPOINTS ---

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    user_id = data.get('user_id')
    # Check if the user opening the app is the Admin
    is_admin = (user_id == ADMIN_ID)
    return jsonify({"is_admin": is_admin})

@app.route('/api/status', methods=['GET'])
def get_status():
    # This is what the frontend checks every 1.5 seconds
    return jsonify(GLOBAL_STATE)

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json
    user_id = data.get('user_id')
    
    # Security check: Only Admin can spin
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403
        
    winner = random.randint(1, 100)
    GLOBAL_STATE['status'] = 'spinning'
    GLOBAL_STATE['winner'] = winner
    return jsonify({"success": True, "winner": winner})

@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403

    GLOBAL_STATE['status'] = 'waiting'
    GLOBAL_STATE['winner'] = None
    return jsonify({"success": True})

# --- 3. FRONTEND SERVING ---
@app.route('/')
def serve_app():
    # When Telegram opens the Mini App, it loads index.html from the public folder
    return app.send_static_file('../public/index.html')