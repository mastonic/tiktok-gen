import os
import requests
import time
import base64
import json
from typing import Optional

def upload_to_fal(file_path: str) -> Optional[str]:
    """
    BudgetOptimizer: Uploads a local file to Fal.ai CDN to be used as I2V reference.
    """
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        return None

    try:
        # 1. Initiate upload
        url = "https://rest.alpha.fal.ai/storage/upload/initiate"
        headers = {
            "Authorization": f"Key {fal_key}",
            "Content-Type": "application/json"
        }
        file_name = os.path.basename(file_path)
        # Simplified content type detection
        content_type = "image/jpeg" if file_name.endswith(".jpg") or file_name.endswith(".jpeg") else "image/png"
        
        payload = {
            "file_name": file_name,
            "content_type": content_type
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        upload_data = response.json()
        
        upload_url = upload_data.get("upload_url")
        file_url = upload_data.get("file_url")
        
        # 2. Upload file content
        with open(file_path, "rb") as f:
            upload_resp = requests.put(upload_url, data=f, headers={"Content-Type": content_type})
            upload_resp.raise_for_status()
            
        return file_url
    except Exception as e:
        print(f"❌ Fal Upload Error: {e}")
        return None

def generate_flux_image(prompt: str, save_path: str, is_square: bool = False) -> bool:
    """
    Generates a high-fidelity image using Flux.1 Schnell via Fal.ai.
    BudgetOptimizer: $0.003/img.
    """
    import os, requests, time
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        print("WARNING: fal_key not found in environment.")
        return False

    url = "https://queue.fal.run/fal-ai/flux/schnell" 
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    # Selection of size based on format
    img_size = "square" if is_square else "portrait_16_9"
    
    payload = {
        "prompt": prompt,
        "image_size": img_size,
        "num_inference_steps": 4,
        "enable_safety_checker": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        res_data = response.json()
        
        # Poll for completion
        status_url = res_data.get("status_url")
        result_url = res_data.get("response_url")
        
        if not status_url or not result_url:
            return False

        for _ in range(20):
            time.sleep(2)
            status_res = requests.get(status_url, headers=headers)
            status_data = status_res.json()
            
            if status_data.get("status") == "COMPLETED":
                # Real-time cost tracking
                try:
                    from database import track_cost
                    track_cost(0.003) # Flux Schnell
                except:
                    pass
                
                # Check if image is directly in status data (common for some Fal versions)
                img_data = status_data.get("images") or []
                if not img_data:
                    # Fetch from result_url
                    res = requests.get(result_url, headers=headers)
                    if res.status_code == 200:
                        img_data = res.json().get("images") or []
                    else:
                        print(f"❌ Fal result_url returned {res.status_code}: {res.text}")
                
                if img_data and len(img_data) > 0:
                    img_url = img_data[0].get("url")
                    if img_url:
                        # Download and save
                        img_res = requests.get(img_url)
                        if img_res.status_code == 200:
                            with open(save_path, "wb") as f:
                                f.write(img_res.content)
                            return True
                
                print(f"⚠️ Fal completed but no image found in response: {status_data}")
                return False
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                print(f"❌ Fal generation {status_data.get('status')}: {status_data.get('error')}")
                return False
        return False
    except Exception as e:
        print(f"Flux generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_wan_video(prompt: str, image_url: Optional[str] = None, is_square: bool = False, webhook_url: Optional[str] = None) -> Optional[str]:
    """
    BudgetOptimizer: Image-to-Video animation with Wan-Video v2.1.
    If image_url is provided, it uses the I2V endpoint.
    """
    import os, requests, time
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        print("WARNING: fal_key not found in environment.")
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    # I2V vs T2V
    if image_url:
        url = "https://queue.fal.run/fal-ai/wan/v2.1/i2v"
        # Force animation prompt as requested
        final_prompt = "The camera zooms in slowly, the subject comes to life and turns their head, cinematic movement, high quality"
    else:
        url = "https://queue.fal.run/fal-ai/wan/v2.1/t2v"
        final_prompt = prompt

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": final_prompt,
        "aspect_ratio": "1:1" if is_square else "9:16",
        "num_frames": 81,
        "resolution": "720p",
        "guidance_scale": 6.0
    }
    
    if image_url:
        payload["image_url"] = image_url
    
    if webhook_url:
        payload["webhook_url"] = webhook_url

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"HTTP {response.status_code}: {response.text}")
        response.raise_for_status()
        res_data = response.json()
        request_id = res_data.get("request_id")
        
        if not request_id:
            return None

        status_url = res_data.get("status_url")
        result_url = res_data.get("response_url")
        
        for _ in range(60): 
            time.sleep(5)
            status_res = requests.get(status_url, headers=headers)
            status_data = status_res.json()
                
            if status_data.get("status") == "COMPLETED":
                # Real-time cost tracking
                try:
                    from database import track_cost
                    track_cost(0.08) # Wan cost
                except:
                    pass
                
                res = requests.get(result_url, headers=headers)
                res_json = res.json()
                video_info = res_json.get("video")
                if video_info and isinstance(video_info, dict):
                         return video_info.get("url")
                
                if "video_url" in res_json:
                         return res_json.get("video_url")
                         
                if "video" in res_json and "url" in res_json["video"]:
                    return res_json["video"]["url"]

                return None
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                return None
                
        return None
    except Exception as e:
        print(f"Error calling Wan API: {e}")
        return None

def generate_ltx_video(prompt: str, image_url: Optional[str] = None, is_square: bool = False, webhook_url: Optional[str] = None) -> Optional[str]:
    """
    BudgetOptimizer: Cost-effective B-Roll animation with LTX-Video.
    If image_url is provided, it leverages Image-to-Video.
    """
    import os, requests, time
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        print("WARNING: fal_key not found in environment.")
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    # I2V vs T2V
    if image_url:
        url = "https://queue.fal.run/fal-ai/ltx-video/image-to-video"
        final_prompt = "Subtle cinematic movement, subject sways gently, highly detailed animation"
    else:
        url = "https://queue.fal.run/fal-ai/ltx-video"
        final_prompt = prompt

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": final_prompt,
        "resolution": "768x768" if is_square else "768x512",
        "num_frames": 65,
        "steps": 25,
        "cfg_scale": 3.0
    }
    
    if image_url:
        payload["image_url"] = image_url
        
    if webhook_url:
        payload["webhook_url"] = webhook_url

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"HTTP {response.status_code}: {response.text}")
        response.raise_for_status()
        res_data = response.json()
        request_id = res_data.get("request_id")
        
        if not request_id:
            return None

        status_url = res_data.get("status_url")
        result_url = res_data.get("response_url")
        
        for _ in range(60): 
            time.sleep(5)
            status_res = requests.get(status_url, headers=headers)
            status_data = status_res.json()
                
            if status_data.get("status") == "COMPLETED":
                # Real-time cost tracking
                try:
                    from database import track_cost
                    track_cost(0.04) # LTX cost approx
                except:
                    pass
                
                res = requests.get(result_url, headers=headers)
                res_json = res.json()
                video_info = res_json.get("video")
                if video_info and isinstance(video_info, dict):
                         return video_info.get("url")
                
                if "video_url" in res_json:
                         return res_json.get("video_url")
                         
                if "video" in res_json and "url" in res_json["video"]:
                    return res_json["video"]["url"]

                return None
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                return None
                
        return None
    except Exception as e:
        print(f"Error calling LTX API: {e}")
        return None

