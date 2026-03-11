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
            
            # Fal.ai F5-TTS has a char limit (approx 1000). We chunk it if needed.
            MAX_CHARS = 800
            chunks = [clean_text[i:i+MAX_CHARS] for i in range(0, len(clean_text), MAX_CHARS)]
            
            audio_segments = []
            
            # Unified reference audio for the "Docu-Style" voice
            REF_AUDIO = "https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/examples/data/paul_graham_essay.wav" # Generic placeholder or your own pro sample
            
            for i, chunk in enumerate(chunks):
                print(f"   -> Processing chunk {i+1}/{len(chunks)}...")
                url = "https://fal.run/fal-ai/f5-tts"
                headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
                payload = {
                    "gen_text": chunk,
                    "ref_audio_url": REF_AUDIO,
                    "model_type": "F5-TTS"
                }
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    print(f"❌ Fal.ai API Error ({response.status_code}): {response.text}")
                    raise Exception(f"Fal.ai error: {response.text}")
                
                data = response.json()
                audio_url = data.get("audio", {}).get("url")
                if audio_url:
                    r = requests.get(audio_url)
                    segment_path = f"{output_path}.chunk_{i}.wav"
                    with open(segment_path, "wb") as f:
                        f.write(r.content)
                    audio_segments.append(segment_path)
            
            if audio_segments:
                # Concatenate segments using ffmpeg if multiple chunks
                if len(audio_segments) > 1:
                    import subprocess
                    concat_file = f"{output_path}.concat.txt"
                    with open(concat_file, "w") as f:
                        for seg in audio_segments:
                            f.write(f"file '{os.path.abspath(seg)}'\n")
                    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path], check=True)
                    # Cleanup
                    for seg in audio_segments: os.remove(seg)
                    os.remove(concat_file)
                else:
                    os.rename(audio_segments[0], output_path)
                
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

