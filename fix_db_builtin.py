import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "backend", "db.sqlite3")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("PRAGMA table_info(script_inbox)")
cols = [r[1] for r in c.fetchall()]

changed_total = 0

for col in cols:
    try:
        c.execute(f"UPDATE script_inbox SET {col} = REPLACE({col}, 'http://localhost:5656', '') WHERE {col} LIKE '%localhost:5656%'")
        if c.rowcount > 0:
            print(f"Updated {c.rowcount} rows in column {col}")
            changed_total += c.rowcount
    except Exception as e:
        pass

conn.commit()
conn.close()

if changed_total == 0:
    print("No localhost links found in script_inbox database.")
else:
    print(f"Total changes committed to DB: {changed_total}")
