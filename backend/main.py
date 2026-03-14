import sys
import os
import time
from pathlib import Path

# --- 1. Load Environment Variables First ---
env_path = Path(__file__).parent.parent / ".env.local"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Loaded environment from {env_path}")
    except ImportError:
        print("⚠️ python-dotenv not found, skipping .env.local loading (native os.environ will be used)")

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Body, Request
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import io
import json
import traceback
import re
import wave
import contextlib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from database import SessionLocal, ScriptInbox, PendingQuestion, RunHistory, SystemAlert, AgentConfig, AgentMessage, GrowthRecommendation, SystemConfig, AffiliateLink, save_agent_message
from datetime import datetime, timezone
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from notifications import send_telegram_message, send_telegram_video
from production import automate_visual_production

import comfyui_client
import video_gen
import tts_service
from render_video import generate_ass_subtitles

app = FastAPI(title="iM System API")

# Strict CORS for deployment
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "https://crewai972.xyz",
    "https://www.crewai972.xyz",
    "https://api.crewai972.xyz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Ensure media directory exists before mounting
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/")
async def root():
    return {"status": "online", "message": "iM-System API is running", "timestamp": datetime.now().isoformat()}

class AsyncLogCapture:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.loop = None
        self.history = []

    def write(self, text):
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        if not isinstance(text, str):
            text = str(text)
        if text.strip():
            self.history.append(text)
            if self.loop is None:
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    return
            try:
                self.loop.call_soon_threadsafe(self.queue.put_nowait, text)
            except Exception:
                pass # Event loop might be closed

    def flush(self):
        pass

log_capture = AsyncLogCapture()

@app.on_event("startup")
async def startup_event():
    # Capture the main asyncio loop explicitly on startup
    log_capture.loop = asyncio.get_running_loop()

async def log_generator():
    while True:
        try:
            message = await asyncio.wait_for(log_capture.queue.get(), timeout=1.0)
            yield f"data: {json.dumps({'log': message})}\n\n"
        except asyncio.TimeoutError:
            yield f": keep-alive\n\n"

