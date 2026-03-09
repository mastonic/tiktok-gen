import os
import json
import subprocess
import argparse
import sqlite3
from pathlib import Path
from notifications import send_telegram_message, send_telegram_video

def generate_video(job_dir: str):
    """
    Merges clips_veo.mp4, voiceover.wav, background_music.mp3
    and applies dynamic yellow subtitles for keywords based on script info.
    """
    job_path = Path(job_dir)
    if not job_path.exists():
        print(f"Error: Directory {job_dir} does not exist.")
        return

    # Input files
    json_file = job_path / "script.json"
    clips_dir = job_path / "clips_video"
    video_in = job_path / "clips_veo.mp4"
    voice_in = job_path / "voiceover.wav"
    bgm_in = job_path / "background_music.mp3"
    vid_out = job_path / "final_output.mp4"

    # Concat clips if not already done
    if clips_dir.exists() and not video_in.exists():
        clips = sorted(list(clips_dir.glob("clip_*.mp4")))
        if clips:
            concat_txt = job_path / "concat.txt"
            with open(concat_txt, "w") as f:
                for c in clips:
                    f.write(f"file '{c.absolute()}'\n")
            print(f"Concatenating {len(clips)} clips into {video_in}...")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(video_in)], check=True)

    # Verify essential files
    if not video_in.exists() or not voice_in.exists():
        print(f"Error: Required video or voiceover missing in {job_dir}.")
        return

    # Parse JSON for keywords or fallback to DB
    keywords = []
    final_script = ""
    
    # Try reading from script.json
    if json_file.exists():
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                keywords = data.get("mots_cles", [])
                final_script = data.get("script", "")
        except Exception as e:
            print(f"Failed to read JSON: {e}")

    # Fallback to Database if keywords/script missing
    job_name = job_path.name
    if (not keywords or not final_script) and job_name.startswith("db_"):
        try:
            db_id = int(job_name.split("_")[1])
            db_path = Path(__file__).parent / "db.sqlite3"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT final_script, keywords FROM script_inbox WHERE id = ?", (db_id,))
            row = cur.fetchone()
            if row:
                final_script = row[0]
                kw_str = row[1] or ""
                keywords = [k.strip() for k in kw_str.split(",") if k.strip()]
            conn.close()
        except Exception as e:
            print(f"Database fallback failed: {e}")

    # Force CTA keywords for visual impact
    for cta in ["ABONNE-TOI", "COEUR", "CŒUR", "ABONNE", "SUIS-MOI"]:
        if cta in final_script.upper():
            if cta not in [k.upper() for k in keywords]:
                keywords.append(cta)

    print(f"Keywords for highlight: {keywords}")

    # Build ASS subtitles
    ass_file = job_path / "subtitles.ass"
    generate_ass_subtitles(final_script, keywords, str(ass_file), str(voice_in))

    # Construct the FFmpeg command
    has_bgm = bgm_in.exists()
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(voice_in)
    ]
    
    if has_bgm:
        cmd.extend(["-i", str(bgm_in)])
        # Ducking BGM by 20dB
        cmd.extend(["-filter_complex", "[2:a]volume=0.1[bgm_ducked];[1:a][bgm_ducked]amix=inputs=2:duration=first[aout]"])
        cmd.extend(["-map", "0:v", "-map", "[aout]"])
    else:
        cmd.extend(["-map", "0:v", "-map", "1:a"])

    # Apply subtitles and watermark for growth
    # We add the @crewai972 handle as a discrete watermark in the top right
    watermark = "drawtext=text='@crewai972':x=W-text_w-20:y=20:fontsize=32:fontcolor=white@0.3:shadowcolor=black@0.2:shadowx=1:shadowy=1"
    
    cmd.extend([
        "-vf", f"{watermark}, ass={str(ass_file)}",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "192k",
        str(vid_out)
    ])

    print(f"Running FFmpeg command:\n{' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"SUCCESS: Output saved to: {vid_out}")
        
        # --- SEND TO TELEGRAM WITH VALIDATION ---
        from notifications import send_telegram_video_with_validation
        
        # Attempt to read the generated caption (description + hashtags)
        tiktok_json = job_path / "tiktok_data.json"
        description = ""
        if tiktok_json.exists():
            try:
                with open(tiktok_json, "r") as f:
                    description = json.load(f).get("caption", "")
            except: pass
            
        script_id = 0
        if job_name.startswith("db_"):
            try: script_id = int(job_name.split("_")[1])
            except: pass

        caption = f"🎬 <b>VIDÉO GÉNÉRÉE</b>\n\n📌 <b>DESCRIPTION TIKTOK :</b>\n{description}\n\nID: {job_name}"
        send_telegram_video_with_validation(str(vid_out), script_id, caption=caption)
        
    except Exception as e:
        print(f"FFmpeg or Completion Notification failed: {e}")

def format_ass_time(seconds):
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds - int(seconds)) * 100)
    return f"{hours}:{mins:02d}:{secs:02d}.{centis:02d}"

def generate_ass_subtitles(script, keywords, output_path, audio_path):
    """
    Generates an Advanced SubStation Alpha script with AI-synced word-level highlights.
    Uses OpenAI Whisper API for exact timing.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    if not os.path.exists(audio_path):
        print(f"Error: Audio file {audio_path} not found for transcription.")
        return

    print(f"Transcribing {audio_path} via OpenAI Whisper...")
    try:
        audio_file = open(audio_path, "rb")
        # Get word-level timestamps from Whisper
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        words_data = getattr(transcript, 'words', [])
        if not words_data:
            # Fallback to segments if words are not available
            words_data = getattr(transcript, 'segments', [])
            print("Using segment-level synchronization.")
        else:
            print(f"Successfully retrieved {len(words_data)} words with timestamps.")
    except Exception as e:
        print(f"Whisper transcription failed: {e}. Falling back to linear sync.")
        return generate_ass_subtitles_linear(script, keywords, output_path, audio_path)

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
    
    # We group words into small chunks (1-2 words) for TikTok style "dynamic captions"
    chunk_size = 2
    for i in range(0, len(words_data), chunk_size):
        chunk = words_data[i:i+chunk_size]
        # Handle both word-level and segment-level data
        if hasattr(chunk[0], 'word'): # Word level
            chunk_text = " ".join([w.word.upper() for w in chunk])
            start_time = chunk[0].start
            end_time = chunk[-1].end
        else: # Segment level
            chunk_text = chunk[0].get('text', '').upper().strip()
            start_time = chunk[0].get('start', 0.0)
            end_time = chunk[0].get('end', 1.0)
        
        start_ts = format_ass_time(start_time)
        end_ts = format_ass_time(end_time)
        
        # Check if any word in chunk is a keyword for yellow highlight
        use_highlight = any(kw.lower() in chunk_text.lower() for kw in keywords)
        style = "Highlight" if use_highlight else "Default"
        
        # Centered position for maximum impact
        events += f"Dialogue: 0,{start_ts},{end_ts},{style},,0,0,0,,{{\\pos(540,960)}}{chunk_text}\n"

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

