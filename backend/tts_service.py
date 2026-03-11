import os
import requests
import asyncio
from typing import Optional

FAL_KEY = os.environ.get("FAL_KEY")

def clean_script_for_tts(text: str) -> str:
    """
    Cleans a script to keep only the spoken narrative.
    Removes: [Visual directions], (Stage directions), **Headers:**, emojis, etc.
    """
    import re
    # 1. Remove everything in brackets [ ... ] (often Visual or Sound directions)
    text = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)
    # 2. Remove everything in parentheses ( ... ) (often secondary directions)
    text = re.sub(r'\(.*?\)', '', text, flags=re.DOTALL)
    # 3. Remove Markdown headers and labels like **Hook:**, **Narration:**, **Visuel:**
    text = re.sub(r'\*\*.*?\*\*[:\- ]*', '', text, flags=re.IGNORECASE)
    # 4. Remove standalone labels at the start of lines
    text = re.sub(r'^(Titre|Sujet|Description|Script|Hook|Mots-clés|Concepts|Visuel|Scene|Scène|Note|Musique|Plan)\s*:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    # 5. Remove quotes and extra formatting characters
    text = text.replace('"', '').replace('*', '').replace('_', '')
    # 6. Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return ' '.join(lines).strip()

def generate_tts(text: str, output_path: str, mode: str = "f5-tts") -> bool:
    """
    StudioManager: Logic for generating 90s narrative audio.
    Modes: f5-tts (default fal-ai), parler-tts (local), edge-tts (fallback).
    """
    clean_text = clean_script_for_tts(text)
    
    # Mirror key for video_gen/comfy compatibility
    fal_key = os.environ.get("FAL_KEY")
    
    if mode == "f5-tts" and fal_key:
        try:
            print(f"🎙️ [VoiceMaster] Length: {len(clean_text)} chars. Generating via fal-ai/f5-tts...")
            # F5-TTS logic (via fal-ai)
            url = "https://fal.run/fal-ai/f5-tts"
            headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
            payload = {
                "gen_text": clean_text
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"❌ Fal.ai API Error ({response.status_code}): {response.text}")
                response.raise_for_status()
        
            # Track cost
            try:
                from database import track_cost
                track_cost(0.035)
            except:
                pass
            
            data = response.json()
            audio_url = data.get("audio", {}).get("url")
            if audio_url:
                r = requests.get(audio_url)
                with open(output_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ VoiceMaster (F5-TTS) generated: {output_path}")
                return True
        except Exception as e:
            print(f"❌ F5-TTS failed: {e}. Falling back...")

    if mode == "parler-tts":
        try:
            print(f"🎙️ [VoiceMaster] Attempting local generation via Parler-TTS...")
            try:
                from parler_tts import ParlerTTSForConditionalGeneration
                from transformers import AutoTokenizer
                import torch
                import scipy.io.wavfile as wavfile
            except ImportError:
                print("⚠️ parler-tts not installed. Falling back to Edge-TTS.")
                return generate_tts(text, output_path, mode="edge-tts")

            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            model = ParlerTTSForConditionalGeneration.from_pretrained("google/parler-tts-mini-v1").to(device)
            tokenizer = AutoTokenizer.from_pretrained("google/parler-tts-mini-v1")

            description = "A deep masculine voice with a documentary narrative tone, clear and professional."
            input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
            prompt_input_ids = tokenizer(clean_text, return_tensors="pt").input_ids.to(device)

            generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation.cpu().numpy().squeeze()
            wavfile.write(output_path, model.config.sampling_rate, audio_arr)
            print(f"✅ VoiceMaster (Parler-TTS Local) generated: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Parler-TTS Local failed: {e}. Falling back to Edge-TTS...")
            return generate_tts(text, output_path, mode="edge-tts")

    # Robust Fallback: Edge-TTS
    try:
        import edge_tts
        VOICE = "fr-FR-VivienneMultilingualNeural" 
        
        async def run_edge_tts():
            communicate = edge_tts.Communicate(clean_text, VOICE, rate="-10%")
            await communicate.save(output_path)
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            import threading
            def _thread_run():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(run_edge_tts())
                new_loop.close()
            t = threading.Thread(target=_thread_run)
            t.start()
            t.join()
        else:
            asyncio.run(run_edge_tts())
        print(f"✅ VoiceMaster (Edge-TTS Fallback) generated: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Edge-TTS failed: {e}")
        return False

