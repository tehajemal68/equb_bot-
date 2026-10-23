import os
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)
ADMIN_ID = "8749216989"  # Make sure this matches your Telegram ID exactly

# Global state for the live draw
GLOBAL_STATE = {
    "status": "waiting",
    "winner": None,
    "history": []
}

@app.route('/api/auth', methods=['POST'])
def auth():
    try:
        data = request.json
        # Force to string to prevent type mismatch
        user_id = str(data.get('user_id', ''))
        is_admin = (user_id == ADMIN_ID)
        print(f"AUTH: User {user_id} | Admin Match: {is_admin}")
        return jsonify({"is_admin": is_admin, "debug_id": user_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(GLOBAL_STATE)

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json
    user_id = str(data.get('user_id', ''))
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403
        
    winner = random.randint(1, 100)
    GLOBAL_STATE['status'] = 'spinning'
    GLOBAL_STATE['winner'] = winner
    return jsonify({"success": True, "winner": winner})

@app.route('/api/reset', methods=['POST'])
def reset():
    data = request.json
    user_id = str(data.get('user_id', ''))
    if user_id != ADMIN_ID:
        return jsonify({"error": "Unauthorized"}), 403
        
    GLOBAL_STATE['status'] = 'waiting'
    GLOBAL_STATE['winner'] = None
    return jsonify({"success": True})