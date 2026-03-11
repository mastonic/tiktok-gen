import os
import argparse
import subprocess
import json
from pathlib import Path

def generate_video(job_dir: str):
    """
    BudgetOptimizer/StudioManager: Montage 90s sync sur l'audio.
    """
    job_path = Path(job_dir)
    if not job_path.exists():
        print(f"Error: Directory {job_dir} does not exist.")
        return

    # Files
    clips_dir = job_path / "clips_video"
    video_in = job_path / "clips_veo.mp4"
    voice_in = job_path / "voiceover.wav"
    bgm_in = job_path / "background_music.mp3"
    vid_out = job_path / "final_output.mp4"

    # 1. Force Concat clips to ensure they match current production (90s)
    if clips_dir.exists():
        clips = sorted(list(clips_dir.glob("clip_*.mp4")))
        if clips:
            print(f"Normalizing and concatenating {len(clips)} clips into {video_in}...")
            normalized_clips = []
            for i, c in enumerate(clips):
                norm_c = job_path / f"norm_clip_{i:02d}.mp4"
                if not norm_c.exists() or norm_c.stat().st_size == 0:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(c),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                        str(norm_c)
                    ], check=True)
                normalized_clips.append(norm_c)
                
            concat_txt = job_path / "concat.txt"
            with open(concat_txt, "w", encoding="utf-8") as f:
                for c in normalized_clips:
                    f.write(f"file '{c.absolute()}'\n")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(video_in)], check=True)

    if not video_in.exists() or not voice_in.exists():
        print(f"Error: Required video or voiceover missing in {job_dir}.")
        return

    # Extract audio duration to SYNC Duration (Correction 1)
    try:
        audio_dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice_in)]
        audio_duration = float(subprocess.check_output(audio_dur_cmd).decode().strip())
        video_dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_in)]
        video_duration = float(subprocess.check_output(video_dur_cmd).decode().strip())
        
        # Scaling factor: video_pts * (audio_dur / video_dur)
        # This stretches the video to match the audio exactly (Correction 1)
        scaling_factor = audio_duration / video_duration if video_duration > 0 else 1.0
        print(f"Syncing: Audio={audio_duration}s, Video={video_duration}s. Factor={scaling_factor}")
    except Exception as e:
        print(f"Duration probe failed: {e}")
        scaling_factor = 1.0

    # Parse Keywords and Script
    keywords = []
    final_script = ""
    json_file = job_path / "script.json"
    if json_file.exists():
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                keywords = data.get("mots_cles", [])
                final_script = data.get("script", "")
        except: pass

    # Database fallback if needed
    if (not keywords or not final_script) and job_path.name.startswith("db_"):
        try:
            db_id = int(job_path.name.split("_")[1])
            db_path = Path(__file__).parent / "db.sqlite3"
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT final_script, keywords FROM script_inbox WHERE id = ?", (db_id,))
            row = cur.fetchone()
            if row:
                final_script, kw_str = row[0], row[1] or ""
                keywords = [k.strip() for k in kw_str.split(",") if k.strip()]
            conn.close()
        except: pass

    # Clean script for subtitle fallback
    import re
    clean_script = re.sub(r'\[\*\*Visuel\*\*.*?\]', '', final_script, flags=re.IGNORECASE | re.DOTALL)
    clean_script = clean_script.replace('**Narration** :', '').replace('**Narration**', '').replace('"', '').strip()

    # Subtitles: Force stylization (Correction 2)
    ass_file = job_path / "subtitles.ass"
    generate_ass_subtitles(clean_script, keywords, str(ass_file), str(voice_in))

    # Main Rendering FFmpeg
    has_bgm = bgm_in.exists()
    
    # We apply setpts to sync video duration with audio (Correction 1)
    video_filter = f"setpts={scaling_factor}*PTS, drawtext=text='@crewai972':x=W-text_w-20:y=20:fontsize=32:fontcolor=white@0.3, ass={str(ass_file)}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(voice_in)
    ]
    
    if has_bgm:
        cmd.extend(["-i", str(bgm_in)])
        cmd.extend(["-filter_complex", f"[0:v]{video_filter}[v];[2:a]volume=-22dB[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]"])
        cmd.extend(["-map", "[v]", "-map", "[a]"])
    else:
        cmd.extend(["-filter_complex", f"[0:v]{video_filter}[v]"])
        cmd.extend(["-map", "[v]", "-map", "1:a"])

    cmd.extend([
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        str(vid_out)
    ])

    try:
        subprocess.run(cmd, check=True)
        print(f"SUCCESS: {vid_out}")
        
        # --- SEND TO TELEGRAM ---
        from notifications import send_telegram_video_with_validation
        caption = f"🎬 <b>VIDÉO 90s GÉNÉRÉE</b>\nID: {job_path.name}\nSynchro: OK"
        send_telegram_video_with_validation(str(vid_out), int(job_path.name.split("_")[1]) if "db_" in job_path.name else 0, caption=caption)
    except Exception as e:
        print(f"Render Error: {e}")

