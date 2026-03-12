import os
import json
import time
from video_gen import generate_flux_image, generate_wan_video, generate_ltx_video, download_video, upload_to_fal
from tts_service import generate_tts
from notifications import send_telegram_message, send_telegram_video
from database import SessionLocal, ScriptInbox
import subprocess
import sys
import re
from pathlib import Path

def automate_visual_production(script_id_num: int):
    """
    Takes a script from the database and runs the full production pipeline:
    Images (Flux) -> Video Clips (Kling) -> TTS -> Video Render -> Telegram
    """
    db = SessionLocal()
    script = db.get(ScriptInbox, script_id_num)
    db.close()

    if not script:
        print(f"Script {script_id_num} not found in database.")
        return

    # --- BUDGET OPTIMIZER: CHECK CREDITS ---
    from video_gen import check_fal_balance
    balance = check_fal_balance()
    if balance < 5.0:
         send_telegram_message(f"⚠️ <b>BUDGET CRITIQUE : {balance:.2f}$</b>\nLe pipeline continue à vos risques et périls.")
         db = SessionLocal()
         from database import SystemAlert
         db.add(SystemAlert(type="danger", message=f"Solde Fal.ai critique: {balance:.2f}$"))
         db.commit()
         db.close()

    job_id = f"db_{script.id}"
    job_dir = f"media/production/db_{script.id}"
    os.makedirs(job_dir, exist_ok=True)
    clips_dir = os.path.join(job_dir, "clips_video")
    
    # NEW: Cleanup old clips to ensure fresh order and no residue from failed runs
    if os.path.exists(clips_dir):
        import shutil
        shutil.rmtree(clips_dir)
    os.makedirs(clips_dir, exist_ok=True)

    try:
        image_prompts = json.loads(script.image_prompts) if script.image_prompts else []
    except:
        image_prompts = []
    
    # Production mode: 15 frames (Cyberpunk 2026 Standard)
    prompt_count = 15

    # --- FALLBACK: Generate prompts if they are missing ---
    if not image_prompts or len(image_prompts) < 1:
        print(f"⚠️ No image prompts found for script {script.id}. Generating fallbacks...")
        try:
            from agents import create_agents
            from crewai import Task
            agents = create_agents()
            # VisualPromptist is usually the 5th agent in the standard list
            visual_promptist = agents[4] 
            
            prompt_task = Task(
                description=f"Le script suivant est pour un format LONG de 90s. Crée exactement {prompt_count} prompts cinématiques en ANGLAIS pour FLUX qui illustrent ce script : {script.final_script[:3000]}",
                expected_output=f"Exactly {prompt_count} cinematic prompts in a list format.",
                agent=visual_promptist
            )
            result = str(visual_promptist.execute_task(prompt_task))
            # Extract prompts (More robust: look for lines starting with numbers or just strings in quotes)
            fallback_prompts = re.findall(r'"([^"]{30,})"', result) # Quoted strings > 30 chars
            if not fallback_prompts:
                 # Try splitting by lines and filtering
                 lines = [p.strip().lstrip('0123456789.- ') for p in result.split('\n')]
                 fallback_prompts = [p for p in lines if len(p) > 30]
            
            # Ensure we have enough or take what we have, up to prompt_count
            image_prompts = fallback_prompts[:prompt_count]
            
            if image_prompts:
                print(f"✅ Generated {len(image_prompts)} fallback image prompts. Updating DB for Studio visibility...")
                
                # Update script record in DB (Correction: persistence for Studio visibility)
                db = SessionLocal()
                s = db.query(ScriptInbox).filter(ScriptInbox.id == script_id_num).first()
                if s:
                    s.image_prompts = json.dumps(image_prompts)
                    db.commit()
                db.close()
        except Exception as gen_e:
            print(f"❌ Failed to generate fallback prompts: {gen_e}")

    if not image_prompts:
        print("No image prompts found and fallback generation failed.")
        return

    # 1. Generate Images with Flux (BudgetOptimizer: Schnell)
    images_paths = {} # Use dict to maintain strict index mapping
    
    send_telegram_message(f"🎨 <b>Production visuelle en cours [{script.title}]</b>\n\nFormat : Long (90s minimum)\nPhase 1: Génération des {prompt_count} visuels (Flux Schnell)\nFormat: 9:16 portrait")
    
    for i, prompt in enumerate(image_prompts[:prompt_count]):
        img_path = os.path.join(job_dir, f"img_{i+1:02d}.jpg")
        print(f"Generating image {i+1}/{prompt_count}...")
        if generate_flux_image(prompt, img_path):
            images_paths[i] = img_path

    # ... (Blog cover update logic) ...

    # 2. Generative Video Clips (STRICT Image-to-Video Animation)
    video_clips_paths = []
    # BLOCKING RULE: Do not proceed if no images were generated
    if not images_paths:
        print("❌ CRITICAL: No images available under preview. Blocking video generation.")
        send_telegram_message("❌ <b>ERREUR CRITICAL :</b> Aucune image générée. Production vidéo stoppée (Règle I2V Stricte).")
        return

    # We iterate over the FULL intended count to ensure no gaps or shifts
    for i in range(len(image_prompts[:prompt_count])):
        print(f"Processing clip {i+1}...")
        clip_path = os.path.join(clips_dir, f"clip_{i+1:02d}.mp4")
        
        # Try to animate if the image was successfully generated
        vid_generated = False
        if i in images_paths:
            img_local_path = images_paths[i]
            print(f"Uploading image {i+1} to Fal for I2V...")
            img_url = upload_to_fal(img_local_path)
            
            if img_url:
                # Animation Logic (Wan for hook, LTX for the rest)
                if i == 0:
                    vid_url = generate_wan_video(prompt="", image_url=img_url)
                else:
                    vid_url = generate_ltx_video(prompt="", image_url=img_url)
                    
                if vid_url and download_video(vid_url, clip_path):
                    vid_generated = True
            else:
                 print(f"❌ Failed to upload image {i+1} to Fal.")
        
        # FAILOVER: If video generation failed or image was missing, 
        # create a 5s static clip from the image or a placeholder
        if not vid_generated:
            print(f"⚠️ Failover: Creating static clip for index {i+1}")
            img_to_use = images_paths.get(i)
            if img_to_use and os.path.exists(img_to_use):
                # FFmpeg to convert image to 5s video (WITH pillarbox/letterbox to avoid cut)
                subprocess.run([
                    "ffmpeg", "-y", "-loop", "1", "-i", img_to_use, 
                    "-t", "5", "-pix_fmt", "yuv420p", 
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
                    clip_path
                ], check=True)
            else:
                # Total fallback: black screen
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=5", 
                    "-pix_fmt", "yuv420p", clip_path
                ], check=True)
        
        video_clips_paths.append(clip_path)

    # 3. Generate TTS
    send_telegram_message("🎙️ <b>Génération de la voix-off...</b>")
    voice_path = os.path.join(job_dir, "voiceover.wav")
    generate_tts(script.final_script, voice_path)

    # 4. Generate AI Background Music (New)
    from video_gen import generate_background_music
    send_telegram_message("🎵 <b>Création d'une musique d'ambiance sur-mesure (IA)...</b>")
    bgm_path = os.path.join(job_dir, "background_music.mp3")
    generate_background_music(script.title, bgm_path)

    # 5. Generate TikTok Caption (New)
    try:
        from agents import create_agents
        from crewai import Task
        _, _, _, _, _, _, tiktok_distributor = create_agents()
        
        caption_task = Task(
            description=f"Crée une description TikTok virale pour ce script : {script.final_script}. Ajoute 5 hashtags pertinents.",
            expected_output="La description TikTok avec hashtags.",
            agent=tiktok_distributor
        )
        tiktok_caption = str(tiktok_distributor.execute_task(caption_task))
        
        # Save caption to a local json for render_video.py
        with open(os.path.join(job_dir, "tiktok_data.json"), "w") as f:
            json.dump({"caption": tiktok_caption}, f)
    except Exception as e:
        print(f"Failed to generate TikTok caption: {e}")

    # 5. Render Final Video
    send_telegram_message("🎬 <b>Assemblage final (FFmpeg)...</b>")
    render_script = os.path.join(os.path.dirname(__file__), "render_video.py")
    try:
        # This will call render_video.py and send the video via Telegram with buttons
        subprocess.run([sys.executable, render_script, "--job", job_id], check=True)
        
        # Finally mark as approved if everything went well
        db = SessionLocal()
        s = db.query(ScriptInbox).get(script_id_num)
        if s:
            s.status = "approved"
            db.commit()

            # --- NEW: Inject video URL into Blog Post ---
            try:
                def slugify(text: str) -> str:
                    slug = text.lower().strip()
                    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
                    slug = re.sub(r"\s+", "-", slug)
                    return slug[:60]
                
                blog_slug = slugify(s.title)
                blog_file = Path(__file__).parent.parent / "blog" / "posts" / f"{blog_slug}.md"
                video_rel = f"/media/production/db_{s.id}/final_output.mp4"
                
                if blog_file.exists():
                    current_content = blog_file.read_text(encoding="utf-8")
                    if 'video_url:' not in current_content:
                        # Insert before the last --- of frontmatter
                        lines = current_content.splitlines()
                        frontmatter_indices = [i for i, line in enumerate(lines) if line.strip() == '---']
                        if len(frontmatter_indices) >= 2:
                            insert_idx = frontmatter_indices[1]
                            lines.insert(insert_idx, f'video_url: "{video_rel}"')
                            blog_file.write_text("\n".join(lines), encoding="utf-8")
                            print(f"✅ Video URL injected into blog: {blog_slug}")
            except Exception as vid_inject_e:
                print(f"⚠️ Could not inject video URL: {vid_inject_e}")
        db.close()
        
    except Exception as e:
        send_telegram_message(f"❌ Erreur lors du rendu final : {e}")
        print(f"Render failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
         automate_visual_production(int(sys.argv[1]))
