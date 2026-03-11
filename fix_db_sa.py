import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.database import SessionLocal, ScriptInbox

db = SessionLocal()
scripts = db.query(ScriptInbox).all()
updated = 0
for s in scripts:
    changed = False
    if s.cover_image and "localhost:5656" in s.cover_image:
        s.cover_image = s.cover_image.replace("http://localhost:5656", "")
        changed = True
    if s.tiktok_url and "localhost:5656" in s.tiktok_url:
        s.tiktok_url = s.tiktok_url.replace("http://localhost:5656", "")
        changed = True
    if changed:
        updated += 1
if updated > 0:
    db.commit()
    print(f"Updated {updated} scripts.")
else:
    print("No scripts needed updating.")
db.close()
