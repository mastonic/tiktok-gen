import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "db.sqlite3")

def migrate():
    if not os.path.exists(db_path):
        print("Database not found, nothing to migrate.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check for run_history columns
    cursor.execute("PRAGMA table_info(run_history)")
    columns = [row[1] for row in cursor.fetchall()]
    
    needed_columns = {
        "progress_percent": "INTEGER DEFAULT 0",
        "current_step": "TEXT DEFAULT 'Initialisation'",
        "duration": "TEXT DEFAULT '--'",
        "schedule": "TEXT"
    }

    for col, type_def in needed_columns.items():
        if col not in columns:
            print(f"Adding column {col} to run_history...")
            try:
                cursor.execute(f"ALTER TABLE run_history ADD COLUMN {col} {type_def}")
            except Exception as e:
                print(f"Error adding {col}: {e}")

    # Check for script_inbox columns
    cursor.execute("PRAGMA table_info(script_inbox)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "image_prompts" not in columns:
        print("Adding column image_prompts to script_inbox...")
        cursor.execute("ALTER TABLE script_inbox ADD COLUMN image_prompts TEXT")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
