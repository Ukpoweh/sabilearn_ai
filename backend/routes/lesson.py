from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import traceback

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter()

class LessonRequest(BaseModel):
    subject: str
    topic: str
    level: str
    language: str = "English"

# Initialize the Gemini model globally
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print("⚠️ Model initialization failed:", e)
    model = None

@router.post("/generate")
def generate_lesson(req: LessonRequest):
    try:
        if model is None:
            raise RuntimeError("Gemini model not initialized properly.")

        prompt = f"""
        You are EduBridge AI+, an intelligent teaching assistant designed for Nigerian educators.

        Generate a short, structured, and localized lesson plan for the topic "{req.topic}" 
        under the subject "{req.subject}" for {req.level} students.

        The output should be written in {req.language} and should include:
        1. Lesson Title
        2. Learning Objectives
        3. Introduction (linked to students' daily lives in Nigeria)
        4. Main Content (clear, engaging, local examples)
        5. Class Activities
        6. Short Assessment Questions
        7. Teaching Aid Suggestions (simple, locally available materials)
        """

        response = model.generate_content(prompt)

        if not response or not hasattr(response, "text") or not response.text.strip():
            raise ValueError("Gemini returned an empty response or invalid output.")

        return {"lesson_plan": response.text.strip()}

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 Gemini error:", e)
        print(error_trace)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lesson: {str(e)}"
        )