@app.get("/api/stream")
async def stream_logs():
    return StreamingResponse(
        log_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

def update_run_progress(run_id: str, percent: int, step: str):
    if not run_id: return
    try:
        db = SessionLocal()
        run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
        if run_rec:
            run_rec.progress_percent = percent
            run_rec.current_step = step
            db.commit()
        db.close()
    except Exception as e:
        print(f"Error updating run progress: {e}")

def add_system_alert(alert_type: str, message: str):
    try:
        db = SessionLocal()
        db.add(SystemAlert(type=alert_type, message=message))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Error adding system alert: {e}")

from typing import Optional

def run_crew_sync(run_type: str, run_id: Optional[str] = None):
    # Hijack stdout
    old_stdout = sys.stdout
    sys.stdout = log_capture
    try:
        update_run_progress(run_id, 10, "Configuration des agents")
        msg = f"🚀 <b>iM-System [{run_type.upper()}]</b>\nDémarrage de l'essaim d'agents IA..."
        send_telegram_message(msg)
        
        save_agent_message(run_id, "System", "Swarm", "info", f"Démarrage d'un nouveau cycle Swarm ({run_type})")
        
        db = SessionLocal()
        agent_configs = db.query(AgentConfig).all()
        conf = db.query(SystemConfig).first()
        db.close()
        config_dict = {a.role: a.model for a in agent_configs}
        
        # 0. Sync Database API Keys to Environment
        if conf:
            if conf.openai_key: os.environ["OPENAI_API_KEY"] = conf.openai_key.strip()
            if conf.gemini_key: 
                g_key = conf.gemini_key.strip()
                os.environ["GEMINI_API_KEY"] = g_key
                os.environ["GOOGLE_API_KEY"] = g_key # Mirror for some libraries
                print(f"🔑 [SYNC] Gemini key synced: {g_key[:6]}...{g_key[-4:]}")
            if conf.fal_key: os.environ["FAL_KEY"] = conf.fal_key.strip()
            if conf.perplexity_key: os.environ["PERPLEXITY_API_KEY"] = conf.perplexity_key.strip()
            if conf.elevenlabs_key: os.environ["ELEVENLABS_KEY"] = conf.elevenlabs_key.strip()
        
        # 1. Prepare configuration and state
        commando_enabled = conf.commando_mode if conf else False
        mode_str = "commando" if commando_enabled else "standard"
        
        # 2. Execute via Sequential Crews (Human-in-the-Loop)
        update_run_progress(run_id, 25, "Sourcing du Top 5 News")
        
        # 2.1 Prepare Agents for Sourcing
        agents_out = create_agents(config=config_dict, commando_mode=commando_enabled)
        # Sourcing Crew consists of Luca (TrendRadar)
        trend_radar = agents_out[0]
        
        # Define Sourcing Tasks
        from tasks import create_tasks
        all_tasks = create_tasks(*agents_out, run_type=run_type, commando_mode=commando_enabled)
        sourcing_tasks = [all_tasks[0]] # Just task_scout (Top 5)
        
        # --- PHASE 1 : SOURCING (Luca) ---
        print("\n" + "="*50)
        print("🔍 PHASE 1 : SOURCING DU TOP 5 (Agents)")
        print("="*50)
        
        sourcing_crew = Crew(
            agents=[trend_radar],
            tasks=sourcing_tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=30
        )
        
        top_5_news = str(sourcing_crew.kickoff())
        
        # --- PHASE 2 : HUMAN-IN-THE-LOOP (Sélection de la News) ---
        print("\n" + "⚖️" * 20)
        print("TOP 5 NEWS IDENTIFIÉES PAR L'IA :")
        print("-" * 40)
        print(top_5_news)
        print("-" * 40)
        print("⚖️" * 20)
        
        update_run_progress(run_id, 40, "Validation requise (Niche Open Source)")
        
        db_hitl = SessionLocal()
        hitl_question = PendingQuestion(
            agent_name="TrendHunter",
            context=f"Le radar a identifié ces 5 news stratégiques :\n\n{top_5_news}",
            question="👉 Opération Commando (Sélection) : Copiez-collez ici la news que vous souhaitez traiter, ou insérez le lien GitHub/lien direct de l'outil Open Source choisi : "
        )
        db_hitl.add(hitl_question)
        db_hitl.commit()
        db_hitl.refresh(hitl_question)
        hitl_id = hitl_question.id
        db_hitl.close()
        
        print(f"📌 [HITL] Question #{hitl_id} créée.")
        print("👉 Opération Commando (Sélection) : Copiez-collez ici la news que vous souhaitez traiter, ou insérez le lien GitHub/lien direct de l'outil Open Source choisi : ")
        print("En attente de votre réponse sur le Dashboard...")
        
        decision_utilisateur = None
        waited_hitl = 0
        timeout_hitl = 3600
        while waited_hitl < timeout_hitl:
            time.sleep(10)
            waited_hitl += 10
            
            db_check = SessionLocal()
            q_check = db_check.query(PendingQuestion).filter(PendingQuestion.id == hitl_id).first()
            if q_check and q_check.is_resolved:
                decision_utilisateur = q_check.answer.strip()
                db_check.close()
                break
            db_check.close()
            
        if not decision_utilisateur or decision_utilisateur.upper() in ["NON", "STOP", "CANCEL"]:
            print("🛑 [HITL] Mission annulée.")
            update_run_progress(run_id, 100, "Mission annulée par l'utilisateur")
            return "Mission annulée par l'utilisateur."
        
        # In this flow, the response IS the news selection
        selected_news = decision_utilisateur
        print(f"🚀 [HITL] News sélectionnée reçue : {selected_news[:50]}...")
        
        print(f"🚀 [HITL] Validation reçue. Lancement de la production...")
        
        # --- PHASE 3 : PRODUCTION VIDÉO (VideoSquad) ---
        update_run_progress(run_id, 50, "Lancement de la VideoSquad (Opération Commando)")
        print("\n" + "="*50)
        print(f"🎬 PHASE 3 : PRODUCTION - GÉNÉRATION SCRIPT & VISUELS")
        print("="*50)
        
        # Video Crew: Les agents restants (Emma ne refait plus le filtre ici si déjà validé, mais on garde task_filter pour la structure)
        video_agents = list(agents_out[2:])
        # Important: On saute task_scout(0) et task_pick_best(1). On commence au task_filter(2) ou task_scoring
        video_tasks = all_tasks[2:]
        
        video_crew = Crew(
            agents=video_agents,
            tasks=video_tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=30
        )
        
        # Kickoff with news_validee input
        crew_result = video_crew.kickoff(inputs={"news_validee": selected_news})
        
        if hasattr(crew_result, "pydantic") and crew_result.pydantic:
            result = crew_result.pydantic.model_dump_json() if hasattr(crew_result.pydantic, "model_dump_json") else crew_result.pydantic.json()
        elif hasattr(crew_result, "json_dict") and crew_result.json_dict:
            result = json.dumps(crew_result.json_dict)
        else:
            result = str(crew_result)

        update_run_progress(run_id, 85, "Optimisation du script final")
        send_telegram_message(f"✅ <b>Script généré</b>\nAnalyse et scoring terminé par le Swarm.")
        save_agent_message(run_id, "QualityController", "System", "info", "Script généré, revue de qualité par le Swarm effectuée.")
        print(f"Execution completed.")
        
        # --- NEW ROBUST PARSING & AUTOMATION TRIGGER ---
        data = {}
        try:
            # Clean up markdown formatting (e.g., ```json)
            json_str = result.strip()
            if json_str.startswith("```json"):
                json_str = json_str.replace("```json\n", "", 1)
            if json_str.endswith("```"):
                json_str = json_str.rsplit("```", 1)[0]
                
            # Handle the "title='...' script='...'" format (pydantic repr fallback)
            if json_str.startswith("title=") and "script=" in json_str:
                print("⚠️ [PARSER] Detected pydantic-like string instead of JSON. Extracting fields...")
                t_match = re.search(r"title=['\"]([\s\S]*?)['\"],?\s+script=", json_str)
                s_match = re.search(r"script=['\"]([\s\S]*?)['\"],?\s+mots_cles=", json_str) or re.search(r"script=['\"]([\s\S]*?)['\"]", json_str)
                k_match = re.search(r"mots_cles=['\"]([\s\S]*?)['\"]", json_str)
                data = {
                    "title": t_match.group(1) if t_match else "Sans titre",
                    "script": s_match.group(1) if s_match else json_str,
                    "mots_cles": k_match.group(1) if k_match else "AI, Tech"
                }
            else:
                match = re.search(r'(\{[\s\S]*\})', json_str)
                if match:
                    json_str = match.group(1)
                
                if not json_str.strip():
                    raise ValueError("Extracted JSON string is empty.")
                    
                data = json.loads(json_str)
            print("✅ Successfully parsed result.")
        except Exception as parse_e:
            print(f"⚠️ Could not parse final output as JSON: {parse_e}. Using raw strings.")
            # Extract a title from the first line or first sentence
            fallback_title = result.split('\n')[0].strip('# ').strip()[:100]
            if not fallback_title or len(fallback_title) < 5:
                fallback_title = f"Sujet : {run_type.capitalize()} {time.strftime('%H:%M')}"
            
            data = {
                "title": fallback_title,
                "script": result,
                "viral_score": 70,
                "keywords": "AI, Viral, Tech"
            }

        # 1. Save to Database (Inbox)
        db = SessionLocal()
        try:
            title = data.get("title") or data.get("titre") or f"Script {run_type}"
            script_body = data.get("script", result)
            viral_score = data.get("score_roi") or data.get("viral_score", 85)
            kw_raw = data.get("keywords") or data.get("mots_cles", "AI, Automation")
            kw_str = kw_raw if isinstance(kw_raw, str) else ", ".join(kw_raw)
            
            new_script = ScriptInbox(
                title=title,
                run_type=run_type,
                final_script=script_body,
                viral_score=viral_score,
                money_score=90,
                keywords=kw_str,
                image_prompts=json.dumps(data.get("image_prompts", [])),
                status="pending_review"
            )
            db.add(new_script)
            
            # Log this as a system alert
            db.add(SystemAlert(type="info", message=f"Nouveau script généré : {new_script.title}"))
            
            db.commit()
            db.refresh(new_script) # Refresh to get the ID
            print(f"💾 Script saved to Inbox (ID: {new_script.id}).")
            
            # Send Telegram notification with script preview
            script_preview = data.get("script", result)[:300] + "..."
            send_telegram_message(f"📝 <b>Nouveau Script : {new_script.title}</b>\n\n{script_preview}\n\n<i>Lancement de la production visuelle (Images/Vidéo)...</i>")
            
            # 2. Trigger Automation (IMMEDIATELY AFTER SAVING)
            import threading
            
            # BlogSquad
            blog_concepts = data.get("top_5_concepts", [])
            blog_thread = threading.Thread(target=_run_blog_squad_sync, args=(blog_concepts,))
            blog_thread.start()
            
            # Visual Production
            if run_type in ["matin", "soir", "apres-midi", "atypique", "run"]:
                print(f"🎬 Launching Visual Production for script {new_script.id}")
                send_telegram_message(f"⚙️ <b>Automatisation</b>\nLancement visuel pour : {new_script.title}")
                prod_thread = threading.Thread(target=automate_visual_production, args=(new_script.id,))
                prod_thread.start()
                
            if run_id:
                run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
                if run_rec:
                    run_rec.status = "completed"
                    run_rec.progress_percent = 100
                    run_rec.current_step = "Terminé"
                    run_rec.cost = "0.05"
                    db.commit()
        except Exception as db_e:
            print(f"❌ Error in Post-Processing: {db_e}")
            # Fallback for run history update if DB save failed
            if run_id:
                run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
                if run_rec:
                    run_rec.status = "completed"
                    run_rec.progress_percent = 100
                    run_rec.current_step = "Terminé (Erreur Post-Traitement)"
                    run_rec.cost = "0.05"
                    db.commit()
        finally:
            db.close()
            
        return result
    except Exception as e:
        error_msg = f"ERROR in run_crew_sync:\n{traceback.format_exc()}"
        print(error_msg)
        add_system_alert("danger", f"Mission échouée : {str(e)[:100]}")
        return f"Error: {e}"
    finally:
        sys.stdout = old_stdout

@app.post("/api/run/{run_type}")
@app.post("/api/run")
async def run_mission(
    background_tasks: BackgroundTasks,
    run_type: Optional[str] = "matin", 
    payload: Optional[dict] = Body(None)
):
    try:
        # Determine the actual run type
        actual_run_type = "matin"
        if run_type and run_type in ["matin", "soir"]:
            actual_run_type = run_type
        
        if payload and isinstance(payload, dict) and payload.get("type") in ["matin", "soir"]:
            actual_run_type = payload.get("type")
            
        print(f"--- Triggered Run Mission: {actual_run_type} (Background) ---")
        
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        start_time_str = datetime.now().strftime("%I:%M %p")
        
        db = SessionLocal()
        new_run = RunHistory(
            run_id=run_id,
            name=f"iM System {actual_run_type.capitalize()}",
            time=start_time_str,
            schedule=actual_run_type,
            status="running",
            progress_percent=5,
            current_step="Initialisation",
            cost="0.00",
            duration="--"
        )
        db.add(new_run)
        db.commit()
        db.close()
        
        log_capture.history = []
        log_capture.write(f"--- DÉMARRAGE DU RUN {actual_run_type.upper()} ---\n")
        
        # Launch in background
        background_tasks.add_task(run_crew_sync, actual_run_type, run_id)
        
        return {
            "status": "success", 
            "message": f"Run {actual_run_type} started in background.", 
            "run_id": run_id
        }
        
    except Exception as e:
        print(f"Error starting mission: {traceback.format_exc()}")
        add_system_alert("danger", f"Échec du lancement : {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/api/run/{run_id}/stop")
async def stop_run(run_id: str):
    try:
        db = SessionLocal()
        run = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
        if run:
            run.is_cancelled = True
            run.status = "stopped"
            run.current_step = "Arrêté par l'utilisateur"
            db.commit()
            db.close()
            return {"status": "success", "message": "Arrêt demandé."}
        db.close()
        return {"status": "error", "message": "Run non trouvé."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/agents")
async def get_agents():
    db = SessionLocal()
    agents = db.query(AgentConfig).all()
    db.close()
    return [{
        "id": a.id,
        "role": a.role,
        "name": a.name,
        "status": a.status,
        "model": a.model,
        "goal": a.goal,
        "backstory": a.backstory,
        "is_active": a.is_active,
        "performance": 100
    } for a in agents]

class UpdateAgentPayload(BaseModel):
    id: int
    model: Optional[str] = None
    status: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    is_active: Optional[bool] = None

@app.post("/api/agents/update")
async def update_agent(payload: UpdateAgentPayload):
    db = SessionLocal()
    agent = db.query(AgentConfig).filter(AgentConfig.id == payload.id).first()
    if not agent:
        db.close()
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    
    if payload.model:
        agent.model = payload.model
    if payload.status:
        agent.status = payload.status
    if payload.goal:
        agent.goal = payload.goal
    if payload.backstory:
        agent.backstory = payload.backstory
    if payload.is_active is not None:
        agent.is_active = payload.is_active
    
    db.commit()
    db.close()
    return {"status": "success", "message": f"Agent {agent.name} mis à jour."}

@app.post("/api/agents/{agent_id}/reset")
async def reset_agent(agent_id: int):
    db = SessionLocal()
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        db.close()
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    
    # Defaults Mapping from agents.py
    defaults = {
        'TrendRadar': {
            'goal': 'Scanner les flux RSS et GitHub pour trouver des sujets TikTok sur le self-hosting et l\'IA.',
            'backstory': 'Tu es un expert en sourcing Open Source. Tu cherches des "Killer Features" gratuites. RÈGLE : Requêtes de 2-3 mots max.'
        },
        'ViralJudge': {
             'goal': 'Valider la gratuité du sujet et évaluer le potentiel viral.',
             'backstory': 'Tu es un analyste de tendances. Tu dois absolument t\'assurer que le sujet est gratuit. SI LE PRIX EST FLOU, écris simplement "Needs_Human_Verification".'
        },
        'MonetizationScorer': {
            'goal': 'Attribuer un score de rentabilité ROI (/100) pour chaque concept.',
            'backstory': 'Tu es un consultant en rentabilité. Calcule le score toi-même sans déléguer.'
        },
        'ScriptArchitect': {
            'goal': 'Rédiger un script TikTok ironique et percutant de 30 secondes.',
            'backstory': 'Tu es le scénariste vedette de iM System. Ton script DOIT OBLIGATOIREMENT se terminer par : "J\'ai cassé Internet... encore." Mets 3 mots-clés stratégiques en MAJUSCULES.'
        },
        'VisualPromptist': {
             'goal': 'Créer exactement 7 prompts d\'images cohérents pour FLUX qui racontent une histoire visuelle.',
             'backstory': 'Tu es un directeur artistique de haut vol. Ta mission est de traduire le script en une suite logique de 7 images ultra-réalistes. Template: Raw cinematic shot, 35mm film grain, hyper-realistic, [THÈME], lighting, bokeh, 8k resolution.'
        },
        'QualityController': {
            'goal': 'Vérifier la cohérence globale du script et des prompts visuels.',
            'backstory': 'Tu es le garant final. Tu vérifies le respect des contraintes et tu valides.'
        }
    }
    
    d = defaults.get(agent.role)
    if d:
        agent.goal = d['goal']
        agent.backstory = d['backstory']
        agent.model = "openai/gpt-4o-mini"
        db.commit()
        msg = f"Agent {agent.name} réinitialisé."
    else:
        msg = "Pas de défauts définis pour ce rôle."
        
    db.close()
    return {"status": "success", "message": msg}

@app.get("/api/trends")
async def get_trends():
    db = SessionLocal()
    scripts = db.query(ScriptInbox).order_by(ScriptInbox.id.desc()).limit(5).all()
    db.close()
    
    trends = []
    for s in scripts:
        try:
            trends.append({
                "id": s.id,
                "title": s.title or "Untitled Script",
                "viralScore": s.viral_score or 85,
                "moneyScore": s.money_score or 90,
                "finalScore": 88,
                "status": s.status or "pending",
                "tiktok_url": s.tiktok_url
            })
        except:
            continue
    return trends

@app.get("/api/runs")
async def get_runs():
    db = SessionLocal()
    runs = db.query(RunHistory).order_by(RunHistory.id.desc()).all()
    db.close()
    return [
        {
            "id": r.run_id,
            "name": r.name,
            "time": r.time,
            "schedule": r.schedule,
            "status": r.status,
            "progress_percent": r.progress_percent,
            "current_step": r.current_step,
            "cost": float(r.cost),
            "duration": r.duration
        } for r in runs
    ]

@app.get("/api/messages")
async def get_messages(content_id: str = None):
    db = SessionLocal()
    query = db.query(AgentMessage)
    if content_id:
        query = query.filter(AgentMessage.content_id == content_id)
    
    msgs = query.order_by(AgentMessage.timestamp.asc()).all()
    db.close()
    
    return [
        {
            "id": m.id,
            "content_id": m.content_id,
            "from_agent": m.from_agent,
            "to_agent": m.to_agent,
            "type": m.message_type,
            "summary": m.summary,
            "payload": json.loads(m.payload) if m.payload else {},
            "timestamp": m.timestamp.strftime("%H:%M:%S")
        } for m in msgs
    ]

@app.get("/api/logs/history")
async def get_log_history():
    return {"logs": log_capture.history}

@app.post("/api/contents/{item_id}/relaunch")
async def relaunch_content(item_id: str):
    db = SessionLocal()
    try:
        if item_id.startswith("db_"):
            db_id = int(item_id.replace("db_", ""))
            script = db.query(ScriptInbox).filter(ScriptInbox.id == db_id).first()
            if script:
                script.status = "pending_review"
                db.commit()
                return {"status": "success", "message": "Script renvoyé en relecture."}
        return {"status": "error", "message": "Item not found"}
    finally:
        db.close()

@app.get("/api/overview")
async def get_overview():
    try:
        db = SessionLocal()
        scripts = db.query(ScriptInbox).all()
        videos = sum(1 for s in scripts if s.status == "posted")
        # Get real spend from SystemConfig
        conf = db.query(SystemConfig).first()
        today_spend = conf.today_spend if conf else 0.0
        daily_cap = conf.daily_cap if conf else 15.0
        
        # Check if any run is currently 'running'
        active_run = db.query(RunHistory).filter(RunHistory.status == "running").order_by(RunHistory.id.desc()).first()
        is_running = active_run is not None
        last_run_id = active_run.run_id if active_run else None

        db.close()
        
        profit_score = sum(s.money_score or 0 for s in scripts) / max(len(scripts), 1)

        # Get recently linked videos
        recent_linked = db.query(ScriptInbox).filter(ScriptInbox.tiktok_url != None).order_by(ScriptInbox.id.desc()).limit(5).all()
        recent_linked_data = [
            {
                "id": f"db_{s.id}",
                "title": s.title,
                "views": s.views or 0,
                "date": s.created_at.strftime("%d/%m") if s.created_at else "-",
                "url": s.tiktok_url
            } for s in recent_linked
        ]

        db.close()
        
        profit_score = sum(s.money_score or 0 for s in scripts) / max(len(scripts), 1)

        return {
            "activeAgents": "5/5",
            "videosToday": f"{videos}/{max(videos, 2)}",
            "aiCostToday": f"${today_spend:.2f}",
            "estProfitScore": f"{profit_score:.1f}",
            "budgetRemaining": f"${max(0.0, daily_cap - today_spend):.2f}",
            "isRunning": is_running,
            "lastRunId": last_run_id,
            "recentLinked": recent_linked_data
        }
    except Exception as e:
        print(f"Error in get_overview: {traceback.format_exc()}")
        return {
            "activeAgents": "5/5",
            "videosToday": "0/2",
            "aiCostToday": "$0.00",
            "estProfitScore": "0.0",
            "budgetRemaining": "$15.00",
            "error": str(e)
        }

def parse_ass_subtitles(ass_path):
    if not os.path.exists(ass_path):
        return []
    subs = []
    try:
        with open(ass_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Dialogue:"):
                    parts = line.split(",", 9)
                    if len(parts) >= 10:
                        start_str = parts[1]
                        end_str = parts[2]
                        # Remove effects/tags like {\pos(540,1344)} and speaker labels like Narrateur:
                        text = re.sub(r'\{.*?\}', '', parts[9]).strip()
                        # Remove Speaker: prefixes (e.g. "Narrateur:", "Intervenant:")
                        text = re.sub(r'^[A-Za-zÀ-ÿ\s]+\[?.*?\]?\s*:\s*', '', text)
                        
                        def to_frames(s):
                            try:
                                h, m, sec = s.split(":")
                                return int((int(h)*3600 + int(m)*60 + float(sec)) * 30) # Assuming 30fps
                            except: return 0
                            
                        subs.append({
                            "text": text,
                            "start": to_frames(start_str),
                            "end": to_frames(end_str)
                        })
    except Exception as e:
        print(f"Error parsing ASS for Studio: {e}")
    return subs

@app.get("/api/contents")
async def get_contents():
    try:
        db = SessionLocal()
        scripts = db.query(ScriptInbox).order_by(ScriptInbox.id.desc()).all()
        db.close()
        
        db_contents = []
        for s in scripts:
            col = None # Don't show by default
            if s.status == "approved": col = "Waiting"
            elif s.status == "producing": col = "Scheduled"
            elif s.status == "posted": col = "Posted"
            
            if not col: continue # Skip items in pending_review, they stay in Approvals menu
            
            try:
                # Ensure we always return at least an empty list for prompts
                image_prompts = json.loads(s.image_prompts) if s.image_prompts else []
            except Exception as e:
                print(f"Error parsing prompts for {s.id}: {e}")
                image_prompts = []

            # Check for existing assets to persist state in Studio
            job_dir = f"media/production/db_{s.id}"
            has_images = False
            has_videos = False
            has_audio = False
            has_final_video = False
            existing_clips = []
            subtitles = []
            
            if os.path.exists(job_dir):
                # Images
                imgs = [f for f in os.listdir(job_dir) if f.startswith("img_") and f.endswith((".jpg", ".png"))]
                has_images = len(imgs) > 0
                
                # Videos (clips) - Check for normalized clips first (Better browser support)
                norm_clips = sorted([f for f in os.listdir(job_dir) if f.startswith("norm_clip_") and f.endswith(".mp4")])
                if norm_clips:
                    has_videos = True
                    existing_clips = [f"/media/production/db_{s.id}/{v}" for v in norm_clips]
                    print(f"🎬 [StudioData] Found {len(norm_clips)} normalized clips for {s.id}")
                else:
                    clips_dir = os.path.join(job_dir, "clips_video")
                    if os.path.exists(clips_dir):
                        vids = sorted([f for f in os.listdir(clips_dir) if f.endswith(".mp4")])
                        has_videos = len(vids) > 0
                        existing_clips = [f"/media/production/db_{s.id}/clips_video/{v}" for v in vids]
                        print(f"🎞️ [StudioData] Found {len(vids)} raw clips for {s.id}")
                
                # Audio
                has_audio = os.path.exists(os.path.join(job_dir, "voiceover.wav"))

                # Subtitles (New: Parse for Studio)
                sub_path = os.path.join(job_dir, "subtitles.ass")
                subtitles = parse_ass_subtitles(sub_path)
                if subtitles:
                    print(f"📝 [StudioData] Parsed {len(subtitles)} subtitles for {s.id}")

                # Final Video
                has_final_video = os.path.exists(os.path.join(job_dir, "final_output.mp4"))

            db_contents.append({
                "id": f"db_{s.id}",
                "title": s.title or "Untitled Generated Script",
                "script": s.final_script,
                "keywords": s.keywords,
                "imagePrompts": image_prompts,
                "viralScore": s.viral_score or 85,
                "moneyScore": s.money_score or 90,
                "finalScore": 88,
                "costEstimate": 0.05,
                "hasFinalVideo": has_final_video,
                "finalVideoUrl": f"/media/production/db_{s.id}/final_output.mp4" if has_final_video else None,
                "column": col,
                "assignedAgent": "QualityController",
                "riskScore": 10,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "date": s.created_at.strftime("%d/%m") if s.created_at else None,
                "hasImages": has_images,
                "hasVideos": has_videos,
                "hasAudio": has_audio,
                "existingClips": existing_clips,
                "subtitles": subtitles if 'subtitles' in locals() else []
            })
            
        db = SessionLocal()
        runs = db.query(RunHistory).filter(RunHistory.status == "running").all()
        db.close()
        for run in runs:
            # Multi-layered safety for cost
            try:
                cost_val = float(run.cost) if run.cost and str(run.cost).replace('.', '', 1).isdigit() else 0.0
            except:
                cost_val = 0.0
                
            db_contents.append({
                "id": f"run_{run.run_id}",
                "title": f"Processing {run.name}",
                "viralScore": 0,
                "moneyScore": 0,
                "finalScore": 0,
                "costEstimate": cost_val,
                "column": "Script",
                "assignedAgent": "Swarm",
                "imagePrompts": [],
                "hasImages": False,
                "hasVideos": False,
                "hasAudio": False,
                "existingClips": []
            })
        
        return db_contents
    except Exception as e:
        print(f"Error in get_contents: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/contents/{item_id}/move")
async def move_content(item_id: str, payload: dict):
    new_col = payload.get("column")
    db = SessionLocal()
    try:
        if item_id.startswith("db_"):
            db_id = int(item_id.replace("db_", ""))
            script = db.query(ScriptInbox).filter(ScriptInbox.id == db_id).first()
            if script:
                old_status = script.status
                # Map column to status
                if new_col == "Waiting": script.status = "approved"
                elif new_col == "Scheduled": script.status = "producing"
                elif new_col == "Posted": script.status = "posted"
                elif new_col == "Review": script.status = "pending_review"
                
                db.commit()
                
                # TRIGGER: If moved to Scheduled (now mapped to 'producing')
                if script.status == "producing" and old_status != "producing":
                    import threading
                    print(f"🚀 Manual Move to Scheduled: Launching visual production for script {script.id}")
                    send_telegram_message(f"⚙️ <b>Pipeline</b>\nScript '{script.title}' lancé en PRODUCTION.")
                    prod_thread = threading.Thread(target=automate_visual_production, args=(script.id,))
                    prod_thread.start()
                
                return {"status": "success"}
        return {"status": "error", "message": "Item not found or not moveable"}
    finally:
        db.close()

@app.delete("/api/contents/{item_id}")
async def delete_content(item_id: str):
    db = SessionLocal()
    try:
        if item_id.startswith("db_"):
            db_id = int(item_id.replace("db_", ""))
            script = db.query(ScriptInbox).filter(ScriptInbox.id == db_id).first()
            if script:
                db.delete(script)
                db.commit()
                return {"status": "success"}
        elif item_id.startswith("run_"):
            run_id = item_id.replace("run_", "")
            run = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
            if run:
                db.delete(run)
                db.commit()
                return {"status": "success"}
        return {"status": "error", "message": "Item not found"}
    finally:
        db.close()

@app.get("/api/approvals")
async def get_approvals():
    db = SessionLocal()
    questions = db.query(PendingQuestion).filter(PendingQuestion.is_resolved == False).all()
    scripts = db.query(ScriptInbox).filter(ScriptInbox.status == "pending_review").all()
    
    apps = []
    # 1. Human-in-the-loop topics
    for q in questions:
        apps.append({
            "id": f"q_{q.id}",
            "title": f"Question from {q.agent_name}",
            "type": "Topic",
            "status": "Pending",
            "context": q.context or "No context provided",
            "question": q.question or "No question available"
        })
        
    # 2. Generated scripts review
    for s in scripts:
        apps.append({
            "id": f"s_{s.id}",
            "title": s.title or "Generated Script Review",
            "type": "Script",
            "script": s.final_script,
            "keywords": s.keywords or "",
            "imagePrompts": json.loads(s.image_prompts) if s.image_prompts else [],
            "status": "Review",
            "context": "Final review of the generated script content.",
            "question": "Approve this script for final video generation and posting?"
        })

    # 3. Final Videos produced but not yet posted
    videos = db.query(ScriptInbox).filter(ScriptInbox.status == "approved").all()
    for v in videos:
        # Only add if final_output.mp4 exists
        video_path = f"media/production/db_{v.id}/final_output.mp4"
        if os.path.exists(video_path):
            apps.append({
                "id": f"v_{v.id}",
                "title": v.title or "Final Video Review",
                "type": "Video",
                "status": "Ready",
                "context": "Video is rendered and ready for final check.",
                "question": "Does the video look viral enough to post?",
                "videoUrl": f"/media/production/db_{v.id}/final_output.mp4"
            })

    db.close()
    return apps

@app.get("/api/alerts")
async def get_alerts():
    db = SessionLocal()
    alerts = db.query(SystemAlert).order_by(SystemAlert.id.desc()).limit(10).all()
    db.close()
    return [{"id": a.id, "type": a.type, "msg": a.message, "time": a.created_at.strftime("%H:%M")} for a in alerts]

@app.post("/api/approvals/{item_id}/approve")
async def approve_item(item_id: str):
    db = SessionLocal()
    prefix, db_id = item_id.split("_", 1)
    
    if prefix == "s":
        script = db.query(ScriptInbox).filter(ScriptInbox.id == int(db_id)).first()
        if script:
            script.status = "approved"
            db.commit()
            status = "success"
        else:
            status = "not_found"
    elif prefix == "q":
        question = db.query(PendingQuestion).filter(PendingQuestion.id == int(db_id)).first()
        if question:
            question.is_resolved = True
            question.answer = "Approved by human."
            db.commit()
            status = "success"
        else:
            status = "not_found"
    elif prefix == "v":
        script = db.query(ScriptInbox).filter(ScriptInbox.id == int(db_id)).first()
        if script:
            script.status = "posted" # Assuming approval on video moves it out of queue to posted
            db.commit()
            status = "success"
        else:
            status = "not_found"
    else:
        status = "invalid_id"
        
    db.close()
    return {"status": status}

@app.post("/api/approvals/{item_id}/reject")
async def reject_item(item_id: str):
    db = SessionLocal()
    prefix, db_id = item_id.split("_", 1)
    
    if prefix in ["s", "v"]:
        script = db.query(ScriptInbox).filter(ScriptInbox.id == int(db_id)).first()
        if script:
            script.status = "rejected"
            db.commit()
            status = "success"
        else:
            status = "not_found"
    elif prefix == "q":
        question = db.query(PendingQuestion).filter(PendingQuestion.id == int(db_id)).first()
        if question:
            question.is_resolved = True
            question.answer = "Rejected by human."
            db.commit()
            status = "success"
        else:
            status = "not_found"
    else:
        status = "invalid_id"
        
    db.close()
    return {"status": status}

@app.post("/api/contents/{content_id}/link-tiktok")
async def link_tiktok_url(content_id: str, payload: dict = Body(...)):
    tiktok_url = payload.get("url")
    if not tiktok_url:
        raise HTTPException(status_code=400, detail="Missing TikTok URL")
    
    db = SessionLocal()
    try:
        # Handle db_ prefix
        db_id_str = content_id.replace("db_", "")
        script = db.query(ScriptInbox).filter(ScriptInbox.id == int(db_id_str)).first()
        if not script:
            raise HTTPException(status_code=404, detail="Content not found")
        
        script.tiktok_url = tiktok_url
        script.status = "posted"
        
        # Initial mock stats for demonstration if they are 0
        if not script.views:
            script.views = 150 # Start with something
            script.likes = 12
            script.retention_rate = 45
            
        db.commit()
        return {"status": "success", "message": "TikTok URL linked and tracking started"}
    finally:
        db.close()

@app.get("/api/metrics")
async def get_metrics():
    db = SessionLocal()
    try:
        posted_scripts = db.query(ScriptInbox).filter(ScriptInbox.status == "posted").all()
        recs = db.query(GrowthRecommendation).order_by(GrowthRecommendation.created_at.desc()).all()
        
        total_views = sum(s.views or 0 for s in posted_scripts)
        total_likes = sum(s.likes or 0 for s in posted_scripts)
        avg_retention = sum(s.retention_rate or 0 for s in posted_scripts) / max(len(posted_scripts), 1)
        
        # Format numbers (e.g. 1500 -> 1.5K)
        def format_num(n):
            if n >= 1000000: return f"{n/1000000:.1f}M"
            if n >= 1000: return f"{n/1000:.1f}K"
            return str(n)

        # Generate chart data from last 7 days of posted content
        chart_data = []
        days_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        # Simplified: group by day of week
        for i, day in enumerate(days_en):
            morning_pts = sum(s.views or 0 for s in posted_scripts if s.run_type == "matin" and s.created_at.strftime("%a") == day)
            evening_pts = sum(s.views or 0 for s in posted_scripts if s.run_type == "soir" and s.created_at.strftime("%a") == day)
            chart_data.append({"name": days_fr[i], "morning": morning_pts, "evening": evening_pts})

        # Get detailed video performance list
        recent_videos = [
            {
                "id": f"db_{s.id}",
                "title": s.title,
                "views": format_num(s.views or 0),
                "likes": format_num(s.likes or 0),
                "retention": s.retention_rate or 0,
                "url": s.tiktok_url
            } for s in posted_scripts if s.tiktok_url
        ]

        return {
            "kpis": {
                "totalViews": format_num(total_views),
                "avgRetention": f"{int(avg_retention)}%",
                "engagement": f"{((total_likes / max(total_views, 1)) * 100):.1f}%" if total_views > 0 else "0%",
                "followers": f"+{total_likes // 10}" if total_likes > 0 else "0"
            },
            "chartData": chart_data,
            "recentVideos": recent_videos,
            "recommendations": [
                {
                    "id": r.id,
                    "type": r.type,
                    "title": r.title,
                    "description": r.description,
                    "action_label": r.action_label
                } for r in recs
            ]
        }
    finally:
        db.close()

class FluxPromptRequest(BaseModel):
    prompts: list[str]
    job_id: str
    is_square: bool = False

@app.post("/api/flux/generate")
def generate_flux_images(request: FluxPromptRequest):
    """
    Sends prompts to fal.ai (Flux Schnell) for high-quality, cost-optimized generation.
    BudgetOptimizer: $0.003/img.
    """
    job_dir = f"media/production/{request.job_id}"
    os.makedirs(job_dir, exist_ok=True)
    clips_dir = f"{job_dir}/clips_video"
    
    from video_gen import generate_flux_image
    
    generated_images = []
    for i, prompt in enumerate(request.prompts):
        idx_str = f"{i+1:02d}"
        filename = f"{job_dir}/img_{idx_str}.jpg"
        clip_path = f"{clips_dir}/clip_{idx_str}.mp4"
        
        # NEW: Delete old clip if it exists to force regeneration from new image
        if os.path.exists(clip_path):
            try: os.remove(clip_path)
            except: pass
            
        print(f"🎨 Regenerating image {idx_str}/{len(request.prompts)} with Fal.ai...")
        success = generate_flux_image(prompt, filename, is_square=request.is_square)
        
        # Cache busting for frontend
        ts = int(time.time())
        img_url = f"/media/production/{request.job_id}/img_{idx_str}.jpg?v={ts}"
        generated_images.append(img_url)

    return {"status": "success", "images": generated_images, "job_id": request.job_id}

video_generation_progress = {}

def process_image_to_video(job_dir_name, job_dir, clips_dir, prompt, is_square=False):
    import subprocess
    success_count = 0
    # Cyberpunk 2026 Standard: 15 clips
    total_clips = 15
    video_generation_progress[job_dir_name] = {"total": total_clips, "completed": 0, "status": "running"}
    
    for i in range(1, total_clips + 1):
        idx_str = f"{i:02d}"
        clip_name = f"clip_{idx_str}.mp4"
        clip_path = os.path.join(clips_dir, clip_name)
        img_path = os.path.join(job_dir, f"img_{idx_str}.jpg")
        
        # Check if high-quality clip already exists
        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1000:
            success_count += 1
            video_generation_progress[job_dir_name]["completed"] = success_count
            continue

        # Try to generate animation clip (STRICT I2V)
        vid_generated = False
        if os.path.exists(img_path):
            print(f"Uploading {img_path} to Fal for Studio I2V...")
            img_url = video_gen.upload_to_fal(img_path)
            if img_url:
                # Use Wan for the first clip (Hook), LTX for the rest
                if i == 1:
                    url = video_gen.generate_wan_video(prompt="", image_url=img_url, is_square=is_square)
                else:
                    url = video_gen.generate_ltx_video(prompt="", image_url=img_url, is_square=is_square)
                    
                if url and video_gen.download_video(url, clip_path):
                    vid_generated = True
            else:
                print(f"❌ Failed to upload {img_path} to Fal.")
        
        # FAILOVER logic: If animation fails OR image is missing
        if not vid_generated:
            print(f"⚠️ Failover: Creating static clip for {clip_name}")
            if os.path.exists(img_path):
                # Image to 5s Video
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
                        "-t", "5", "-pix_fmt", "yuv420p",
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
                        clip_path
                    ], check=True)
                    vid_generated = True
                except: pass
            
            if not vid_generated:
                # Black 5s Video
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=5", 
                        "-pix_fmt", "yuv420p", clip_path
                    ], check=True)
                except: pass

        success_count += 1
        video_generation_progress[job_dir_name]["completed"] = success_count
        
    video_generation_progress[job_dir_name]["status"] = "completed"
    print(f"Workflow Image-to-Video terminé. Sync complète sur 15 clips.")

