import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
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
            "run_id": "TEXT",
            "name": "TEXT",
            "time": "TEXT",
            "schedule": "TEXT",
            "status": "TEXT DEFAULT 'running'",
            "progress_percent": "INTEGER DEFAULT 0",
            "current_step": "TEXT DEFAULT 'Initialisation'",
            "cost": "TEXT DEFAULT '0.00'",
            "duration": "TEXT DEFAULT '--'"
        }
        for col, type_def in needed.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE run_history ADD COLUMN {col} {type_def}")
                    print(f"Migration: added {col} to run_history")
                except Exception as e:
                    print(f"Migration error on run_history {col}: {e}")
    
    # Check script_inbox
    cursor.execute("PRAGMA table_info(script_inbox)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns:
        needed_script = {
            "image_prompts": "TEXT",
            "viral_score": "INTEGER DEFAULT 0",
            "money_score": "INTEGER DEFAULT 0",
            "run_type": "TEXT",
            "tiktok_url": "TEXT",
            "views": "INTEGER DEFAULT 0",
            "likes": "INTEGER DEFAULT 0",
            "shares": "INTEGER DEFAULT 0",
            "retention_rate": "INTEGER DEFAULT 0",
            "blog_summary": "TEXT",
            "selected_tools": "TEXT"
        }
        for col, type_def in needed_script.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE script_inbox ADD COLUMN {col} {type_def}")
                    print(f"Migration: added {col} to script_inbox")
                except Exception as e:
                    print(f"Migration error on script_inbox {col}: {e}")

    # Check agent_configs
    cursor.execute("PRAGMA table_info(agent_configs)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns:
        needed_agent = {
            "goal": "TEXT",
            "backstory": "TEXT"
        }
        for col, type_def in needed_agent.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE agent_configs ADD COLUMN {col} {type_def}")
                    print(f"Migration: added {col} to agent_configs")
                except Exception as e:
                    print(f"Migration error on agent_configs {col}: {e}")
            
    # Check system_config
    cursor.execute("PRAGMA table_info(system_config)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns:
        needed_sys = {
            "system_name": "TEXT DEFAULT 'Mission Control - Primary'",
            "environment": "TEXT DEFAULT 'Production (Live)'",
            "strict_mode": "BOOLEAN DEFAULT 1",
            "debug_logging": "BOOLEAN DEFAULT 0",
            "access_token": "TEXT DEFAULT 'im-dev-token-2026'",
            "allowed_ips": "TEXT DEFAULT '*'",
            "openai_key": "TEXT DEFAULT ''",
            "gemini_key": "TEXT DEFAULT ''",
            "fal_key": "TEXT DEFAULT ''",
            "stability_key": "TEXT DEFAULT ''",
            "elevenlabs_key": "TEXT DEFAULT ''",
            "auto_cleanup_days": "INTEGER DEFAULT 30",
            "discord_webhook": "TEXT DEFAULT ''",
            "telegram_token": "TEXT DEFAULT ''",
            "telegram_chat_id": "TEXT DEFAULT ''",
            "enable_alerts": "BOOLEAN DEFAULT 1",
            "commando_mode": "BOOLEAN DEFAULT 0",
            "last_reset": "TEXT"
        }
        for col, type_def in needed_sys.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE system_config ADD COLUMN {col} {type_def}")
                    print(f"Migration: added {col} to system_config")
                except Exception as e:
                    print(f"Migration error on system_config {col}: {e}")

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
    tiktok_url = Column(String, nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    retention_rate = Column(Integer, default=0)
    blog_summary = Column(String, nullable=True)
    selected_tools = Column(String, nullable=True) # JSON list of tool IDs or data
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

class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, index=True)
    daily_cap = Column(Float, default=15.0)
    today_spend = Column(Float, default=0.0)
    auto_stop = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    system_name = Column(String, default="Mission Control - Primary")
    environment = Column(String, default="Production (Live)")
    strict_mode = Column(Boolean, default=True)
    debug_logging = Column(Boolean, default=False)
    commando_mode = Column(Boolean, default=False)
    
    # Security & Access
    access_token = Column(String, default="im-dev-token-2026")
    allowed_ips = Column(String, default="*")
    
    # API Keys (Stored in DB for UI management, overriding .env if present)
    openai_key = Column(String, default="")
    gemini_key = Column(String, default="")
    fal_key = Column(String, default="")
    stability_key = Column(String, default="")
    elevenlabs_key = Column(String, default="")
    
    # Data Management
    auto_cleanup_days = Column(Integer, default=30)
    
    # Notifications
    discord_webhook = Column(String, default="")
    telegram_token = Column(String, default="")
    telegram_chat_id = Column(String, default="")
    enable_alerts = Column(Boolean, default=True)
    
    last_reset = Column(DateTime, default=datetime.utcnow)

class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, index=True) 
    from_agent = Column(String)
    to_agent = Column(String)
    message_type = Column(String) 
    summary = Column(String)
    payload = Column(String) 
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, unique=True, index=True)
    name = Column(String)
    model = Column(String, default="openai/gpt-4o-mini")
    goal = Column(String, nullable=True)
    backstory = Column(String, nullable=True)
    temperature = Column(String, default="0.7")
    status = Column(String, default="Idle")
    is_active = Column(Boolean, default=True)

class GrowthRecommendation(Base):
    __tablename__ = "growth_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # scale, alert, pivot
    title = Column(String)
    description = Column(String)
    action_label = Column(String, default="Apply to Pipeline")
    created_at = Column(DateTime, default=datetime.utcnow)

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category = Column(String)
    description = Column(String)
    cta = Column(String, default="Tester Gratuitement")
    link = Column(String)
    gradient = Column(String, default="from-cyan-400 to-emerald-400")
    reconciliation_keywords = Column(String) # e.g. "voice, tts, speech"
    is_active = Column(Boolean, default=True)

# Create all tables in the engine
Base.metadata.create_all(bind=engine)
migrate_db()

# Seeding default recommendations if empty
db = SessionLocal()
if db.query(GrowthRecommendation).count() == 0:
    recs = [
        GrowthRecommendation(
            type="scale", 
            title="Scale this niche", 
            description="'Self-hosting for Beginners' content outperformed the baseline by 35%. Dedicate 1 extra run per week to this topic.",
            action_label="Apply to Pipeline"
        ),
        GrowthRecommendation(
            type="alert", 
            title="Change hook structure", 
            description="Listicles starting with 'Stop doing this...' are showing high ad fatigue. Try curiosity gaps ('I tried X for 30 days...').",
            action_label="Update Prompts"
        ),
        GrowthRecommendation(
            type="pivot", 
            title="Pivot format", 
            description="Videos over 60s are losing 80% retention. Limit scripts to 45s maximum length for the next 7 days.",
            action_label="Adjust Scripting"
        )
    ]
    db.add_all(recs)
    db.commit()
db.close()
def seed_agents():
    db = SessionLocal()
    count = db.query(AgentConfig).count()
    if count == 0:
        defaults = [
            {
                "role": "TrendRadar", 
                "name": "TrendRadar", 
                "model": "openai/gpt-4o-mini",
                "goal": "Scanner les flux RSS et GitHub pour trouver des sujets TikTok sur le self-hosting et l'IA.",
                "backstory": "Tu es un expert en sourcing Open Source. Tu cherches des \"Killer Features\" gratuites. RÈGLE : Requêtes de 2-3 mots max."
            },
            {
                "role": "ViralJudge", 
                "name": "ViralJudge", 
                "model": "openai/gpt-4o-mini",
                "goal": "Valider la gratuité du sujet et évaluer le potentiel viral.",
                "backstory": "Tu es un analyste de tendances. Tu dois absolument t'assurer que le sujet est gratuit. SI LE PRIX EST FLOU, écris simplement \"Needs_Human_Verification\"."
            },
            {
                "role": "MonetizationScorer", 
                "name": "MonetizationScorer", 
                "model": "openai/gpt-4o-mini",
                "goal": "Attribuer un score de rentabilité ROI (/100) pour chaque concept.",
                "backstory": "Tu es un consultant en rentabilité. Calcule le score toi-même sans déléguer."
            },
            {
                "role": "ScriptArchitect", 
                "name": "ScriptArchitect", 
                "model": "openai/gpt-4o-mini",
                "goal": "Rédiger un script TikTok ironique et percutant de 30 secondes.",
                "backstory": "Tu es le scénariste vedette de iM System. Ton script DOIT OBLIGATOIREMENT se terminer par : \"J'ai cassé Internet... encore.\" Mets 3 mots-clés stratégiques en MAJUSCULES."
            },
            {
                "role": "VisualPromptist", 
                "name": "VisualPromptist", 
                "model": "openai/gpt-4o-mini",
                "goal": "Créer exactement 7 prompts d'images cohérents pour FLUX qui racontent une histoire visuelle.",
                "backstory": "Tu es un directeur artistique de haut vol. Ta mission est de traduire le script en une suite logique de 7 images ultra-réalistes. RÈGLE D'OR : Storytelling visuel."
            },
            {
                "role": "QualityController", 
                "name": "QualityController", 
                "model": "openai/gpt-4o-mini",
                "goal": "Vérifier la cohérence globale du script et des prompts visuels.",
                "backstory": "Tu es le garant final. Tu vérifies le respect des contraintes et tu valides."
            },
        ]
        for d in defaults:
            db.add(AgentConfig(**d))
        db.commit()
    db.close()

seed_agents()

def seed_affiliates():
    db = SessionLocal()
    if db.query(AffiliateLink).count() == 0:
        links = [
            AffiliateLink(
                name="ElevenLabs", category="Voice IA", 
                description="La voix n°1 pour tes vidéos virales. Hyper-réaliste.",
                link="https://elevenlabs.io/?from=tonid",
                gradient="from-cyan-400 to-emerald-400",
                reconciliation_keywords="voix, tts, speech, audio, elevenlabs"
            ),
            AffiliateLink(
                name="Luma Dream Machine", category="Video Gen",
                description="Anime tes images Flux en vidéos cinématiques HD.",
                link="https://luma.ai",
                gradient="from-violet-500 to-fuchsia-500",
                reconciliation_keywords="video, animation, luma, kling, clip"
            ),
            AffiliateLink(
                name="Hetzner", category="Cloud Hosting",
                description="Le meilleur rapport qualité/prix pour auto-héberger tes outils.",
                link="https://hetzner.cloud",
                gradient="from-orange-400 to-red-500",
                reconciliation_keywords="hosting, server, cloud, vps, docker, self-hosting"
            )
        ]
        db.add_all(links)
        db.commit()
    db.close()

seed_affiliates()

def seed_system_config():
    db = SessionLocal()
    if db.query(SystemConfig).count() == 0:
        conf = SystemConfig(
            daily_cap=15.0,
            today_spend=2.45,
            auto_stop=True,
            is_active=True,
            system_name="Mission Control - Primary",
            environment="Production (Live)",
            strict_mode=True,
            debug_logging=False,
            access_token="im-dev-token-2026",
            allowed_ips="*",
            openai_key="",
            gemini_key="",
            fal_key="",
            stability_key="",
            elevenlabs_key="",
            auto_cleanup_days=30,
            discord_webhook="",
            telegram_token="",
            telegram_chat_id="",
            enable_alerts=True,
            commando_mode=False
        )
        db.add(conf)
        db.commit()
    db.close()

seed_system_config()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
