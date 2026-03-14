import sys
import os
import json
import sqlite3
import time
import requests
from datetime import datetime
from openai import OpenAI
import fal_client
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

# Add relevant directories to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path: sys.path.insert(0, current_dir)
if parent_dir not in sys.path: sys.path.insert(0, parent_dir)

# Load env
load_dotenv(os.path.join(current_dir, "..", ".env.local"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_PATH = os.path.join(os.path.dirname(__file__), "youtube_leads.db")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def transcribe_audio(audio_path):
    print(f"Transcribing {audio_path}...")
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_script(topic_text):
    print("Generating cynical script with GPT-4o...")
    prompt = f"""
    Create a high-impact 60-second video script based on this transcript: {topic_text}
    The script must be divided into exactly 12 segments of 5 seconds each.
    Style: Cynical, technical, but TRÈS EXPRESSIF and EMOTIONNEL. French language.
    
    IMPORTANT: 
    - Use expressive punctuation (..., !, ?) to create pauses and emphasis in the voice.
    - Write as if you are telling a secret or shouting a revolution.
    - The 12th segment (last 5 seconds) MUST be a strong Call to Action (CTA) like "Abonne-toi pour ne pas mourir bête" or "Commente 'IA' pour le lien".
    
    Respond ONLY with a JSON object containing a key 'segments' which is an array of 12 objects.
    Each object MUST have:
    - 'text': The narration for those 5 seconds (KEEP IT SHORT, max 10-12 words).
    - 'visual_prompt': A detailed prompt for an image generator (FLUX) to illustrate this segment.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a viral content architect."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    content = json.loads(response.choices[0].message.content)
    return content["segments"]

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_image(prompt, index):
    print(f"Generating image {index} with FLUX (fal.ai)...")
    try:
        handler = fal_client.submit(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "image_size": {
                    "width": 1024,
                    "height": 1792
                },
                "num_inference_steps": 4
            }
        )
        result = handler.get()
        return result["images"][0]["url"]
    except Exception as e:
        print(f"❌ Fal.ai Error: {e}")
        raise e

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_audio(text, output_path):
    print(f"Generating High-Quality TTS (nova)...")
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="nova",
        input=text,
        speed=1.05
    )
    response.stream_to_file(output_path)
    return output_path

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def download_file(url, path):
    response = requests.get(url)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    return path

def update_status(video_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, video_id))
    conn.commit()
    conn.close()

def process_video(video_id):
    print(f"--- STARTING WORKER FOR {video_id} ---")
    update_status(video_id, "EN COURS")
    
    audio_path = f"audio_{video_id}.mp3"
    try:
        # 1. Source extraction
        print("Extracting audio from YouTube...")
        os.system(f"yt-dlp -x --audio-format mp3 -o '{audio_path}' https://www.youtube.com/watch?v={video_id}")
        
        transcript = transcribe_audio(audio_path)
        
        # 2. Scripting
        segments = generate_script(transcript)
        
        # 3. Assets Generation & Assembly
        clips = []
        temp_files = [audio_path]
        
        for i, seg in enumerate(segments):
            print(f"Processing segment {i+1}/12...")
            img_url = generate_image(seg["visual_prompt"], i)
            img_path = f"temp_{video_id}_img_{i}.jpg"
            download_file(img_url, img_path)
            
            audio_seg_path = f"temp_{video_id}_audio_{i}.mp3"
            generate_audio(seg["text"], audio_seg_path)
            
            # Create Base Image Clip
            a_clip = AudioFileClip(audio_seg_path)
            i_clip = ImageClip(img_path)
            
            # Add 0.5s of padding to each segment to prevent "cut off" feeling
            duration = a_clip.duration + 0.5
            
            # Handle MoviePy 1.0 vs 2.0 differences
            if hasattr(i_clip, 'with_duration'):
                i_clip = i_clip.with_duration(duration)
            else:
                i_clip = i_clip.set_duration(duration)
            
            # Subtitles (TikTok style)
            try:
                # Use absolute path to ensure pillow/moviepy finds it
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                if not os.path.exists(font_path):
                    font_path = "DejaVu-Sans-Bold" # Fallback
                
                txt_clip = TextClip(
                    text=seg["text"].upper(),
                    font_size=70,
                    color='yellow',
                    font=font_path,
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(800, None)
                )
                
                if hasattr(txt_clip, 'with_duration'):
                    txt_clip = txt_clip.with_duration(duration).with_position(('center', 1400))
                else:
                    txt_clip = txt_clip.set_duration(duration).set_position(('center', 1400))
                
                # Composite
                comp_clip = CompositeVideoClip([i_clip, txt_clip])
            except Exception as te:
                print(f"⚠️ TextClip Error: {te}")
                comp_clip = i_clip
            
            # Add audio
            if hasattr(comp_clip, 'with_audio'):
                comp_clip = comp_clip.with_audio(a_clip) # Audio remains its original length
            else:
                comp_clip = comp_clip.set_audio(a_clip)
                
            clips.append(comp_clip)
            
            temp_files.extend([img_path, audio_seg_path])
        
        # 4. Final Outro (13th Clip)
        print("Adding final Outro (crewai972)...")
        outro_text = "REJOINS L'AVENTURE : CREWAI972 - S'ABONNER"
        outro_prompt = "Futuristic cyberpunk terminal, glowing digital signature 'CREWAI972', high tech aesthetic, cinematic lighting, 8k"
        
        outro_img_url = generate_image(outro_prompt, "outro")
        outro_img_path = f"temp_{video_id}_img_outro.jpg"
        download_file(outro_img_url, outro_img_path)
        
        outro_audio_path = f"temp_{video_id}_audio_outro.mp3"
        generate_audio(outro_text, outro_audio_path)
        
        a_outro = AudioFileClip(outro_audio_path)
        i_outro = ImageClip(outro_img_path)
        
        # Outro duration: audio + 2 seconds of freeze for impact
        outro_duration = a_outro.duration + 2.0
        
        if hasattr(i_outro, 'with_duration'):
            i_outro = i_outro.with_duration(outro_duration)
        else:
            i_outro = i_outro.set_duration(outro_duration)
            
        try:
            txt_outro = TextClip(
                text=outro_text.upper(),
                font_size=80,
                color='white',
                font=font_path,
                stroke_color='red',
                stroke_width=3,
                method='caption',
                size=(900, None)
            )
            if hasattr(txt_outro, 'with_duration'):
                txt_outro = txt_outro.with_duration(outro_duration).with_position('center')
            else:
                txt_outro = txt_outro.set_duration(outro_duration).set_position('center')
            
            comp_outro = CompositeVideoClip([i_outro, txt_outro])
        except:
            comp_outro = i_outro
            
        if hasattr(comp_outro, 'with_audio'):
            comp_outro = comp_outro.with_audio(a_outro)
        else:
            comp_outro = comp_outro.set_audio(a_outro)
            
        clips.append(comp_outro)
        temp_files.extend([outro_img_path, outro_audio_path])

        print("Concatenating clips...")
        # 'chain' is more stable when all clips have the same Resolution
        final_video = concatenate_videoclips(clips, method="chain")
        
        # Ensure output directory exists
        output_dir = os.path.join(current_dir, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        output_name = f"short_{video_id}.mp4"
        output_path = os.path.join(output_dir, output_name)
        
        final_video.write_videofile(output_path, fps=24, codec="libx264")
        
        # Cleanup
        for f in temp_files:
            try: os.remove(f)
            except: pass
            
        update_status(video_id, "TERMINE")
        print(f"SUCCESS: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"ERROR: {e}")
        update_status(video_id, f"ERREUR: {str(e)}")
        return None

if __name__ == "__main__":
    # Test
    # process_video("dQw4w9WgXcQ")
    pass

