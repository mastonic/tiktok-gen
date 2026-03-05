import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Setup SQLite Database in the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_db():
    import sqlite3
    if not os.path.exists(DB_PATH):
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check run_history
    cursor.execute("PRAGMA table_info(run_history)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if columns: # Only if table exists
        needed = {
            "progress_percent": "INTEGER DEFAULT 0",
            "current_step": "TEXT DEFAULT 'Initialisation'",
            "duration": "TEXT DEFAULT '--'",
            "schedule": "TEXT"
        }
        for col, type_def in needed.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE run_history ADD COLUMN {col} {type_def}")
                    print(f"Migration: added {col} to run_history")
                except:
                    pass
    
    # Check script_inbox
    cursor.execute("PRAGMA table_info(script_inbox)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns and "image_prompts" not in columns:
        try:
            cursor.execute("ALTER TABLE script_inbox ADD COLUMN image_prompts TEXT")
            print("Migration: added image_prompts to script_inbox")
        except:
            pass
            
    conn.commit()
    conn.close()

Base = declarative_base()

class ScriptInbox(Base):
    __tablename__ = "script_inbox"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    run_type = Column(String) # 'matin' or 'soir'
    final_script = Column(String)
    viral_score = Column(Integer)
    money_score = Column(Integer)
    keywords = Column(String)
    image_prompts = Column(String, nullable=True)
    status = Column(String, default="pending_review") # pending_review, approved, posted
    created_at = Column(DateTime, default=datetime.utcnow)

class PendingQuestion(Base):
    __tablename__ = "pending_questions"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String)
    context = Column(String)
    question = Column(String)
    answer = Column(String, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RunHistory(Base):
    __tablename__ = "run_history"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    name = Column(String)
    time = Column(String)
    schedule = Column(String)
    status = Column(String, default="running")
    progress_percent = Column(Integer, default=0)
    current_step = Column(String, default="Initialisation")
    cost = Column(String)
    duration = Column(String, default="--")
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # warning, info, danger
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables in the engine
Base.metadata.create_all(bind=engine)
migrate_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
