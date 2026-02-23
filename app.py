import os
import json
import requests
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment variables
APP_ID = os.getenv('APP_ID', '1420931642825622')
APP_SECRET = os.getenv('APP_SECRET', '734281e752152647cfa8500475477544')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'MERA_SECRET_123')
PAGE_ID = os.getenv('PAGE_ID', '61587893352091')

# Log configuration on startup
logger.info("=" * 50)
logger.info("🚀 Facebook Leads API Starting...")
logger.info(f"📱 APP_ID: {APP_ID}")
logger.info(f"📄 PAGE_ID: {PAGE_ID}")
logger.info(f"🔑 ACCESS_TOKEN: {'Set ✅' if ACCESS_TOKEN else 'Missing ❌'}")
logger.info(f"🔐 VERIFY_TOKEN: {VERIFY_TOKEN}")
logger.info("=" * 50)

# Log folder setup
LOG_FOLDER = Path('logs')
LOG_FOLDER.mkdir(exist_ok=True)
logger.info(f"📂 Log folder created: {LOG_FOLDER.absolute()}")

def save_lead_to_log(lead_data):
    """Save lead data to JSON log file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"lead_{timestamp}_{lead_data.get('id', 'unknown')}.json"
        filepath = LOG_FOLDER / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(lead_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Lead saved: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving lead: {e}")
        return False

def fetch_lead_details(leadgen_id):
    """Fetch complete lead details from Facebook API"""
    try:
        url = f"https://graph.facebook.com/v21.0/{leadgen_id}"
        params = {
            'access_token': ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        lead_data = response.json()
        logger.info(f"📥 Lead fetched: {leadgen_id}")
        return lead_data
    except Exception as e:
        logger.error(f"❌ Error fetching lead {leadgen_id}: {e}")
        return None

@app.route('/')
def home():
    """Health check endpoint"""
    logger.info("📍 Root endpoint accessed")
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
    
    logger.info(f"🔍 Webhook verification request: mode={mode}, token={token}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info('✅ Webhook verified successfully!')
        return challenge, 200
    else:
        logger.warning('❌ Webhook verification failed!')
        return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming lead data from Facebook"""
    try:
        data = request.get_json()
        logger.info(f"📨 Webhook received: {json.dumps(data, indent=2)}")
        
        # Process lead data
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'leadgen':
                        leadgen_id = change.get('value', {}).get('leadgen_id')
                        
                        if leadgen_id:
                            logger.info(f"🎯 Processing lead: {leadgen_id}")
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
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
def view_logs():
    """View all saved leads"""
    try:
        logger.info("📂 Accessing logs endpoint")
        log_files = sorted(LOG_FOLDER.glob('*.json'), reverse=True)
        
        leads = []
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                lead_data = json.load(f)
                leads.append({
                    'filename': log_file.name,
                    'data': lead_data
                })
        
        logger.info(f"📊 Returning {len(leads)} leads")
        return jsonify({
            'total_leads': len(leads),
            'leads': leads
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Error fetching logs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test_connection():
    """Test Facebook API connection"""
    try:
        logger.info("🧪 Testing Facebook API connection...")
        logger.info(f"📱 PAGE_ID: {PAGE_ID}")
        logger.info(f"🔑 ACCESS_TOKEN length: {len(ACCESS_TOKEN) if ACCESS_TOKEN else 0}")
        
        # Check if token exists
        if not ACCESS_TOKEN:
            logger.error("❌ ACCESS_TOKEN is empty!")
            return jsonify({
                'status': 'error',
                'message': 'ACCESS_TOKEN is not set in environment variables',
                'access_token_valid': False
            }), 200
        
        # Test access token
        url = f"https://graph.facebook.com/v21.0/{PAGE_ID}"
        params = {
            'fields': 'name,id',
            'access_token': ACCESS_TOKEN
        }
        
        logger.info(f"📡 Making request to: {url}")
        
        response = requests.get(url, params=params, timeout=10)
        
        logger.info(f"📊 Response Status: {response.status_code}")
        logger.info(f"📄 Response Body: {response.text[:500]}")  # First 500 chars
        
        # Check if response is OK
        if response.status_code == 200:
            page_data = response.json()
            logger.info("✅ Facebook API connection successful!")
            return jsonify({
                'status': 'success',
                'message': 'Facebook API connection successful! ✅',
                'page_info': page_data,
                'access_token_valid': True
            }), 200
        else:
            # Return detailed error
            logger.error(f"❌ Facebook API returned error: {response.text}")
            return jsonify({
                'status': 'error',
                'message': f'Facebook API Error: {response.text}',
                'status_code': response.status_code,
                'access_token_valid': False
            }), 200
    
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout")
        return jsonify({
            'status': 'error',
            'message': 'Request timeout - Facebook API not responding',
            'access_token_valid': False
        }), 200
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request Error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Network Error: {str(e)}',
            'access_token_valid': False
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Unexpected Error: {str(e)}',
            'error_type': type(e).__name__,
            'access_token_valid': False
        }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🌐 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
