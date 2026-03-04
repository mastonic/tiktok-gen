import os
import requests
import time
import base64

FAL_KEY = os.environ.get("FAL_KEY")

from typing import Optional

def generate_video_from_image(image_path: str, prompt: str) -> Optional[str]:
    """
    Submits an image to generative video AI via Fal.ai.
    Uses Kling standard or Luma for stable generation.
    Returns the URL of the generated video/mp4.
    """
    if not FAL_KEY:
        print("WARNING: FAL_KEY not found in environment.")
        # For demonstration if no key, just return a mock URL
        return "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4"

    # We need to upload the image or pass it as data URL
    try:
        with open(image_path, "rb") as f:
            base64_img = base64.b64encode(f.read()).decode('utf-8')
            img_data_url = f"data:image/jpeg;base64,{base64_img}"
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return None

    # Call Fal.ai Kling or general Image-to-Video endpoint.
    url = "https://queue.fal.run/fal-ai/kling-video/v1/standard/image-to-video"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "image_url": img_data_url,
        "prompt": prompt,
        "duration": "5"
    }

    try:
        # Submit task
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"HTTP {response.status_code}: {response.text}")
        response.raise_for_status()
        try:
            print(f"Raw Fal.ai Response: {response.text}")
            res_data = response.json()
            request_id = res_data.get("request_id")
        except Exception as je:
            print(f"JSON decode failed on submit: {je}. Raw response: {response.text}")
            return None
        
        if not request_id:
            return None

        # Poll for completion
        status_url = res_data.get("status_url")
        result_url = res_data.get("response_url")
        
        if not status_url or not result_url:
            print("Missing status_url or response_url in response.")
            return None
        
        for _ in range(60): # wait up to 5 mins
            time.sleep(5)
            status_res = requests.get(status_url, headers=headers)
            try:
                status_data = status_res.json()
            except Exception as e:
                print(f"Failed to decode status response: {status_res.text}")
                return None
                
            if status_data.get("status") == "COMPLETED":
                res = requests.get(result_url, headers=headers)
                try:
                    res_json = res.json()
                    # The Kling API sometimes puts it directly in 'video.url' or returns it flat based on endpoint
                    video_info = res_json.get("video")
                    if video_info and isinstance(video_info, dict):
                         return video_info.get("url")
                    
                    # Alternatively, if Fal returns it differently
                    if "video_url" in res_json:
                         return res_json.get("video_url")
                         
                    print(f"Could not find video URL in successful Fal.ai result: {res_json}")
                    return None
                except Exception as e:
                    print(f"Failed to parse Fal.ai final result JSON: {res.text}")
                    return None
            elif status_data.get("status") in ["FAILED", "CANCELED"]:
                print(f"Fal.ai video generation failed: {status_data}")
                return None
            else:
                print(f"Fal.ai polling status: {status_data.get('status')}")
                
        print("Timeout waiting for Fal.ai video generation.")
        return None
    except Exception as e:
        import traceback
        print(f"Error calling Fal.ai API: {e}\n{traceback.format_exc()}")
        return None

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
