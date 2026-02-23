import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path

app = Flask(__name__)

# Environment variables (Render pe set karenge)
APP_ID = os.getenv('APP_ID', '1420931642825622')
APP_SECRET = os.getenv('APP_SECRET', '734281e752152647cfa8500475477544')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', 'EAAUMVG3SG5YBQ0dUgPGC66mJZCUwaqt0CoEqER6HfCcFoSTs69ZCelDwJb6f6pZATnmNJ0x2TXL5QWQ81JeDnOI04l5LWD16kvpWFD2WG0Kt2ACMccj9ySOYIdrisBoIlJM76kDjQkXv86SIWZAYUygZBN9NvQF2dM7iPgbvwAzZAu1aASxThDBC6vOOiJjWNADDokHRlSAURpLJHAJcZBkr7WK3T4gAkLl3FDZCWmwZD')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'MERA_SECRET_123')
PAGE_ID = os.getenv('PAGE_ID', '61587893352091')

# Log folder setup
LOG_FOLDER = Path('logs')
LOG_FOLDER.mkdir(exist_ok=True)

def save_lead_to_log(lead_data):
    """Save lead data to JSON log file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"lead_{timestamp}_{lead_data.get('id', 'unknown')}.json"
        filepath = LOG_FOLDER / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lead_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Lead saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving lead: {e}")
        return False

def fetch_lead_details(leadgen_id):
    """Fetch complete lead details from Facebook API"""
    try:
        url = f"https://graph.facebook.com/v21.0/{leadgen_id}"
        params = {
            'access_token': ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        lead_data = response.json()
        print(f"📥 Lead fetched: {leadgen_id}")
        return lead_data
    except Exception as e:
        print(f"❌ Error fetching lead {leadgen_id}: {e}")
        return None

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'message': 'Facebook Leads API is running! 🚀',
        'endpoints': {
            'webhook': '/webhook (GET/POST)',
            'logs': '/logs (GET)',
            'test': '/test (GET)'
        }
    })

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Facebook webhook verification"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print('✅ Webhook verified successfully!')
        return challenge, 200
    else:
        print('❌ Webhook verification failed!')
        return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming lead data from Facebook"""
    try:
        data = request.get_json()
        print(f"📨 Webhook received: {json.dumps(data, indent=2)}")
        
        # Process lead data
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'leadgen':
                        leadgen_id = change.get('value', {}).get('leadgen_id')
                        
                        if leadgen_id:
                            # Fetch complete lead details
                            lead_data = fetch_lead_details(leadgen_id)
                            
                            if lead_data:
                                # Add metadata
                                lead_data['webhook_received_at'] = datetime.now().isoformat()
                                lead_data['page_id'] = entry.get('id')
                                
                                # Save to log
                                save_lead_to_log(lead_data)
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
def view_logs():
    """View all saved leads"""
    try:
        log_files = sorted(LOG_FOLDER.glob('*.json'), reverse=True)
        
        leads = []
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                lead_data = json.load(f)
                leads.append({
                    'filename': log_file.name,
                    'data': lead_data
                })
        
        return jsonify({
            'total_leads': len(leads),
            'leads': leads
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test_connection():
    """Test Facebook API connection"""
    try:
        # Test access token
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}"
        params = {
            'fields': 'name,id',
            'access_token': ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        page_data = response.json()
        
        return jsonify({
            'status': 'success',
            'message': 'Facebook API connection successful! ✅',
            'page_info': page_data,
            'access_token_valid': True
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'access_token_valid': False
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
