import sqlite3
from pathlib import Path

db_path = Path("c:/Users/w110480/OneDrive - Worldline/Documents/perso/tiktok-gen/backend/db.sqlite3")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, title, cover_image FROM script_inbox WHERE cover_image LIKE '%localhost%'")
rows = c.fetchall()
print("Found rows with localhost:")
for r in rows:
    print(r)

c.execute("UPDATE script_inbox SET cover_image = REPLACE(cover_image, 'http://localhost:5656', '') WHERE cover_image LIKE '%localhost%'")
print(f"Updated {c.rowcount} rows")

conn.commit()
conn.close()
