import os
import requests
import time
import base64
from typing import Optional

def generate_flux_image(prompt: str, save_path: str, is_square: bool = False) -> bool:
    """
    Generates a high-fidelity image using Flux.1 Schnell via Fal.ai.
    BudgetOptimizer: $0.003/img.
    """
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

def generate_wan_video(prompt: str, is_square: bool = False) -> Optional[str]:
    """
    Implémentation de la fonction generate_wan_video (Qualité Cinématique 720p).
    """
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        print("WARNING: fal_key not found in environment.")
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    url = "https://queue.fal.run/fal-ai/wan/v2.1/t2v"
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": "1:1" if is_square else "9:16",
        "num_frames": 81,
        "resolution": "720p",
        "guidance_scale": 6.0
    }

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
                    track_cost(0.08) # Wan t2v cost approx
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

def generate_ltx_video(prompt: str, is_square: bool = False) -> Optional[str]:
    """
    Implémentation de la fonction generate_ltx_video (Économique, 768x512, Steps réduits).
    """
    fal_key = (os.environ.get("FAL_KEY") or "").strip()
    if not fal_key:
        print("WARNING: fal_key not found in environment.")
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    url = "https://queue.fal.run/fal-ai/ltx-video"
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "resolution": "768x768" if is_square else "768x512",
        "num_frames": 65,
        "steps": 25,
        "cfg_scale": 3.0
    }

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
