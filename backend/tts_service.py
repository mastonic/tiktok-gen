import os
import requests
import asyncio
from typing import Optional

def clean_script_for_tts(text: str) -> str:
    """
    Cleans a script to keep only the spoken narrative.
    Removes: [Visual directions], (Stage directions), **Headers:**, emojis, etc.
    """
    import re
    # 1. Remove everything in brackets [ ... ] (Visual/Sound/Music directions)
    text = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)
    # 2. Remove everything in parentheses ( ... ) (Stage directions)
    text = re.sub(r'\(.*?\)', '', text, flags=re.DOTALL)
    # 3. Remove Markdown headers and labels like **Hook:**, **Narration:**, **Visuel:**
    text = re.sub(r'\*\*.*?\*\*[:\- ]*', '', text, flags=re.IGNORECASE)
    # 4. Remove Speaker labels at the start of lines: "Narrateur:", "Intervenant:", "Narrateur [Voix Off]:"
    text = re.sub(r'^[A-Za-zÀ-ÿ\s]+\[?.*?\]?\s*:\s*', '', text, flags=re.MULTILINE)
    # 5. Remove standalone labels at the start of lines for specific tech keywords
    text = re.sub(r'^(Titre|Sujet|Description|Script|Hook|Mots-clés|Concepts|Visuel|Scene|Scène|Note|Musique|Plan)\s*:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    # 6. Remove quotes and extra formatting characters
    text = text.replace('"', '').replace('*', '').replace('_', '')
    # 7. Clean up whitespace and join lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return ' '.join(lines).strip()

def generate_tts(text: str, output_path: str, mode: str = "openai") -> bool:
    """
    StudioManager: Logic for generating 90s narrative audio using OpenAI TTS-1.
    Handles strategic pauses like [pause_0.5s].
    """
    import re
    import subprocess
    
    clean_text = clean_script_for_tts(text)
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OpenAI API Key missing for TTS.")
        return False
        
    try:
        # 1. Parse pauses [pause_X.Xs]
        # We split the text by pauses and keep the pause tag to know where to insert silence
        parts = re.split(r'(\[pause_\d+\.?\d*s\])', clean_text)
        
        audio_segments = []
        
        for idx, part in enumerate(parts):
            if not part.strip():
                continue
                
            # Check if it's a pause tag
            pause_match = re.match(r'\[pause_(\d+\.?\d*)s\]', part)
            if pause_match:
                duration = float(pause_match.group(1))
                pause_file = f"{output_path}.pause_{idx}.mp3"
                print(f"⌛ [VoiceMaster] Inserting {duration}s pause...")
                # Generate silence using FFmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", 
                    "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame", pause_file
                ], check=True, capture_output=True)
                audio_segments.append(pause_file)
            else:
                # It's actual text
                print(f"🎙️ [VoiceMaster] Generating text segment {idx}...")
                segment_path = f"{output_path}.text_{idx}.mp3"
                
                url = "https://api.openai.com/v1/audio/speech"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "tts-1",
                    "input": part.strip(),
                    "voice": "onyx",
                    "response_format": "mp3"
                }
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    print(f"❌ OpenAI TTS Error: {response.text}")
                    return False
                    
                with open(segment_path, "wb") as f:
                    f.write(response.content)
                audio_segments.append(segment_path)
        
        if audio_segments:
            # Concatenate all segments (text + pauses)
            concat_file = f"{output_path}.concat.txt"
            with open(concat_file, "w") as f:
                for s in audio_segments:
                    f.write(f"file '{os.path.abspath(s)}'\n")
            
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, 
                "-c", "copy", output_path
            ], check=True, capture_output=True)
            
            # Cleanup
            for s in audio_segments: 
                try: os.remove(s)
                except: pass
            try: os.remove(concat_file)
            except: pass
            
            print(f"✅ VoiceMaster (OpenAI TTS + Pauses) generated: {output_path}")
            return True
            
    except Exception as e:
        print(f"❌ OpenAI TTS failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False
