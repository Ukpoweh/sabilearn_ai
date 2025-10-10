from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.ai.generator import generate_lesson
import traceback

router = APIRouter()

class LessonRequest(BaseModel):
    teacher_id: str = None
    subject: str
    topic: str
    level: str
    mode: str = "urban"
    language: str = "English"

@router.post("/generate_lesson")
def generate(req: LessonRequest):
    try:
        lesson = generate_lesson(req.subject, req.topic, req.level, req.language, req.mode)
        return {"success": True, "lesson": lesson}
    except Exception as e:
        tb = traceback.format_exc()
        print("Generation error:", e)
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))
