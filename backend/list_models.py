import requests
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
if response.status_code == 200:
    models = response.json().get("models", [])
    for m in models:
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"])
else:
    print(response.text)
