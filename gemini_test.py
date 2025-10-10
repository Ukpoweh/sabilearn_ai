# gemini_test.py
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key from .env in your project root
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

# Configure Gemini
genai.configure(api_key=api_key)

# Pick a model — these exist and work:
model_name = "models/gemini-2.5-flash"   # or "models/gemini-2.5-pro"

model = genai.GenerativeModel(model_name)

# Generate a test response
prompt = """
Create a JSON lesson plan about "Photosynthesis" for primary school students in Nigeria.
Include title, objectives, introduction, activities_urban, activities_rural, resources, and quiz.
"""

response = model.generate_content(prompt)

print("\n--- RAW RESPONSE ---\n")
print(response.text)
