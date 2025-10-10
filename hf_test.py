import os
from dotenv import load_dotenv
import requests

# Load .env file
load_dotenv()

# Get API key
HF_KEY = os.getenv("HF_TOKEN")
if not HF_KEY:
    raise ValueError("❌ HUGGINGFACE_API_KEY not found in .env file")

# Choose a lightweight model for testing
model_id = "google/gemma-3-1b-it"
api_url = f"https://api-inference.huggingface.co/models/{model_id}"

headers = {"Authorization": f"Bearer {HF_KEY}"}

# Define the test prompt
prompt = "Explain the concept of fractions in simple terms for a primary school student."

# Send request
response = requests.post(api_url, headers=headers, json={"inputs": prompt})

# Display output
if response.status_code == 200:
    result = response.json()
    print("✅ Response received:")
    print(result[0]["generated_text"])
else:
    print(f"❌ Request failed ({response.status_code}): {response.text}")
