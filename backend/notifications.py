import os
import requests
import json
from database import SessionLocal, SystemConfig

def send_telegram_message(message: str):
    """Sends a text message to Telegram using bot token and chat ID from DB."""
    db = SessionLocal()
    conf = db.query(SystemConfig).first()
    db.close()
    
    if not conf or not conf.telegram_token or not conf.telegram_chat_id:
        print("Telegram notification skipped: Missing token or chat_id in SystemConfig.")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{conf.telegram_token}/sendMessage"
        payload = {
            "chat_id": conf.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def send_telegram_video(video_path: str, caption: str = ""):
    """Sends a video file to Telegram."""
    db = SessionLocal()
    conf = db.query(SystemConfig).first()
    db.close()
    
    if not conf or not conf.telegram_token or not conf.telegram_chat_id:
        print("Telegram video skip: Missing token or chat_id.")
        return False
        
    if not os.path.exists(video_path):
        print(f"Telegram video error: File not found at {video_path}")
        return False

    try:
        url = f"https://api.telegram.org/bot{conf.telegram_token}/sendVideo"
        files = {'video': open(video_path, 'rb')}
        data = {
            "chat_id": conf.telegram_chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, files=files, timeout=60)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram video: {e}")
        return False

def send_telegram_video_with_validation(video_path: str, script_id: int, caption: str = ""):
    """Sends a video to Telegram with 'Approve' and 'Reject' buttons."""
    db = SessionLocal()
    conf = db.query(SystemConfig).first()
    db.close()
    
    if not conf or not conf.telegram_token or not conf.telegram_chat_id:
        print("Telegram validation skip: Missing token or chat_id.")
        return False
        
    if not os.path.exists(video_path):
        print(f"Telegram validation error: File not found at {video_path}")
        return False

    try:
        url = f"https://api.telegram.org/bot{conf.telegram_token}/sendVideo"
        
        # Define the inline keyboard for Appoval
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ APPROUVER ET PUBLIER TikTok", "callback_data": f"tiktok_approve_{script_id}"},
                {"text": "❌ REJETER", "callback_data": f"tiktok_reject_{script_id}"}
            ]]
        }
        
        with open(video_path, 'rb') as f:
            files = {'video': f}
            data = {
                "chat_id": conf.telegram_chat_id,
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            response = requests.post(url, data=data, files=files, timeout=60)
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram video validation: {e}")
        return False
