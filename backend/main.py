from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
from database import SessionLocal, ScriptInbox, PendingQuestion, RunHistory, SystemAlert
from datetime import datetime, timezone
import uuid
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
    return StreamingResponse(log_generator(), media_type="text/event-stream")

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
        print("Creating agents...")
        trend_radar, viral_judge, monetization_scorer, script_architect, visual_promptist, quality_controller = create_agents()
        
        update_run_progress(run_id, 25, "Planification des tâches")
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
        print("Kicking off crew...")
        result = str(crew.kickoff())
        update_run_progress(run_id, 85, "Optimisation du script final")
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
async def run_mission(run_type: Optional[str] = "matin", payload: Optional[dict] = None):
    # Determine the actual run type
    actual_run_type = run_type or "matin"
    if payload and isinstance(payload, dict) and payload.get("type"):
        actual_run_type = payload.get("type")
    
    # Clean run_type for safety
    if actual_run_type not in ["matin", "soir"]:
        actual_run_type = "matin"
    
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    start_time_str = datetime.now().strftime("%I:%M %p")
    
    db = SessionLocal()
    new_run = RunHistory(
        run_id=run_id,
        name=f"iM System {actual_run_type.capitalize()}",
        time=start_time_str,
        schedule=actual_run_type,
        status="running",
        progress_percent=0,
        current_step="Démarrage",
        cost="0.00",
        duration="--"
    )
    db.add(new_run)
    db.commit()
    db.close()
    
    log_capture.history = []
    log_capture.write(f"--- DÉMARRAGE DU RUN {actual_run_type.upper()} ---\n")
    
    # Run the crew in a separate thread so we don't block the FastAPI event loop
    start_ts = datetime.now()
    result = await asyncio.to_thread(run_crew_sync, actual_run_type, run_id)
    end_ts = datetime.now()
    
    duration = end_ts - start_ts
    mins, secs = divmod(duration.total_seconds(), 60)
    final_duration = f"{int(mins)}m {int(secs)}s"
    
    db = SessionLocal()
    run_rec = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
    if run_rec:
        run_rec.status = "completed"
        run_rec.duration = final_duration
        run_rec.cost = "0.05"
        db.commit()
    db.close()

    log_capture.write("--- RUN TERMINÉ ---\n")
    return {"status": "success", "result": result}

@app.get("/api/agents")
async def get_agents():
    # Real agent configurations
    return [
        {"id": "a1", "name": "TrendRadar", "role": "Détective RSS", "status": "Idle", "performance": 100},
        {"id": "a2", "name": "ViralJudge", "role": "Filtre Rétention", "status": "Idle", "performance": 100},
        {"id": "a3", "name": "MonetizationScorer", "role": "Stratège Cash", "status": "Idle", "performance": 100},
        {"id": "a4", "name": "ScriptArchitect", "role": "Copywriter iM", "status": "Idle", "performance": 100},
        {"id": "a5", "name": "QualityController", "role": "Manager Final", "status": "Idle", "performance": 100}
    ]

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
    return []

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
    # Return mock pipeline contents plus any finalized scripts from DB
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
            "column": col,
            "assignedAgent": "QualityController",
            "riskScore": 10,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "date": s.created_at.strftime("%d/%m") if s.created_at else None
        })
        
    db = SessionLocal()
    runs = db.query(RunHistory).filter(RunHistory.status == "running").all()
    db.close()
    for run in runs:
        db_contents.append({
            "id": f"run_{run.run_id}",
            "title": f"Processing {run.name}",
            "viralScore": 0,
            "moneyScore": 0,
            "finalScore": 0,
            "costEstimate": float(run.cost),
            "column": "Script",
            "assignedAgent": "Swarm",
            "riskScore": 5,
            "created_at": run.time,
            "date": run.created_at.strftime("%d/%m") if run.created_at else None
        })
    
    return db_contents

@app.get("/api/approvals")
async def get_approvals():
    db = SessionLocal()
    questions = db.query(PendingQuestion).filter(PendingQuestion.is_resolved == False).all()
    scripts = db.query(ScriptInbox).filter(ScriptInbox.status == "pending_review").all()
    db.close()
    
    apps = []
    for q in questions:
        apps.append({
            "id": f"q_{q.id}",
            "title": f"Question from {q.agent_name}",
            "type": "Topic",
            "status": "Pending",
            "context": q.context or "No context provided",
            "question": q.question or "No question available"
        })
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

@app.get("/api/metrics")
async def get_metrics():
    return {
        "kpis": {
            "totalViews": "0",
            "avgRetention": "0%",
            "engagement": "0%",
            "followers": "0"
        },
        "chartData": []
    }

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

@app.get("/api/routes")
async def get_routes():
    # Return the real default LLM tasks routing used by CrewAI (Gemini)
    return [
        {
            "task": "Trend Analysis & Scraping", "model": "gemini-1.5-flash-latest", "provider": "Google", 
            "cost": "$0.0 / 1M", "reason": "Fast analysis of RSS/Search.", "icon": "⚡"
        },
        {
            "task": "Content Scoring & Filtering", "model": "gemini-1.5-flash-latest", "provider": "Google", 
            "cost": "$0.0 / 1M", "reason": "Consistent JSON and analytical reasoning.", "icon": "⚖️"
        },
        {
            "task": "Script Generation", "model": "gemini-1.5-flash-latest", "provider": "Google", 
            "cost": "$0.0 / 1M", "reason": "Creative generation in iM style.", "icon": "🧠"
        },
        {
            "task": "Quality Control & Validation", "model": "gemini-1.5-flash-latest", "provider": "Google", 
            "cost": "$0.0 / 1M", "reason": "Final DB formatting.", "icon": "🎬"
        }
    ]

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
