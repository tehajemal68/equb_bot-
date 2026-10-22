import os
import json
import urllib.request
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN")

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json(force=True)
        
        # Check if the message is /start
        if 'message' in data and 'text' in data['message']:
            chat_id = data['message']['chat']['id']
            text = data['message']['text']
            
            if text == '/start':
                # Directly call the Telegram API to send the message
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                payload = {
                    "chat_id": chat_id, 
                    "text": "ሰላም! ቦቱ በክላውድ ላይ በተሳካ ሁኔታ ሰርቷል! (Bot is on the cloud!)"
                }
                
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(payload).encode('utf-8'), 
                    headers={'Content-Type': 'application/json'}
                )
                
                try:
                    urllib.request.urlopen(req)
                except Exception as e:
                    print(f"TELEGRAM ERROR: {e}")
                    
        return 'OK', 200
    return 'Bad Request', 400

@app.route('/', methods=['GET'])
def index():
    return "Webhook is active"