@app.post("/api/workflows/image-to-video")
async def run_image_to_video(background_tasks: BackgroundTasks, payload: Optional[dict] = None):
    print("Executing Image-to-Video Master Workflow (Background)...")
    base_dir = "media/production"
    
    if payload and "script_id" in payload:
        job_dir_name = payload["script_id"]
    else:
        try:
            dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            job_dir_name = dirs[0] if dirs else None
        except Exception:
            job_dir_name = None

    if not job_dir_name:
        return {"status": "error", "message": "Aucun dossier projet trouvé avec des images."}

    job_dir = os.path.join(base_dir, job_dir_name)
    clips_dir = os.path.join(job_dir, "clips_video")
    os.makedirs(clips_dir, exist_ok=True)

    is_square = payload.get("is_square", False) if payload else False
    prompt = "Cinematic video of the prompt, high movement, high quality" # Default
    
    print(f"Generating 15 clips in {job_dir}. Background production started...")
    background_tasks.add_task(process_image_to_video, job_dir_name, job_dir, clips_dir, prompt, is_square=is_square)
    
    return {"status": "success", "message": "Génération de 15 clips démarrée en arrière-plan (I2V Stricte)..."}

@app.get("/api/workflows/progress/{job_id}")
async def get_video_progress(job_id: str):
    return video_generation_progress.get(job_id, {"status": "not_found"})

