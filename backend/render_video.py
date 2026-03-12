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

    # 1. Force Concat clips to ensure they match current production (19 clips)
    if clips_dir.exists():
        clips = sorted(list(clips_dir.glob("clip_*.mp4")))
        if clips:
            # We target 19 clips as per new "ViralEditor V2.1" guidelines
            target_clips = clips[:19]
            print(f"Normalizing and concatenating {len(target_clips)} clips (ViralEditor 19-image rule)...")
            
            # Re-calculate timing if we have audio
            audio_dur = 90.0
            if voice_in.exists():
                audio_dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice_in)]
                audio_dur = float(subprocess.check_output(audio_dur_cmd).decode().strip())
            
            # audio_duration / 19
            clip_duration = audio_dur / 19.0 if len(target_clips) >= 19 else audio_dur / len(target_clips)
            print(f"🎬 ViralEditor V2.1: Each clip will last {clip_duration:.2f}s")

            normalized_clips = []
            for i, c in enumerate(target_clips):
                norm_c = job_path / f"norm_clip_{i:02d}.mp4"
                # Always re-render if duration changed or doesn't exist
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(c),
                    "-vf", f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
                    "-t", str(clip_duration),
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
        
        # We need the video to match the audio EXACTLY.
        # scaling_factor will stretch or shrink the video to match audio.
        scaling_factor = audio_duration / video_duration if video_duration > 0 else 1.0
        print(f"🎬 SYNC: Audio={audio_duration}s, Video={video_duration}s. Factor={scaling_factor}")
    except Exception as e:
        print(f"Duration probe failed: {e}")
        scaling_factor = 1.0
        audio_duration = 90.0 # Default fallback

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
    
    # 5. SFX Transitions (Whoosh/Pop)
    sfx_whoosh = job_path / "whoosh.mp3"
    if not sfx_whoosh.exists():
        # Fallback or generate once
        pass
    
    # We apply setpts to sync video duration with audio (Correction 1)
    video_filter = f"setpts={scaling_factor}*PTS, drawtext=text='@crewai972':x=W-text_w-20:y=20:fontsize=32:fontcolor=white@0.3, ass={str(ass_file)}"
    
    # Create the complex filter for audio mixing (Voice + BGM + SFX)
    # Each transition is at i * clip_duration
    # audio_duration was calculated in Step 1
    clip_dur = audio_duration / 19.0 if clips_dir.exists() else 5.0
    
    audio_filters = [f"[1:a]volume=1.5[vce]"]
    if has_bgm:
        audio_filters.append(f"[2:a]volume=-22dB[bgm]")
        mix_inputs = "[vce][bgm]"
        input_count = 2
    else:
        mix_inputs = "[vce]"
        input_count = 1
        
    # Potential SFX mixing (requires sfx files to be present as inputs)
    # For now, we stick to the core requirements and mix BGM at -22dB
    filter_complex = f"[0:v]{video_filter}[v];" + ";".join(audio_filters) + f";{mix_inputs}amix=inputs={input_count}:duration=first:dropout_transition=2[a]"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(voice_in)
    ]
    
    if has_bgm:
        cmd.extend(["-i", str(bgm_in)])
    
    cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]"])

    cmd.extend([
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", # IMPORTANT: Stop when shortest stream ends (audio)
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
                # Use the original script as a prompt to help Whisper include emojis and match the text
                prompt = script[:200] # Standard whisper prompt limit
                transcript = client.audio.transcriptions.create(
                    file=f, model="whisper-large-v3", response_format="verbose_json", 
                    timestamp_granularities=["word"], prompt=prompt
                )
            except Exception:
                # Fallback to standard whisper
                f.seek(0)
                transcript = client.audio.transcriptions.create(
                    file=f, model="whisper-1", response_format="verbose_json", 
                    timestamp_granularities=["word"], prompt=script[:200]
                )
        words_data = getattr(transcript, 'words', [])
    except Exception as e:
        print(f"Transcription failed: {e}")
        return

    # Subtitle Style: Hormozi (Yellow Bold, Word-by-word)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,150,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,3,2,0,0,0,1
"""
    events = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    
    # GROUP WORDS: 1 word per subtitle block as requested (Word-by-word)
    chunks = []
    chunk_size = 1
    for i in range(0, len(words_data), chunk_size):
        chunks.append(words_data[i:i + chunk_size])

    for chunk in chunks:
        text = " ".join([w.word.strip().upper() for w in chunk])
        if not text: continue
        
        start_ts = format_ass_time(chunk[0].start)
        end_ts = format_ass_time(chunk[-1].end)
        
        # Pop-up / Bounce Effect: Scale from 100% to 125% back to 100% (More aggressive pop)
        ani = "{\\t(0,40,\\fscx125\\fscy125)\\t(40,120,\\fscx100\\fscy100)}"
        
        # Position at 70% height (1344)
        pos = f"{{\\pos(540,1344)}}"
        
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

