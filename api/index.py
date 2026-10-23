import os
import json
import random
import urllib.request
from flask import Flask, request, jsonify, send_from_directory

# Safely locate the public folder relative to the api folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, '..', 'public')

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

# Make sure this is a STRING
ADMIN_ID = "8749216989"  

GLOBAL_STATE = {"status": "waiting", "winner": None, "history": []}

@app.route('/api/auth', methods=['POST'])
def auth():
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        is_admin = (user_id == ADMIN_ID)
        print(f"AUTH CHECK: User {user_id} | Admin ID {ADMIN_ID} | Match: {is_admin}")
        return jsonify({"is_admin": is_admin, "received_id": user_id})
    except Exception as e:
        print(f"AUTH ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(GLOBAL_STATE)

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json
    user_id = str(data.get('user_id'))
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403
    winner = random.randint(1, 100)
    GLOBAL_STATE['status'] = 'spinning'
    GLOBAL_STATE['winner'] = winner
    return jsonify({"success": True, "winner": winner})

@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.json
    user_id = str(data.get('user_id'))
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403
    GLOBAL_STATE['status'] = 'waiting'
    GLOBAL_STATE['winner'] = None
    return jsonify({"success": True})

@app.route('/', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            if data['message']['text'] == '/start':
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                payload = {"chat_id": chat_id, "text": "👋 እንኳን ደህና መጡ! ለመጫወት ከታች ያለውን 'Halal Equb' ሜኑ ቁጥር ይጫኑ።"}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
    return 'OK', 200

# Serve the HTML
@app.route('/', methods=['GET'])
def serve_app():
    return send_from_directory(PUBLIC_DIR, 'index.html')