def format_ass_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    centiseconds = int((seconds - int(seconds)) * 100)
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}.{centiseconds:02d}"

def generate_ass_subtitles(script, keywords, output_path, audio_path):
    """
    SubStation Alpha Stylized (Yellow Bold 70% Pos Pop-Up)
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        with open(audio_path, "rb") as f:
            try:
                transcript = client.audio.transcriptions.create(
                    file=f, model="whisper-large-v3", response_format="verbose_json", timestamp_granularities=["word"]
                )
            except Exception:
                # Fallback to standard whisper if large-v3 endpoint is unavailable on this proxy/client
                f.seek(0)
                transcript = client.audio.transcriptions.create(
                    file=f, model="whisper-1", response_format="verbose_json", timestamp_granularities=["word"]
                )
        words_data = getattr(transcript, 'words', [])
    except Exception as e:
        print(f"Transcription failed: {e}")
        return

    # &H0000FFFF = Yellow (ABGR format), Bold: -1, Outline: 2, Position Y: 1344 (70% of 1920)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,The Bold Font,75,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,0,0,0,1
"""
    events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    
    # Chunk by 1 word for Hormozi style (mot-par-mot)
    for i in range(0, len(words_data)):
        w = words_data[i]
        text = w.word.upper().strip()
        if not text: continue
        
        start_ts = format_ass_time(w.start)
        end_ts = format_ass_time(w.end)
        
        # Pop-up / Bounce Effect: Scale from 100% to 115% back to 100%
        ani = "{\\t(0,50,\\fscx115\\fscy115)\\t(50,150,\\fscx100\\fscy100)}"
        
        # Position at 70% height (1344)
        pos = "{\\pos(540,1344)}"
        
        events += f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{pos}{ani}{text}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n" + events)

def generate_ass_subtitles_linear(script, keywords, output_path, audio_path):
    """
    Fallback linear subtitle generation (less accurate).
    """
    import wave
    import contextlib

    # Get audio duration
    duration = 30.0
    if os.path.exists(audio_path):
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
        except: pass

    words = script.split()
    if not words:
        words = ["FOLLOW", "FOR", "MORE"]
    
    time_per_word = duration / len(words)
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,2,5,10,10,10,1
Style: Highlight,Arial,110,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,2,5,10,10,10,1
"""
    events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    current_time = 0.0
    chunk_size = 2
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i+chunk_size]
        chunk_text = " ".join(chunk).upper()
        chunk_duration = len(chunk) * time_per_word
        start_ts = format_ass_time(current_time)
        end_ts = format_ass_time(current_time + chunk_duration)
        use_highlight = any(kw.lower() in chunk_text.lower() for kw in keywords)
        style = "Highlight" if use_highlight else "Default"
        events += f"Dialogue: 0,{start_ts},{end_ts},{style},,0,0,0,,{{\\pos(540,960)}}{chunk_text}\n"
        current_time += chunk_duration

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n" + events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render final TikTok video using FFmpeg")
    parser.add_argument("--job", type=str, required=True, help="Job ID directory inside media/production")
    args = parser.parse_args()
    
    # Identify absolute path to media dir
    base_dir = Path(__file__).parent
    job_dir = base_dir / "media" / "production" / args.job
    generate_video(str(job_dir))

