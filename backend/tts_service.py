import os
import requests
import asyncio
from typing import Optional

FAL_KEY = os.environ.get("FAL_KEY")

def generate_tts(text: str, output_path: str, mode: str = "f5-tts") -> bool:
    """
    StudioManager: Logic for generating 90s narrative audio.
    Modes: f5-tts (default fal-ai), parler-tts (local), edge-tts (fallback).
    """
    if mode == "f5-tts" and FAL_KEY:
        try:
            print(f"🎙️ [VoiceMaster] Generating narrative voice via fal-ai/f5-tts...")
            # F5-TTS logic (via fal-ai)
            # Reference: https://fal.ai/models/fal-ai/f5-tts
            url = "https://fal.run/fal-ai/f5-tts"
            headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
            payload = {
                "gen_text": text,
                "speed": 1.1, # TikTok Dynamic Speed
                "remove_silence": True
            }
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
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
            # Required: pip install parler-tts transformers torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
            import torch
            import scipy.io.wavfile as wavfile

            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            model = ParlerTTSForConditionalGeneration.from_pretrained("google/parler-tts-mini-v1").to(device)
            tokenizer = AutoTokenizer.from_pretrained("google/parler-tts-mini-v1")

            description = "A deep masculine voice with a documentary narrative tone, clear and professional."
            input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
            prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

            generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation.cpu().numpy().squeeze()
            wavfile.write(output_path, model.config.sampling_rate, audio_arr)
            print(f"✅ VoiceMaster (Parler-TTS Local) generated: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Parler-TTS Local failed: {e}")

    # Robust Fallback: Edge-TTS
    try:
        import edge_tts
        VOICE = "fr-FR-VivienneMultilingualNeural" 
        async def run_edge_tts():
            communicate = edge_tts.Communicate(text, VOICE, rate="+10%")
            await communicate.save(output_path)
        asyncio.run(run_edge_tts())
        print(f"✅ VoiceMaster (Edge-TTS Fallback) generated: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Edge-TTS failed: {e}")
        return False

