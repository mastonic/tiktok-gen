import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "backend", "db.sqlite3")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, title, video_url, tiktok_url, final_script FROM script_inbox WHERE id=21")
row = c.fetchone()
print(f"Row 21: {row}")

c.execute("SELECT id, cover_image, video_url FROM script_inbox")
all_rows = c.fetchall()
for r in all_rows:
    if r[1] and "localhost:5656" in r[1]:
        print(f"id={r[0]} cover_image={r[1]}")

conn.close()
