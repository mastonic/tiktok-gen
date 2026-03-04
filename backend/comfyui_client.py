import json
import urllib.request
import urllib.parse
import os

def load_env_local():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    val = val.strip('"').strip("'")
                    os.environ[key] = val

# Load keys on module import
load_env_local()

def generate_and_save_flux(prompt_text, save_path):
    """
    Submits prompt to Fal.ai FLUX.1 API and saves the image.
    This replaces the local ComfyUI mock.
    Returns True if successful, False otherwise.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not found in environment.")
        return False
        
    url = "https://fal.run/fal-ai/flux/schnell"
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt_text,
        "image_size": "portrait_16_9",
        "num_inference_steps": 4,
        "num_images": 1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        if "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]
            print(f"Downloading generated image from {image_url}")
            
            # Download the actual image
            img_req = urllib.request.Request(image_url)
            img_resp = urllib.request.urlopen(img_req)
            
            with open(save_path, "wb") as f:
                f.write(img_resp.read())
                
            print(f"Successfully saved image to {save_path}")
            return True
        else:
            print("No images returned from Fal.ai:", result)
            return False
            
    except Exception as e:
        print(f"Failed to generate via Fal.ai: {e}")
        return False