def generate_background_music(prompt: str, save_path: str) -> bool:
    """
    Generates background music using MusicGen via Fal.ai.
    """
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        return False

    url = "https://queue.fal.run/fal-ai/basic-music-gen"
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    # Cyberpunk V9: Dark Phonk style
    full_prompt = f"Phonk, aggressive drift bass, high energy, dark atmospheric background music, 120bpm, HQ: {prompt}"
    
    payload = {
        "prompt": full_prompt,
        "duration": 95 
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        res_data = response.json()
        
        status_url = res_data.get("status_url")
        result_url = res_data.get("response_url")
        
        for _ in range(40):
            time.sleep(3)
            status_res = requests.get(status_url, headers=headers)
            status_data = status_res.json()
            
            if status_data.get("status") == "COMPLETED":
                # Cost tracking
                try:
                    from database import track_cost
                    track_cost(0.04)
                except: pass
                
                audio_url = None
                # Fetch result
                res = requests.get(result_url, headers=headers)
                if res.status_code == 200:
                    audio_res_data = res.json()
                    # MusicGen output structure: {'audio': {'url': '...', ...}}
                    audio_info = audio_res_data.get("audio")
                    if audio_info and isinstance(audio_info, dict):
                        audio_url = audio_info.get("url")
                
                if audio_url:
                    audio_res = requests.get(audio_url)
                    if audio_res.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(audio_res.content)
                        return True
                return False
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                return False
        return False
    except Exception as e:
        print(f"Music generation error: {e}")
        return False

def check_fal_balance() -> float:
    return 12.50 # Placeholder

def download_video(url: str, save_path: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading video from {url}: {e}")
        return False
