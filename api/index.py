import os
import json
import random
import urllib.request
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='../public', static_url_path='')
TOKEN = os.environ.get("BOT_TOKEN")

# 🚨 IMPORTANT: YOUR TELEGRAM ID (Admin)
ADMIN_ID = 1808631552

# Global state for the live draw
GLOBAL_STATE = {
    "status": "waiting",
    "winner": None,
    "history": []
}

# --- 1. MINI APP API ENDPOINTS ---

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    user_id = data.get('user_id')
    
    # Check if the user opening the app is YOU (the Admin)
    is_admin = (user_id == ADMIN_ID)
    
    print(f"Auth Check: User {user_id} | Is Admin: {is_admin}")
    return jsonify({"is_admin": is_admin})

@app.route('/api/status', methods=['GET'])
def get_status():
    # Users poll this every 1.5 seconds to see if the Admin has spun
    return jsonify(GLOBAL_STATE)

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json
    user_id = data.get('user_id')
    
    # SECURITY: Block regular users from spinning
    if user_id != ADMIN_ID:
        return jsonify({"error": "Only Admin can spin"}), 403
        
    winner = random.randint(1, 100)
    GLOBAL_STATE['status'] = 'spinning'
    GLOBAL_STATE['winner'] = winner
    
    print(f"ADMIN SPUN THE WHEEL. Winner: {winner}")
    return jsonify({"success": True, "winner": winner})

@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id != ADMIN_ID:
        return jsonify({"error": "Only Admin can reset"}), 403

    GLOBAL_STATE['status'] = 'waiting'
    GLOBAL_STATE['winner'] = None
    return jsonify({"success": True})

# --- 2. TELEGRAM BOT WEBHOOK ---

@app.route('/', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            if text == '/start':
                send_telegram_message(chat_id, "👋 እንኳን ደህና መጡ! ለመጫወት ከታች ያለውን 'Halal Equb' ሜኑ ቁልፍ ይጫኑ።")
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

# --- 3. SERVE THE FRONTEND ---

@app.route('/')
def serve_app():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all for other static files (like CSS, images)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)