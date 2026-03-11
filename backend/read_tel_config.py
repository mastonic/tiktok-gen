from database import SessionLocal, SystemConfig
db = SessionLocal()
conf = db.query(SystemConfig).first()
if conf:
    print(f"TELEGRAM_TOKEN: {conf.telegram_token}")
    print(f"TELEGRAM_CHAT_ID: {conf.telegram_chat_id}")
else:
    print("No system config found.")
db.close()
