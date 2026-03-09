import os
import json
import time
from fal_client import generate_flux_image, generate_video_from_image, download_video
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
    script = db.query(ScriptInbox).get(script_id_num)
    db.close()

    if not script:
        print(f"Script {script_id_num} not found in database.")
        return

    job_id = f"db_{script.id}"
    job_dir = f"media/production/db_{script.id}"
    os.makedirs(job_dir, exist_ok=True)
    clips_dir = os.path.join(job_dir, "clips_video")
    os.makedirs(clips_dir, exist_ok=True)

    try:
        image_prompts = json.loads(script.image_prompts) if script.image_prompts else []
    except:
        image_prompts = []

    if not image_prompts:
        print("No image prompts found for this script.")
        return

    send_telegram_message(f"🎨 <b>Production visuelle en cours [{script.title}]</b>\n\nGénération de {len(image_prompts)} images avec Flux.1...")

    # 1. Generate Images with Flux
    images_paths = []
    for i, prompt in enumerate(image_prompts):
        img_path = os.path.join(job_dir, f"img_{i+1:02d}.jpg")
        print(f"Generating image {i+1}/{len(image_prompts)}...")
        if generate_flux_image(prompt, img_path):
            images_paths.append(img_path)
            # Update progress could be sent to frontend if needed
    
    if not images_paths:
        send_telegram_message("❌ Échec de la génération des images Flux.1.")
        return

    # --- NEW: Inject first image into Blog Post ---
    try:
        # 1. First image path relative to root
        first_img_rel = f"/media/production/db_{script.id}/img_01.jpg"
        
        # 2. Find blog post file
        def slugify(text: str) -> str:
            slug = text.lower().strip()
            slug = re.sub(r"[^a-z0-9\s-]", "", slug)
            slug = re.sub(r"\s+", "-", slug)
            return slug[:60]
        
        blog_slug = slugify(script.title)
        blog_file = Path(__file__).parent.parent / "blog" / "posts" / f"{blog_slug}.md"
        
        if blog_file.exists():
            content = blog_file.read_text(encoding="utf-8")
            # Replace placeholder unsplash URL with the local AI image URL
            new_content = re.sub(
                r'cover_image:\s*"https://images\.unsplash\.com/.*?"',
                f'cover_image: "http://localhost:5656{first_img_rel}"',
                content
            )
            blog_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Blog cover updated with AI image: {blog_slug}")
    except Exception as blog_update_e:
        print(f"⚠️ Could not update blog cover: {blog_update_e}")

    send_telegram_message(f"📹 <b>Visuels générés !</b>\nTransformation des images en clips vidéo 5s avec Kling.ai...")

    # 2. Convert Images to Video Clips with Kling
    video_clips_paths = []
    for i, img_path in enumerate(images_paths):
        print(f"Generating video clip {i+1}/{len(images_paths)}...")
        prompt = f"Automated cinematic clip based on script topic: {script.title}"
        vid_url = generate_video_from_image(img_path, prompt)
        if vid_url:
            clip_path = os.path.join(clips_dir, f"clip_{i+1:02d}.mp4")
            if download_video(vid_url, clip_path):
                video_clips_paths.append(clip_path)

    # 3. Generate TTS
    send_telegram_message("🎙️ <b>Génération de la voix-off...</b>")
    voice_path = os.path.join(job_dir, "voiceover.wav")
    generate_tts(script.final_script, voice_path)

    # 4. Render Final Video
    send_telegram_message("🎬 <b>Assemblage final (FFmpeg)...</b>")
    render_script = os.path.join(os.path.dirname(__file__), "render_video.py")
    try:
        # This will call render_video.py and send the video via Telegram at the end
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
                            lines.insert(insert_idx, f'video_url: "http://localhost:5656{video_rel}"')
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
