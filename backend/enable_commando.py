from database import SessionLocal, SystemConfig
import json

def set_commando_mode(enabled: bool):
    db = SessionLocal()
    try:
        conf = db.query(SystemConfig).first()
        if conf:
            conf.commando_mode = enabled
            db.commit()
            print(f"COMMANDO_MODE successfully set to {enabled}")
        else:
            print("SystemConfig not found in DB.")
    finally:
        db.close()

if __name__ == "__main__":
    set_commando_mode(True)
