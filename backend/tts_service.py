import os
import requests
import asyncio

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

def generate_tts(text: str, output_path: str, voice_id: str = "pNInz6obpgDQGcFmaJcg") -> bool:
    """
    Generates TTS audio using ElevenLabs API and saves it to output_path.
    If ELEVENLABS_API_KEY is not set, tries to use edge-tts as high quality fallback.
    """
    if ELEVENLABS_API_KEY:
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"TTS successfully generated to {output_path} via ElevenLabs")
            return True
        except Exception as e:
            print(f"ElevenLabs TTS failed: {e}. Falling back to edge-tts.")

    # High-quality fallback via edge-tts (Microsoft Azure free voices)
    try:
        import edge_tts
        # Default high-quality french voice
        VOICE = "fr-FR-VivienneMultilingualNeural" 
        
        async def run_edge_tts():
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(output_path)
            
        asyncio.run(run_edge_tts())
        print(f"TTS successfully generated to {output_path} via edge-tts (high quality).")
        return True
    except Exception as e:
        print(f"Edge-TTS failed: {e}. Falling back to basic gTTS.")

    # Basic fallback to gTTS (low quality)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='fr')
        tts.save(output_path)
        print(f"TTS successfully generated to {output_path} via gTTS fallback.")
        return True
    except Exception as e:
        print(f"Failed to generate TTS: {e}")
        return False

