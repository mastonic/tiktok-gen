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
    """
    clean_text = clean_script_for_tts(text)
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OpenAI API Key missing for TTS.")
        return False
        
    try:
        print(f"🎙️ [VoiceMaster] Length: {len(clean_text)} chars. Generating via OpenAI TTS-1...")
        
        # OpenAI TTS has a 4096 character limit
        MAX_CHARS = 4000
        chunks = [clean_text[i:i+MAX_CHARS] for i in range(0, len(clean_text), MAX_CHARS)]
        
        audio_segments = []
        for i, chunk in enumerate(chunks):
            print(f"   -> Processing chunk {i+1}/{len(chunks)}...")
            url = "https://api.openai.com/v1/audio/speech"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "tts-1",
                "input": chunk,
                "voice": "onyx", # High quality masculine narrative voice
                "response_format": "mp3"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"❌ OpenAI TTS Error: {response.text}")
                return False
                
            segment_path = f"{output_path}.chunk_{i}.mp3"
            with open(segment_path, "wb") as f:
                f.write(response.content)
            audio_segments.append(segment_path)
            
        if audio_segments:
            if len(audio_segments) > 1:
                import subprocess
                concat_file = f"{output_path}.concat.txt"
                with open(concat_file, "w") as f:
                    for s in audio_segments:
                        f.write(f"file '{os.path.abspath(s)}'\n")
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path], check=True)
                for s in audio_segments: os.remove(s)
                os.remove(concat_file)
            else:
                os.rename(audio_segments[0], output_path)
            
            print(f"✅ VoiceMaster (OpenAI TTS) generated: {output_path}")
            return True
            
    except Exception as e:
        print(f"❌ OpenAI TTS failed: {e}")
        return False

    return False
