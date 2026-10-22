import os
import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION: Replace with your actual Telegram numeric User ID
ADMIN_USER_IDS = [8749216989]  

# In-memory storage for global state and history
STATE = {
    "status": "waiting",  # "waiting", "spinning", "finished"
    "winner": None,
    "timestamp": time.time()
}

DRAW_HISTORY = []  # Stores past winners


@app.route('/api/auth', methods=['POST'])
def check_auth():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id format"}), 400

    is_admin = user_id in ADMIN_USER_IDS
    return jsonify({"user_id": user_id, "is_admin": is_admin})


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        **STATE,
        "history": DRAW_HISTORY
    })


@app.route('/api/spin', methods=['POST'])
def trigger_spin():
    data = request.get_json(silent=True) or {}
    try:
        user_id = int(data.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Unauthorized"}), 401

    if user_id not in ADMIN_USER_IDS:
        return jsonify({"error": "Forbidden: Admin access required"}), 403

    if STATE["status"] == "spinning":
        return jsonify({"error": "Spin already in progress"}), 400

    winning_number = random.randint(1, 100)

    STATE["status"] = "spinning"
    STATE["winner"] = winning_number
    STATE["timestamp"] = time.time()

    # Automatically log to history after spin completes simulation time
    DRAW_HISTORY.insert(0, {
        "winner": winning_number,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(STATE["timestamp"]))
    })
    # Keep only the last 10 draws
    if len(DRAW_HISTORY) > 10:
        DRAW_HISTORY.pop()

    return jsonify({"success": True, "status": STATE["status"], "winner": winning_number})


@app.route('/api/reset', methods=['POST'])
def reset_draw():
    data = request.get_json(silent=True) or {}
    try:
        user_id = int(data.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Unauthorized"}), 401

    if user_id not in ADMIN_USER_IDS:
        return jsonify({"error": "Forbidden"}), 403

    STATE["status"] = "waiting"
    STATE["winner"] = None
    STATE["timestamp"] = time.time()

    return jsonify({"success": True, "status": "waiting"})


if __name__ == '__main__':
    app.run(debug=True)
