import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("GROQ_API_KEY is missing from .env")
    exit()

headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)

if response.status_code == 200:
    models = sorted([m["id"] for m in response.json().get("data", [])])
    print("\n--- Available Groq Models on Your Key ---")
    for m in models:
        print(f"  - {m}")
else:
    print("Error:", response.status_code, response.text)