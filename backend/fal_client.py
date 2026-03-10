import os
import requests
import time
import base64

FAL_KEY = os.environ.get("FAL_KEY")

from typing import Optional

def generate_flux_image(prompt: str, save_path: str) -> bool:
    """
    Generates a high-fidelity image using Flux.1 Schnell via Fal.ai.
    Forced for BudgetOptimizer: 0.003$ per image.
    """
    if not FAL_KEY:
        print("WARNING: FAL_KEY not found in environment.")
        return False

    url = "https://queue.fal.run/fal-ai/flux/schnell" 
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "image_size": "portrait_9_16", # FORCED TikTok-Native
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
                res = requests.get(result_url, headers=headers)
                img_url = res.json().get("images")[0].get("url")
                
                # Download and save
                img_res = requests.get(img_url)
                with open(save_path, "wb") as f:
                    f.write(img_res.content)
                return True
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                return False
        return False
    except Exception as e:
        print(f"Flux generation error: {e}")
        return False

def generate_video_from_image(image_path: str, prompt: str, model="kling") -> Optional[str]:
    """
    Submits an image to generative video AI (Kling or Wan) via Fal.ai.
    Forced for BudgetOptimizer: 5 seconds max.
    """
    if not FAL_KEY:
        print("WARNING: FAL_KEY not found in environment.")
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    try:
        with open(image_path, "rb") as f:
            base64_img = base64.b64encode(f.read()).decode('utf-8')
            img_data_url = f"data:image/jpeg;base64,{base64_img}"
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return None

    # Model selection based on BudgetOptimizer
    if model == "wan":
        url = "https://queue.fal.run/fal-ai/wan/v2.1/image-to-video"
    else:
        url = "https://queue.fal.run/fal-ai/kling-video/v1/standard/image-to-video"

    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "image_url": img_data_url,
        "prompt": prompt,
        "duration": "5", # FORCED
        "aspect_ratio": "9:16" # FORCED
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
        print(f"Error calling Fal.ai API: {e}")
        return None

def check_fal_balance() -> float:
    """
    Mock function to check Fal.ai balance.
    Real implementation would use fal-client SDK or specialized endpoint.
    """
    # Since fal.ai doesn't have a public balance API yet, 
    # we return a mock value or read from an internal tracker.
    return 12.50 # Placeholder value

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