@app.post("/api/tts/generate")
async def generate_voice(payload: dict):
    script_id = payload.get("script_id")
    if not script_id: return {"status": "error", "message": "ID script manquant"}
    
    db = SessionLocal()
    script = db.query(ScriptInbox).filter(ScriptInbox.id == int(script_id.split("_")[1])).first()
    db.close()
    
    if not script: return {"status": "error", "message": "Script introuvable"}
    
    job_dir = os.path.join("media/production", script_id)
    os.makedirs(job_dir, exist_ok=True)
    voice_path = os.path.join(job_dir, "voiceover.wav")
    
    import tts_service
    tts_service.generate_tts(script.final_script, voice_path)
    
    # NEW: Trigger Subtitle generation (Whisper) automatically for Studio
    try:
        ass_path = os.path.join(job_dir, "subtitles.ass")
        keywords = [k.strip() for k in (script.keywords or "").split(",") if k.strip()]
        generate_ass_subtitles(script.final_script, keywords, ass_path, voice_path)
        print(f"📝 Subtitles generated for {script_id} in Studio.")
    except Exception as e:
        print(f"⚠️ Could not generate subtitles in Studio: {e}")

    return {"status": "success", "audioUrl": f"/{voice_path}"}

@app.post("/api/workflows/assemblage-viral")
async def run_assemblage_viral_endpoint(payload: dict = None):
    # This just calls the logic but ensures return format
    return await run_assemblage_viral(payload)

