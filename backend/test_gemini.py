import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local")
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=api_key)
try:
    print(llm.invoke("Say hi"))
except Exception as e:
    print(f"Error: {e}")
