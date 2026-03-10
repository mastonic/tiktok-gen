import os
import sys
import json
import threading
import re
from pathlib import Path

# Add backend to path to reuse tools
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

try:
    from fal_client import generate_flux_image, generate_video_from_image, download_video, check_fal_balance
    from database import SessionLocal, ScriptInbox, SystemAlert
    from notifications import send_telegram_message
except ImportError:
    # Fallback for direct execution if paths are weird
    print("⚠️ Imports failed, trying relative paths...")
    sys.path.append(os.getcwd())
    from backend.fal_client import generate_flux_image, generate_video_from_image, download_video, check_fal_balance
    from backend.database import SessionLocal, ScriptInbox, SystemAlert
    from backend.notifications import send_telegram_message

def check_balance_alert():
    """
    BudgetOptimizer: Checks fal.ai balance and alerts if under $5.
    """
    balance = check_fal_balance()
    if balance < 5.0:
        db = SessionLocal()
        # Add system alert for the UI
        alert = SystemAlert(
            type="danger",
            message=f"🚨 BUDGET CRITIQUE : Votre solde fal.ai est de ${balance:.2f}. Production ralentie."
        )
        db.add(alert)
        db.commit()
        db.close()
        send_telegram_message(f"🚨 <b>ALERTE BUDGET</b>\nSolde Fal.ai critique : <b>{balance:.2f}$</b>\nLe pipeline risque de s'interrompre.")
        return False
    return True

def smart_loop_workflow(script_id: int):
    """
    Module Smart Loop (TikTok Native 9:16):
    - Module 1 (Génération) : 2 images via Flux Schnell.
    - Module 2 (Animation Sélective) : Image 1 (Hook) via Kling. Image 2 (Loop) via Wan.
    - Module 3 (Assemblage) : Fusionne clips pour rétention 8s.
    """
    print(f"⚙️ Launching Smart Loop Workflow for Script ID {script_id}...")
    
    if not check_balance_alert():
        print("⚠️ Budget critically low. Proceeding with caution.")

    db = SessionLocal()
    script = db.query(ScriptInbox).get(script_id)
    db.close()
    
    if not script:
        print(f"❌ Script {script_id} not found.")
        return

    job_dir = backend_dir / "media" / "production" / f"db_{script.id}"
    job_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = job_dir / "clips_video"
    clips_dir.mkdir(exist_ok=True)

    # 1. Generation Module (Schnell 9:16)
    try:
        # We extract 2 prompts or generate fallback
        image_prompts = json.loads(script.image_prompts) if script.image_prompts else []
    except:
        image_prompts = []

    if not image_prompts:
        image_prompts = [
            f"Dynamic cinematic TikTok hook for {script.title}, high detail, 8k",
            f"Vibrant cinematic background for {script.title} loop, subtle patterns"
        ]

    images = []
    # Force first 2 images
    for i in range(min(2, len(image_prompts))):
        prompt = image_prompts[i]
        img_path = job_dir / f"img_loop_{i+1}.jpg"
        print(f"🎨 Generating Image {i+1}/2 (Flux Schnell)...")
        if generate_flux_image(prompt, str(img_path)):
            images.append(img_path)

    if len(images) < 2:
        print("❌ Could not generate 2 images. Aborting loop.")
        return

    # 2. Selective Animation Module
    # Kling for Hook, Wan for Loop/Ambience
    clips = []
    
    # Clip 1: KLING (premium action/human)
    print("📹 Animating Hook (Kling)...")
    kling_url = generate_video_from_image(str(images[0]), "Hyper-realistic cinematic movement, viral hook action", model="kling")
    if kling_url:
        c1 = clips_dir / "clip_01.mp4"
        if download_video(kling_url, str(c1)):
            clips.append(c1)

    # Clip 2: WAN (ambience/décor)
    print("📹 Animating Background (Wan)...")
    wan_url = generate_video_from_image(str(images[1]), "Cinematic atmospheric background movement, subtle loop", model="wan")
    if wan_url:
        c2 = clips_dir / "clip_02.mp4"
        if download_video(wan_url, str(c2)):
            clips.append(c2)

    if not clips:
        print("❌ No video clips generated.")
        return

    # 3. Assemblage Module
    # We trigger the existing render_video.py which will concat them
    print("🎬 Finalizing Smart Loop assembly...")
    render_script = backend_dir / "render_video.py"
    import subprocess
    subprocess.run([sys.executable, str(render_script), "--job", f"db_{script.id}"])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        smart_loop_workflow(int(sys.argv[1]))
    else:
        print("Usage: python video_gen.py <script_id>")