async def run_assemblage_viral(payload: Optional[dict] = None):
    print("Executing Assemblage Viral Workflow...")
    # Fetch script
    script_id = payload.get("script_id") if payload else None
    
    if script_id and str(script_id).startswith("db_"):
        db_id = int(script_id.split("_")[1])
        db = SessionLocal()
        script_record = db.query(ScriptInbox).filter(ScriptInbox.id == db_id).first()
        db.close()
        
        if not script_record:
            return {"status": "error", "message": "Script introuvable en BDD."}
            
        final_script = script_record.final_script
        job_dir_name = script_id
    else:
        final_script = "Bienvenue sur ma chaîne ! Ce short est généré automatiquement par l'intelligence artificielle."
        job_dir_name = script_id or "test_job"

    job_dir = os.path.join("media/production", str(job_dir_name))
    os.makedirs(job_dir, exist_ok=True)
    voice_path = os.path.join(job_dir, "voiceover.wav")

    # Generate TTS
    if not os.path.exists(voice_path):
        print(f"Generating TTS for script: {final_script[:50]}...")
        tts_service.generate_tts(final_script, voice_path)
    
    # Scan for video clips generated by step 1
    clips = []
    clips_dir = os.path.join(job_dir, "clips_video")
    if os.path.exists(clips_dir):
        files = [f for f in os.listdir(clips_dir) if f.endswith(".mp4")]
        files.sort()
        for f in files:
            clips.append(f"/{clips_dir}/{f}")
            
    # Include audio if generated
    audio_url = f"/{voice_path}?v={int(time.time())}" if os.path.exists(voice_path) else ""
    
    # NEW: Include Background Music URL if exists
    bgm_path = os.path.join(job_dir, "background_music.mp3")
    bgm_url = f"/{bgm_path}?v={int(time.time())}" if os.path.exists(bgm_path) else ""

    # Calculate exact TTS duration for perfect subtitle sync
    duration_sec = 30.0 # fallback
    if os.path.exists(voice_path):
        import wave
        import contextlib
        try:
            with contextlib.closing(wave.open(voice_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration_sec = frames / float(rate)
        except Exception as e:
            print(f"Could not read wav duration: {e}")
            
    total_frames = int(duration_sec * 30) # 30fps base
    
    # Generate dynamic subtitles based on the script
    words = final_script.split()
    subtitles = []
    frames_per_word = max(3, total_frames // max(1, len(words))) # Exact frame matching

    current_frame = 0
    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunk_len = len(words[i:i+chunk_size])
        duration = chunk_len * frames_per_word
        subtitles.append({
            "text": chunk.upper(),
            "start": current_frame,
            "end": min(total_frames, current_frame + duration)
        })
        current_frame += duration
    
    return {
        "status": "success", 
        "message": "Workflow Assemblage Viral prêt pour Remotion !", 
        "clips": clips, 
        "audioUrl": audio_url,
        "bgmUrl": bgm_url,
        "subtitles": subtitles
    }

# ─────────────────────────────────────────────
# FAL.AI WEBHOOK LISTENER
# ─────────────────────────────────────────────

@app.post("/api/fal/webhook")
async def fal_webhook(request: Request):
    """
    BudgetOptimizer: Optimized listener for Fal.ai asynchronous jobs.
    Saves the generated video to the correct production path once ready.
    """
    data = await request.json()
    request_id = data.get("request_id")
    status = data.get("status")
    
    # Payload from Fal might contain custom metadata if we passed it
    # For now, we use a mapping or filename passed in the callback URL query params
    params = request.query_params
    dest_path = params.get("dest")
    
    if status == "COMPLETED" and dest_path:
        video_url = None
        # Handle different output structures (LTX vs Wan vs MusicGen)
        video_info = data.get("payload", {}).get("video") or data.get("payload", {}).get("audio")
        if video_info and isinstance(video_info, dict):
            video_url = video_info.get("url")
        elif "url" in data.get("payload", {}):
            video_url = data["payload"]["url"]
            
        if video_url:
            print(f"📥 [Webhook] Job {request_id} completed. Downloading to {dest_path}...")
            import requests
            res = requests.get(video_url)
            if res.status_code == 200:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(res.content)
                return {"status": "ok"}
                
    return {"status": "processed"}

class UpdateSystemConfigPayload(BaseModel):
    daily_cap: Optional[float] = None
    auto_stop: Optional[bool] = None
    is_active: Optional[bool] = None
    system_name: Optional[str] = None
    environment: Optional[str] = None
    strict_mode: Optional[bool] = None
    debug_logging: Optional[bool] = None
    access_token: Optional[str] = None
    allowed_ips: Optional[str] = None
    openai_key: Optional[str] = None
    gemini_key: Optional[str] = None
    fal_key: Optional[str] = None
    stability_key: Optional[str] = None
    elevenlabs_key: Optional[str] = None
    auto_cleanup_days: Optional[int] = None
    discord_webhook: Optional[str] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    enable_alerts: Optional[bool] = None
    commando_mode: Optional[bool] = None

@app.get("/api/system/config")
async def get_system_config():
    db = SessionLocal()
    conf = db.query(SystemConfig).first()
    db.close()
    if not conf:
        return {
            "daily_cap": 15.0, "today_spend": 2.45, "auto_stop": True, "is_active": True,
            "system_name": "Mission Control - Primary", "environment": "Production (Live)",
            "strict_mode": True, "debug_logging": False,
            "access_token": "im-dev-token-2026", "allowed_ips": "*",
            "openai_key": "", "gemini_key": "", "fal_key": "", "stability_key": "", "elevenlabs_key": "",
            "auto_cleanup_days": 30,
            "discord_webhook": "", "telegram_token": "", "telegram_chat_id": "", "enable_alerts": True, "commando_mode": False
        }
    return {
        "daily_cap": conf.daily_cap,
        "today_spend": conf.today_spend,
        "auto_stop": conf.auto_stop,
        "is_active": conf.is_active,
        "system_name": conf.system_name,
        "environment": conf.environment,
        "strict_mode": conf.strict_mode,
        "debug_logging": conf.debug_logging,
        "access_token": conf.access_token,
        "allowed_ips": conf.allowed_ips,
        "openai_key": conf.openai_key,
        "gemini_key": conf.gemini_key,
        "fal_key": conf.fal_key,
        "stability_key": conf.stability_key,
        "elevenlabs_key": conf.elevenlabs_key,
        "auto_cleanup_days": conf.auto_cleanup_days,
        "discord_webhook": conf.discord_webhook,
        "telegram_token": conf.telegram_token,
        "telegram_chat_id": conf.telegram_chat_id,
        "enable_alerts": conf.enable_alerts,
        "commando_mode": conf.commando_mode
    }

@app.post("/api/system/config")
async def update_system_config(payload: UpdateSystemConfigPayload):
    db = SessionLocal()
    conf = db.query(SystemConfig).first()
    if not conf:
        conf = SystemConfig()
        db.add(conf)
    
    # Simple mapping for all fields
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conf, key, value)
        
    db.commit()
    db.close()
    return {"status": "success"}

@app.post("/api/system/purge-pipeline")
async def purge_pipeline():
    db = SessionLocal()
    try:
        db.query(ScriptInbox).delete()
        db.query(RunHistory).delete()
        db.commit()
        return {"status": "success", "message": "Pipeline purgé avec succès."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/routes")
async def get_routes():
    db = SessionLocal()
    agents = db.query(AgentConfig).filter(AgentConfig.is_active == True).all()
    db.close()
    
    # Mapping to display strategic tasks based on roles
    task_mapping = {
        "TrendRadar": {"task": "Trend Analysis & Scraping", "reason": "Fast analysis of RSS/Search.", "icon": "⚡"},
        "ViralJudge": {"task": "Content Scoring & Filtering", "reason": "Consistent JSON and analytical reasoning.", "icon": "⚖️"},
        "TechUtilityExpert": {"task": "Technical Utility Analysis", "reason": "Innovation & performance experts.", "icon": "⚙️"},
        "ScriptArchitect": {"task": "Creative Script Generation", "reason": "iM Style storytelling.", "icon": "🧠"},
        "VisualPromptist": {"task": "Visual Planning (FLUX)", "reason": "Photorealistic prompting.", "icon": "🎬"},
        "QualityController": {"task": "Final Validation & DB", "reason": "Data integrity check.", "icon": "✔️"},
    }
    
    routes = []
    for a in agents:
        mapping = task_mapping.get(a.role, {"task": a.name, "reason": "Agent autonomous task.", "icon": "🤖"})
        provider = "Google" if "gemini" in str(a.model).lower() else "OpenAI"
        
        routes.append({
            "task": mapping["task"],
            "model": a.model or "gpt-4o-mini",
            "provider": provider,
            "cost": "$0.0 / 1M" if provider == "Google" else "$0.15 / 1M",
            "reason": mapping["reason"],
            "icon": mapping["icon"]
        })
    return routes

@app.post("/api/workflows/publish")
async def publish_video(payload: dict = None):
    print("Executing Publish & Render Workflow...")
    script_id = payload.get("script_id") if payload else None
    
    if script_id and str(script_id).startswith("db_"):
        db_id = int(script_id.split("_")[1])
        db = SessionLocal()
        script_record = db.query(ScriptInbox).filter(ScriptInbox.id == db_id).first()
        if script_record:
            script_record.status = "posted"
            db.commit()
        db.close()
        
    job_dir_name = script_id or "test_job"
    
    # Trigger FFmpeg generation
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "render_video.py")
    try:
        subprocess.run([sys.executable, script_path, "--job", str(job_dir_name)], check=True)
    except Exception as e:
        print(f"Failed to render video: {e}")
        return {"status": "error", "message": f"Erreur FFmpeg : {e}"}
        
    video_url = f"/media/production/{job_dir_name}/final_output.mp4"
    return {"status": "success", "message": "Vidéo publiée et rendue avec succès ! (Dispo dans Pipeline > Posted)", "videoUrl": video_url}

@app.post("/api/agents/action")
async def agent_action(payload: dict):
    agent_id = payload.get("agent_id")
    action = payload.get("action")
    print(f"Action triggered: {action} on {agent_id}")
    return {"status": "success", "message": f"Action {action} dispatched to {agent_id}"}

# --- HUMAN IN THE LOOP & DB ENDPOINTS ---

class AskHumanPayload(BaseModel):
    agent_name: str
    context: str
    question: str

@app.post("/api/internal/ask-human")
async def internal_ask_human(payload: AskHumanPayload):
    """
    Called internally by an Agent (ViralJudge) to pause and wait for the dashboard user.
    """
    db = SessionLocal()
    question = PendingQuestion(
        agent_name=payload.agent_name,
        context=payload.context,
        question=payload.question
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    db.close()
    
    # In a real async blocking pattern, we would use an asyncio.Event.
    # For this implementation, we will simulate polling the DB until resolved.
    timeout = 3600
    waited = 0
    while waited < timeout:
        await asyncio.sleep(5)
        waited += 5
        db = SessionLocal()
        q = db.query(PendingQuestion).filter(PendingQuestion.id == question.id).first()
        if q and q.is_resolved:
            ans = q.answer
            db.close()
            return {"status": "resolved", "answer": ans}
        db.close()
        
    return {"status": "timeout", "answer": "Humain n'a pas répondu. Continue avec tes meilleures suppositions."}

@app.get("/api/pending-questions")
async def get_pending_questions():
    """ Called by the Frontend React app to verify if an agent is stuck. """
    db = SessionLocal()
    questions = db.query(PendingQuestion).filter(PendingQuestion.is_resolved == False).all()
    db.close()
    return [{"id": q.id, "agent_name": q.agent_name, "context": q.context, "question": q.question} for q in questions]

class AnswerPayload(BaseModel):
    question_id: int
    answer: str

@app.post("/api/answer-question")
async def answer_question(payload: AnswerPayload):
    """ Called by the Frontend React app to provide the answer to the stuck agent. """
    db = SessionLocal()
    question = db.query(PendingQuestion).filter(PendingQuestion.id == payload.question_id).first()
    if not question:
        db.close()
        raise HTTPException(status_code=404, detail="Question not found")
        
    question.answer = payload.answer
    question.is_resolved = True
    db.commit()
    db.close()
    return {"status": "success"}

class FinalizeScriptPayload(BaseModel):
    title: str
    run_type: str
    final_script: str
    viral_score: int
    money_score: int
    keywords: str

@app.post("/api/finalize-script")
async def finalize_script(payload: FinalizeScriptPayload):
    """ Called by QualityController at the end of the pipeline. """
    db = SessionLocal()
    script = ScriptInbox(**payload.dict())
    db.add(script)
    db.commit()
    db.close()
    db.commit()
    db.close()
    return {"status": "success", "message": "Script saved to Inbox"}

@app.post("/api/recs/{rec_id}/apply")
async def apply_recommendation(rec_id: int):
    """
    BudgetOptimizer: Applies a growth recommendation to the system.
    Dynamically updates configurations or agent backstories based on the suggestion.
    """
    db = SessionLocal()
    rec = db.query(GrowthRecommendation).filter(GrowthRecommendation.id == rec_id).first()
    if not rec:
        db.close()
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    conf = db.query(SystemConfig).first()
    
    status_msg = "Recommandation appliquée."
    
    try:
        if rec.type == "scale":
            # Scale usually means increasing budget or frequency
            if conf:
                conf.daily_cap += 5.0
                status_msg = f"Budget quotidien augmenté à ${conf.daily_cap}."
        
        elif rec.type == "pivot":
            # Pivot usually means changing the creative direction
            architect = db.query(AgentConfig).filter(AgentConfig.role == "ScriptArchitect").first()
            if architect:
                if "45s" in rec.description:
                    architect.backstory += " RÈGLE PIVOT : Scripts limités à 45s (env. 100-110 mots) pour maximiser la rétention."
                    status_msg = "Règle de durée (45s) injectée dans l'Architecte."
        
        elif rec.type == "alert":
             # Optimization suggestion
             commander = db.query(AgentConfig).filter(AgentConfig.role == "ViralGrowthCommander").first()
             if commander:
                 commander.backstory += " NOUVEAU HOOK : Utilise des Curiosity Gaps ('J'ai testé X...') au lieu de Listicles."
                 status_msg = "Stratégie de Hook mise à jour."

        db.commit()
        
        # Log the action
        from database import save_agent_message
        save_agent_message("system", "Human", "QualityController", "recommendation_applied", 
                           f"Applied: {rec.title}", {"id": rec_id, "type": rec.type})
                           
        return {"status": "success", "message": status_msg}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# --- Scheduler Setup ---
from pytz import timezone as pytz_timezone

# Force the timezone to Europe/Paris to match the user's local time (+01:00)
# and avoid discrepancies with server local time (AST).
paris_tz = pytz_timezone('Europe/Paris')
scheduler = BackgroundScheduler(timezone=paris_tz)

def scheduled_job():
    now = datetime.now(paris_tz)
    # Determine run type: 8h=matin, 16h=apres-midi, 20h=soir
    if now.hour < 12:
        run_type = "matin"
    elif now.hour < 18:
        run_type = "apres-midi"
    else:
        run_type = "soir"
        
    print(f"⏰ [SCHEDULER] Triggering {run_type} run at {now.strftime('%H:%M:%S')} ({paris_tz})")
    
    # Create Run History record
    run_id = f"cron_{run_type}_{uuid.uuid4().hex[:6]}"
    db = SessionLocal()
    try:
        new_run = RunHistory(
            run_id=run_id,
            name=f"iM System {run_type.capitalize()} (Auto)",
            time=now.strftime("%I:%M %p"),
            schedule=run_type,
            status="running",
            progress_percent=5,
            current_step="Démarrage Automatique",
            cost="0.00",
            duration="--"
        )
        db.add(new_run)
        db.commit()
        print(f"✅ [SCHEDULER] Registered {run_id} in RunHistory")
    except Exception as e:
        print(f"❌ [SCHEDULER] Error creating RunHistory: {e}")
    finally:
        db.close()

    send_telegram_message(f"⏰ <b>iM-System | Mission Programmée</b>\nDémarrage automatique du run de {run_type} ({now.hour}h Paris).")
    
    import threading
    t = threading.Thread(target=run_crew_sync, args=(run_type, run_id))
    t.start()

# Schedule for 08:00, 16:00, and 20:00 (Paris Time)
scheduler.add_job(scheduled_job, 'cron', hour=8, minute=0)
scheduler.add_job(scheduled_job, 'cron', hour=16, minute=0)
scheduler.add_job(scheduled_job, 'cron', hour=20, minute=0)
scheduler.start()
print("🚀 [SCHEDULER] Background scheduler started (Timezone: Europe/Paris) at 08h, 16h, 20h.")
# --- AFFILIATE LINKS API ---

@app.get("/api/affiliates")
async def get_affiliates():
    db = SessionLocal()
    links = db.query(AffiliateLink).filter(AffiliateLink.is_active == True).all()
    db.close()
    return [{
        "id": l.id, "name": l.name, "category": l.category,
        "description": l.description, "cta": l.cta, "link": l.link,
        "gradient": l.gradient, "reconciliation_keywords": l.reconciliation_keywords
    } for l in links]

class AffiliateLinkPayload(BaseModel):
    name: str
    category: str
    description: str
    cta: Optional[str] = "Tester Gratuitement"
    link: str
    gradient: Optional[str] = "from-cyan-400 to-emerald-400"
    reconciliation_keywords: Optional[str] = ""

@app.post("/api/affiliates")
async def create_affiliate(payload: AffiliateLinkPayload):
    db = SessionLocal()
    link = AffiliateLink(**payload.dict())
    db.add(link)
    db.commit()
    db.close()
    return {"status": "success"}

@app.delete("/api/affiliates/{link_id}")
async def delete_affiliate(link_id: int):
    db = SessionLocal()
    link = db.query(AffiliateLink).get(link_id)
    if link:
        db.delete(link)
        db.commit()
    db.close()
    return {"status": "success"}

@app.get("/api/blog/latest")
async def get_latest_blog():
    """Returns blog data for the most recently generated script WITHOUT redirect to avoid CORS issues."""
    db = SessionLocal()
    script = db.query(ScriptInbox).order_by(ScriptInbox.created_at.desc()).first()
    db.close()
    if not script:
        raise HTTPException(status_code=404, detail="No scripts yet")
    
    # Call the actual data getter internally
    return await get_blog_data(script.id)

def _slugify(text):
    """Transforme un titre en slug de fichier propre."""
    if not text:
        return "sans-titre"
    slug = str(text).lower().strip()
    import re
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60]

@app.get("/api/blog/{script_id}")
async def get_blog_data(script_id: int):
    """Returns the data needed for the Public Blog page for a given script."""
    db = SessionLocal()
    script = db.get(ScriptInbox, script_id)
    if not script:
        db.close()
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Match affiliate links based on keywords in the script
    all_links = db.query(AffiliateLink).filter(AffiliateLink.is_active == True).all()
    db.close()
    
    script_text = (script.final_script or "").lower()
    matched_links = []
    for l in all_links:
        keywords = [kw.strip() for kw in (l.reconciliation_keywords or "").split(",")]
        if any(kw and kw in script_text for kw in keywords):
            matched_links.append(l)
    
    # If no matches, return all links (better than an empty page)
    if not matched_links:
        matched_links = all_links[:3]

    video_path = f"/media/production/db_{script.id}/final_output.mp4"
    # Fallback image from the production folder if video is missing
    fallback_img = f"/media/production/db_{script.id}/img_01.jpg"
    base_dir_local = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(base_dir_local, "media", "production", f"db_{script.id}", "img_01.jpg")):
        cover_attr = getattr(script, "cover_image", None)
        fallback_img = cover_attr or "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=1200"
        if fallback_img and fallback_img.startswith("http://localhost:5656"):
            fallback_img = fallback_img.replace("http://localhost:5656", "")

    slug = _slugify(script.title)
    
    # Check if a blog post MD actually exists, if not, try another script
    posts_dir = Path(__file__).parent / "blog" / "posts"
    if not (posts_dir / f"{slug}.md").exists():
        # Optional: could search for another one, but for now we just return the calculated slug
        pass

    return {
        "videoTitle": script.title,
        "videoUrl": video_path, # Use relative path for frontend to handle with API_URL
        "coverImage": fallback_img,
        "slug": slug,
        "summary": script.blog_summary or f"Voici les outils utilisés dans cette vidéo sur {script.title}.",
        "tools": [{
            "name": l.name, "category": l.category,
            "description": l.description, "cta": l.cta,
            "link": l.link, "gradient": l.gradient
        } for l in matched_links]
    }



# ─────────────────────────────────────────────
# BLOG SQUAD API
# ─────────────────────────────────────────────

from blog_squad import BlogSquad

class BlogSquadRunPayload(BaseModel):
    concepts: Optional[list] = None  # If None, fetch Top 5 from DB automatically

def _run_blog_squad_sync(concepts: list):
    """Background runner for BlogSquad."""
    try:
        send_telegram_message("✍️ <b>iM-System | BlogSquad</b>\nLancement de la rédaction de 5 articles SEO...")
        squad = BlogSquad()
        results = squad.run(concepts)
        
        success_list = [r for r in results if r.get("success")]
        
        msg = f"📰 <b>BlogSquad : Rapport de Production</b>\n"
        msg += f"✅ {len(success_list)} articles publiés sur le blog.\n\n"
        
        for r in success_list:
            title = r.get("concept", "Sans titre")
            slug = r.get("slug", "")
            # Assuming frontend is on port 3000 as per start_servers.sh
            msg += f"🔹 <b>{title}</b>\n"
            msg += f"🔗 <i>{slug}.md généré</i>\n\n"
            
        msg += "🌍 <i>Disponible sur ton Dashboard section Blog.</i>"
        send_telegram_message(msg)
        
    except Exception as e:
        send_telegram_message(f"❌ <b>BlogSquad Erreur</b>\n{e}")

@app.post("/api/blog-squad/run")
async def run_blog_squad(payload: BlogSquadRunPayload, background_tasks: BackgroundTasks):
    """
    Déclenche la BlogSquad sur les 5 concepts fournis, ou récupère
    automatiquement les 5 derniers scripts en base si aucun n'est fourni.
    """
    concepts = payload.concepts

    if not concepts:
        db = SessionLocal()
        scripts = db.query(ScriptInbox).order_by(ScriptInbox.created_at.desc()).limit(5).all()
        db.close()
        if not scripts:
            raise HTTPException(status_code=404, detail="Aucun script en base pour alimenter la BlogSquad.")
        concepts = [{"titre": s.title, "killerfeature": s.keywords or s.title} for s in scripts]

    import threading
    t = threading.Thread(target=_run_blog_squad_sync, args=(concepts,))
    t.start()

    return {
        "status": "started",
        "message": f"BlogSquad lancée sur {len(concepts)} concept(s). Tu recevras les résultats sur Telegram.",
        "concepts": [c.get("titre", "?") for c in concepts]
    }

@app.get("/api/blog-squad/posts")
async def list_blog_posts():
    """Liste tous les fichiers .md générés dans /blog/posts/, triés du plus récent au plus ancien."""
    posts_dir = Path(__file__).parent / "blog" / "posts"
    if not posts_dir.exists():
        return []

    # Get all .md files with their mtime
    files = list(posts_dir.glob("*.md"))
    # Sort files by modification time descending (newest first)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    posts = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8").replace("http://localhost:5656", "")
            title_match = re.search(r'^title:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
            date_match = re.search(r'^date:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
            excerpt_match = re.search(r'^excerpt:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
            cover_match = re.search(r'^cover_image:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
            category_match = re.search(r'^category:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
            
            # Tags can be "tag1, tag2" or YAML list
            tags = []
            tags_match = re.search(r'^tags:\s*\[?(.*?)\]?$', content, re.MULTILINE)
            if tags_match:
                tags = [t.strip().replace('"', '') for t in tags_match.group(1).split(",") if t.strip()]

            posts.append({
                "slug": f.stem,
                "filename": f.name,
                "title": title_match.group(1).replace('"', '') if title_match else f.stem,
                "date": date_match.group(1).replace('"', '') if date_match else "",
                "excerpt": excerpt_match.group(1).replace('"', '') if excerpt_match else "",
                "cover_image": cover_match.group(1).replace('"', '') if cover_match else None,
                "category": category_match.group(1).replace('"', '') if category_match else "Général",
                "tags": tags,
                "mtime": f.stat().st_mtime,
                "size_bytes": f.stat().st_size
            })
        except Exception as e:
            print(f"Error reading blog post {f.name}: {e}")
            continue
            
    # Sort by date (YYYY-MM-DD) string, then by mtime
    posts.sort(key=lambda x: (x.get("date") or "0000-00-00", x.get("mtime", 0)), reverse=True)
    
    return posts

@app.get("/api/blog-squad/post/{slug}")
async def get_blog_post_raw(slug: str):
    """Sert le contenu Markdown brut d'un article pour le rendu côté React."""
    posts_dir = Path(__file__).parent / "blog" / "posts"
    file_path = posts_dir / f"{slug}.md"

    try:
        if not file_path.exists():
            # FALLBACK: Try to find a script with this slug to serve a "virtual" markdown
            db = SessionLocal()
            all_scripts = db.query(ScriptInbox).filter(ScriptInbox.title != None).all()
            target_script = None
            for s in all_scripts:
                if _slugify(s.title) == slug:
                    target_script = s
                    break
            
            if target_script:
                print(f"🎬 [VIRTUAL BLOG] Serving virtual MD for slug: {slug}")
                video_url = f"/media/production/db_{target_script.id}/final_output.mp4"
                video_tag = "[INSERT_VIDEO_PLAYER]" if os.path.exists(os.path.join(os.path.dirname(__file__), "media", "production", f"db_{target_script.id}", "final_output.mp4")) else ""
                
                # Use a safer replacement to avoid f-string KeyError if script contains { }
                template = """---
title: "{title}"
excerpt: "{title} — Découverte en avant-première de notre dernière production."
cover_image: "{cover}"
category: "Avant-Première"
date: "{date}"
video_url: "{video}"
---

# {title}

Bienvenue dans cet article généré automatiquement pour accompagner notre dernière vidéo. 

{video_tag}

## Le Script de l'épisode

{script}

[BENTO_TOOLS]

---
*Cet article a été généré par l'iM-System en attendant la revue complète de la BlogSquad.*
"""
                content = template.replace("{title}", str(target_script.title))
                cover_url = getattr(target_script, "cover_image", None) or f"/media/production/db_{target_script.id}/img_01.jpg"
                content = content.replace("{cover}", str(cover_url))
                content = content.replace("{date}", target_script.created_at.strftime('%Y-%m-%d') if target_script.created_at else '')
                content = content.replace("{video}", video_url)
                content = content.replace("{video_tag}", video_tag)
                content = content.replace("{script}", str(target_script.final_script or "Script en cours de rédaction..."))
                db.close()
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse(content=content, media_type="text/plain; charset=utf-8")
            
            db.close()
            raise HTTPException(status_code=404, detail=f"Article '{slug}' introuvable.")

        content = file_path.read_text(encoding="utf-8").replace("http://localhost:5656", "")
        
        # Try to find a matching script to inject video_url if [INSERT_VIDEO_PLAYER] is present
        db = SessionLocal()
        # Simple search by title approximation or look in frontmatter title
        title_match = re.search(r'^title:\s*"?([\s\S]*?)"?\s*$', content, re.M)
        search_title = title_match.group(1).replace('"', '') if title_match else slug.replace('-', ' ')
        
        script = db.query(ScriptInbox).filter(ScriptInbox.title.like(f"%{search_title[:15]}%")).first()
        if script:
            # Inject into frontmatter
            video_url = f"/media/production/db_{script.id}/final_output.mp4"
            if "video_url:" not in content:
                content = content.replace("---\n", f"---\nvideo_url: \"{video_url}\"\n", 1)
            
            # Also ensure cover_image is there if missing
            if "cover_image: \"https" in content or "cover_image: None" in content:
                local_img = f"/media/production/db_{script.id}/img_01.jpg"
                content = re.sub(r'cover_image: ".*?"', f'cover_image: "{local_img}"', content)
                
        db.close()

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"X-Backend-Hardened": "v1.4-getattr-safety"}
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so FastAPI handles them correctly
        raise
    except Exception as e:
        print(f"❌ ERROR serving blog post {slug}: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# --- TELEGRAM WEBHOOK (Validation Workflow) ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Handles callbacks from Telegram Inline Buttons (Approve/Reject).
    Set this URL as your bot webhook: https://your-domain.com/api/telegram/webhook
    """
    try:
        data = await request.json()
        print(f"Telegram Webhook received: {data}")
        
        callback_query = data.get("callback_query")
        if not callback_query:
            return {"status": "ok", "message": "No callback query."}
            
        callback_data = callback_query.get("data", "")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        message_id = callback_query.get("message", {}).get("message_id")
        
        # 1. Parse the action and id
        # Expected: tiktok_approve_123 or tiktok_reject_123
        if "_" not in callback_data:
            return {"status": "ok"}
            
        parts = callback_data.split("_")
        action = parts[1] # "approve" or "reject"
        script_id = int(parts[2])
        
        db = SessionLocal()
        script = db.get(ScriptInbox, script_id)
        
        if not script:
            # Tell Telegram to close the loading spin with an answerCallbackQuery
            requests.post(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/answerCallbackQuery", 
                          json={"callback_query_id": callback_query["id"], "text": "Erreur: Script introuvable."})
            db.close()
            return {"status": "ok"}

        # 2. Handle Action
        response_text = ""
        if action == "approve":
            from tiktok_automation import upload_to_tiktok
            from notifications import send_telegram_message
            
            # Update status to pending upload
            script.status = "publishing"
            db.commit()
            
            # Answer callback immediately to avoid timeout
            requests.post(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/answerCallbackQuery", 
                          json={"callback_query_id": callback_query["id"], "text": "🚀 Lancement de l'upload TikTok..."})

            # Run upload (Blocking call, better in a background task)
            # For now synchronous, but for prod use BackgroundTasks
            upload_result = upload_to_tiktok(script_id)
            response_text = f"✅ <b>TikTok:</b> {upload_result}"
            send_telegram_message(response_text)
            
        elif action == "reject":
            script.status = "rejected"
            db.commit()
            response_text = f"❌ <b>Rejeté:</b> Le script #{script_id} a été mis de côté."
            requests.post(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/answerCallbackQuery", 
                          json={"callback_query_id": callback_query["id"], "text": "Script rejeté."})
            from notifications import send_telegram_message
            send_telegram_message(response_text)

        db.close()
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Telegram Webhook Error: {e}")
        return {"status": "error", "message": str(e)}
# Force reload Thu Mar 12 02:33:39 AM AST 2026
