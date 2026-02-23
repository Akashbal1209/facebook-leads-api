from flask import Flask, request
import json
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'API is running!'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = "MERA_SECRET_123"
        if request.args.get('hub.verify_token') == verify_token:
            return request.args.get('hub.challenge')
        return 'Invalid token', 403
    
    if request.method == 'POST':
        data = request.json
        with open('leads_log.txt', 'a') as f:
            f.write(f"{datetime.now()} | {json.dumps(data)}\n")
        return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
