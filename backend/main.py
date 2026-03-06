from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Body, Request
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import sys
import io
import json
import os
import traceback
import re
import wave
import contextlib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from database import SessionLocal, ScriptInbox, PendingQuestion, RunHistory, SystemAlert, AgentConfig, AgentMessage, GrowthRecommendation, SystemConfig
from datetime import datetime, timezone
import uuid

def save_agent_message(content_id, from_agent, to_agent, msg_type, summary, payload={}):
    db = SessionLocal()
    try:
        msg = AgentMessage(
            content_id=content_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=msg_type,
            summary=summary,
            payload=json.dumps(payload)
        )
        db.add(msg)
        db.commit()
    except Exception as e:
        print(f"Error saving agent message: {e}")
    finally:
        db.close()
import comfyui_client
import fal_client
import tts_service

# Ensure environment variables are loaded
comfyui_client.load_env_local()

app = FastAPI(title="iM System API")

# Allow all origins for VPS deployment flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        save_agent_message(run_id, "System", "Swarm", "info", f"Démarrage d'un nouveau cycle Swarm ({run_type})")
        
        db = SessionLocal()
        agent_configs = db.query(AgentConfig).all()
        db.close()
        config_dict = {a.role: a.model for a in agent_configs}
        
        trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller = create_agents(config=config_dict)
        
        update_run_progress(run_id, 25, "Planification des tâches")
        save_agent_message(run_id, "Manager", "System", "info", "Calcul du chemin critique et assignation des tâches terminée.")
        print("Creating tasks...")
        tasks = create_tasks(trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller, run_type)
        
        print("Instantiating crew...")
        crew = Crew(
            agents=[trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        update_run_progress(run_id, 40, "Recherche de tendances & Scoring")
        save_agent_message(run_id, "Swarm", "ViralJudge", "vote", "Analyse comparative des tendances détectées en cours.")
        print("Kicking off crew...")
        result = str(crew.kickoff())
        update_run_progress(run_id, 85, "Optimisation du script final")
        save_agent_message(run_id, "QualityController", "System", "info", "Script généré, revue de qualité par le Swarm effectuée.")
        print(f"Crew execution completed.")
        
        # Parse outcome and save to DB
        try:
            json_str = result
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', result, re.IGNORECASE | re.DOTALL)
            if match:
                json_str = match.group(1)
            
            data = json.loads(json_str)
            db = SessionLocal()
            # Keywords come as a list or a string "A, B, C"
            kw_raw = data.get("mots_cles", [])
            kw_str = kw_raw if isinstance(kw_raw, str) else ", ".join(kw_raw)
            
            # We force status to pending_review so it shows up in Approvals, 
            # even if agent says it's validated, to give human final say.
            final_status = "pending_review" 
            
            new_script = ScriptInbox(
                title=data.get("titre", "Automated Script"),
                run_type=run_type,
                final_script=data.get("script", result),
                viral_score=data.get("score_roi", 85),
                money_score=90,
                keywords=kw_str,
                image_prompts=json.dumps(data.get("image_prompts", [])),
                status=final_status
            )
            db.add(new_script)
            
            # Log this as a system alert
            db.add(SystemAlert(type="info", message=f"Nouveau script généré : {new_script.title}"))
            
            db.commit()
            print("Successfully saved Script to Inbox and created Alert.")
            
            if run_id:
                run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
                if run_rec:
                    run_rec.status = "completed"
                    run_rec.progress_percent = 100
                    run_rec.current_step = "Terminé"
                    run_rec.cost = "0.05"
                    db.commit()
            db.close()
        except Exception as parse_e:
            print(f"Could not parse final output as JSON: {parse_e}")
            db = SessionLocal()
            db.add(ScriptInbox(title=f"Raw Output - {run_type}", run_type=run_type, final_script=result, status="pending_review", viral_score=0, money_score=0))
            db.commit()
            db.close()
            print("Saved raw result fallback to Inbox.")
            if 'db' in locals():
                if run_id:
                    run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
                    if run_rec:
                        run_rec.status = "completed"
                        run_rec.progress_percent = 100
                        run_rec.current_step = "Terminé (Fallback)"
                        run_rec.cost = "0.05"
                        db.commit()
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
                "status": (s.status or "pending").replace("_", " ").title()
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

@app.get("/api/overview")
async def get_overview():
    try:
        db = SessionLocal()
        scripts = db.query(ScriptInbox).all()
        videos = sum(1 for s in scripts if s.status == "posted")
        runs = db.query(RunHistory).all()
        db.close()
        
        total_cost = 0.0
        for r in runs:
            try:
                if r.cost and str(r.cost).replace('.', '', 1).isdigit():
                    total_cost += float(r.cost)
            except:
                continue
                
        profit_score = sum(s.money_score or 0 for s in scripts) / max(len(scripts), 1)

        return {
            "activeAgents": "5/5",
            "videosToday": f"{videos}/{max(videos, 2)}",
            "aiCostToday": f"${total_cost:.2f}",
            "estProfitScore": f"{profit_score:.1f}",
            "budgetRemaining": f"${max(0.0, 15.0 - total_cost):.2f}"
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

@app.get("/api/contents")
async def get_contents():
    try:
        db = SessionLocal()
        scripts = db.query(ScriptInbox).all()
        db.close()
        
        db_contents = []
        for s in scripts:
            col = "Review"
            if s.status == "approved": col = "Scheduled"
            elif s.status == "posted": col = "Posted"
            elif s.status == "pending_review": col = "Review"
            
            try:
                image_prompts = json.loads(s.image_prompts) if s.image_prompts else []
            except:
                image_prompts = []

            # Check for existing assets to persist state in Studio
            job_dir = f"media/production/db_{s.id}"
            has_images = False
            has_videos = False
            has_audio = False
            existing_clips = []
            
            if os.path.exists(job_dir):
                # Images
                imgs = [f for f in os.listdir(job_dir) if f.startswith("img_") and f.endswith((".jpg", ".png"))]
                has_images = len(imgs) > 0
                
                # Videos (clips)
                clips_dir = os.path.join(job_dir, "clips_video")
                if os.path.exists(clips_dir):
                    vids = [f for f in os.listdir(clips_dir) if f.endswith(".mp4")]
                    has_videos = len(vids) > 0
                    existing_clips = [f"/media/production/db_{s.id}/clips_video/{v}" for v in sorted(vids)]
                
                # Audio
                has_audio = os.path.exists(os.path.join(job_dir, "voiceover.wav"))

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
                "existingClips": existing_clips
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
                "riskScore": 5,
                "created_at": run.time,
                "date": run.created_at.strftime("%d/%m") if run.created_at else None
            })
        
        return db_contents
    except Exception as e:
        print(f"Error in get_contents: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})

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
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        # Simplified: group by day of week
        for day in days:
            morning_pts = sum(s.views or 0 for s in posted_scripts if s.run_type == "matin" and s.created_at.strftime("%a") == day)
            evening_pts = sum(s.views or 0 for s in posted_scripts if s.run_type == "soir" and s.created_at.strftime("%a") == day)
            chart_data.append({"name": day, "morning": morning_pts, "evening": evening_pts})

        return {
            "kpis": {
                "totalViews": format_num(total_views),
                "avgRetention": f"{int(avg_retention)}%",
                "engagement": f"{((total_likes / max(total_views, 1)) * 100):.1f}%" if total_views > 0 else "0%",
                "followers": f"+{total_likes // 10}" if total_likes > 0 else "0"
            },
            "chartData": chart_data,
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

@app.post("/api/flux/generate")
def generate_flux_images(request: FluxPromptRequest):
    """
    Sends prompts to local FLUX.1 ComfyUI WebSocket/API.
    Waits for the image to be generated and saves it.
    """
    job_dir = f"media/production/{request.job_id}"
    os.makedirs(job_dir, exist_ok=True)
    
    generated_images = []
    for i, prompt in enumerate(request.prompts):
        filename = f"{job_dir}/img_{i+1:02d}.jpg"
        
        # Real call to ComfyUI (blocking until done or timeout)
        success = comfyui_client.generate_and_save_flux(prompt, filename)
        
        if success:
            generated_images.append(f"/media/production/{request.job_id}/img_{i+1:02d}.jpg")
        else:
            # Fallback mock if ComfyUI is unavailable or errors
            import base64
            # 1x1 black pixel PNG for fallback display
            png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            with open(filename, "wb") as f:
                f.write(base64.b64decode(png_base64))
            generated_images.append(f"/media/production/{request.job_id}/img_{i+1:02d}.jpg")

    return {"status": "success", "images": generated_images, "job_id": request.job_id}

video_generation_progress = {}

def process_image_to_video(job_dir_name, images, job_dir, clips_dir, prompt):
    success_count = 0
    video_generation_progress[job_dir_name] = {"total": len(images), "completed": 0, "status": "running"}
    for img in images:
        img_path = os.path.join(job_dir, img)
        clip_name = f"clip_{img.split('_')[1].split('.')[0]}.mp4"
        clip_path = os.path.join(clips_dir, clip_name)
        
        if os.path.exists(clip_path):
            print(f"Clip {clip_name} already exists. Skipping.")
            success_count += 1
            video_generation_progress[job_dir_name]["completed"] = success_count
            continue

        url = fal_client.generate_video_from_image(img_path, prompt)
        if url:
            if fal_client.download_video(url, clip_path):
                success_count += 1
                print(f"Successfully generated and downloaded {clip_name}")
            else:
                print(f"Failed to download {url}")
        else:
            print(f"Failed to generate video for {img}")
        
        video_generation_progress[job_dir_name]["completed"] = success_count
        
    video_generation_progress[job_dir_name]["status"] = "completed"
    print(f"Workflow Image-to-Video terminé. {success_count}/{len(images)} clips générés !")

@app.post("/api/workflows/image-to-video")
async def run_image_to_video(background_tasks: BackgroundTasks, payload: Optional[dict] = None):
    print("Executing Image-to-Video Master Workflow (Background)...")
    base_dir = "media/production"
    
    if payload and "script_id" in payload:
        # We need to process job directories. For simplicity, we just use the first dir if missing
        script_id = payload["script_id"]
        job_dir_name = script_id # Assumes job_dir is named after script_id. Example: "db_1"
    else:
        # Fallback to first available directory
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

    # Find images
    images = [f for f in os.listdir(job_dir) if f.startswith("img_") and f.endswith((".jpg", ".png"))]
    images.sort()

    if not images:
        return {"status": "error", "message": f"Aucune image trouvée dans {job_dir}"}

    prompt = "Cinematic slow movement, 4k, high resolution, consistent with original image style."
    
    print(f"Found {len(images)} images in {job_dir}. Sending to Fal.ai in background...")
    background_tasks.add_task(process_image_to_video, job_dir_name, images, job_dir, clips_dir, prompt)
    
    return {"status": "success", "message": f"Génération de {len(images)} clips démarrée en arrière-plan..."}

@app.get("/api/workflows/progress/{job_id}")
async def get_video_progress(job_id: str):
    return video_generation_progress.get(job_id, {"status": "not_found"})

@app.post("/api/workflows/assemblage-viral")
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
    audio_url = f"/{voice_path}" if os.path.exists(voice_path) else ""
    
    # Calculate exact TTS duration for perfect subtitle sync
    duration_sec = 30.0 # fallback
    if os.path.exists(voice_path):
        try:
            with contextlib.closing(wave.open(voice_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration_sec = frames / float(rate)
        except Exception as e:
            print(f"Could not read wav duration: {e}")
            
    total_frames = int(duration_sec * 30) # 30fps base
    
    # Generate dynamic subtitles based on the script
    # We will split the script into chunks of 3 words for strong TikTok-style captions.
    words = final_script.split()
    subtitles = []
    frames_per_word = max(3, total_frames // max(1, len(words))) # Exact frame matching

    
    current_frame = 0
    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        duration = len(words[i:i+chunk_size]) * frames_per_word
        subtitles.append({
            "text": chunk,
            "start": current_frame,
            "end": current_frame + duration
        })
        current_frame += duration
    
    return {
        "status": "success", 
        "message": "Workflow Assemblage Viral (Assets TTS chuẩn bị) prêt pour Remotion !", 
        "clips": clips, 
        "audioUrl": audio_url,
        "subtitles": subtitles
    }

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
    enable_alerts: Optional[bool] = None

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
            "discord_webhook": "", "telegram_token": "", "enable_alerts": True
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
        "enable_alerts": conf.enable_alerts
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
        "MonetizationScorer": {"task": "Profit Valuation", "reason": "Business logic & ROI.", "icon": "💰"},
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
    return {"status": "success", "message": "Script saved to Inbox"}
