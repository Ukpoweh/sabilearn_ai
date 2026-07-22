from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid

from ..data_models import schemas, models
from ..data_models.database import get_db
from ..ai import generator
from ..auth import get_current_teacher

router = APIRouter(
    prefix="/lessons",
    tags=["Lesson Management"]
)

# ----------------------------------------------------
# POST /generate_lesson (mounted at root in main.py)
# ----------------------------------------------------
generate_router = APIRouter(tags=["Lesson Generation"])


@generate_router.post("/generate_lesson")
async def generate_lesson_endpoint(
    request: schemas.GenerateLessonRequest,
    current_teacher: models.Teacher = Depends(get_current_teacher),
) -> Dict[str, Any]:
    """
    Generates a contextual lesson plan via Gemini. Does not persist anything —
    the teacher reviews the result and calls POST /lessons to save it.
    """
    result = await generator.generate_lesson(
        subject=request.subject,
        topic=request.topic,
        level=request.level,
        language=request.language,
        mode=request.mode,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Lesson generation failed (Gemini returned no usable content). Please try again.",
        )
    return result


# ----------------------------------------------------
# POST /lessons (Save Lesson)
# ----------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def save_lesson_metadata(
    request: schemas.LessonSaveRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher),
) -> Dict[str, Any]:
    """
    Saves the generated lesson plan content and metadata to the database.
    This is called by the frontend after the teacher reviews and confirms the lesson.
    """
    # Use the UUID from the request if provided (for offline sync idempotency)
    lesson_id = request.lesson_id or uuid.uuid4()

    # 1. Create the Lesson ORM Object
    db_lesson = models.Lesson(
        id=lesson_id,
        teacher_id=current_teacher.id,
        topic=request.topic,
        mode=request.mode,
        content_json=request.content_json.model_dump()
    )

    try:
        # 2. Save to Database
        db.add(db_lesson)
        db.commit()
        db.refresh(db_lesson)
    except Exception as e:
        db.rollback()
        print(f"Database error during lesson save: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save lesson to database."
        )

    # 3. Log activity (Lesson Saved)
    db_log = models.ActivityLog(
        teacher_id=current_teacher.id,
        event_type="LESSON_SAVED",
        event_metadata={"lesson_id": str(db_lesson.id), "topic": request.topic}
    )
    db.add(db_log)
    db.commit()

    return {
        "status": "Lesson saved successfully",
        "lesson_id": str(db_lesson.id),
        "created_at": db_lesson.created_at.isoformat()
    }

# ----------------------------------------------------
# GET /lessons (List Lessons by Teacher)
# ----------------------------------------------------
@router.get("/", response_model=List[Dict[str, Any]])
def list_teacher_lessons(
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher),
) -> List[Dict[str, Any]]:
    """
    Retrieves a list of lesson summaries for the authenticated teacher.
    """
    lessons = db.query(models.Lesson).filter(models.Lesson.teacher_id == current_teacher.id).all()

    if not lessons:
        return []

    # Simple mapping to return list of dicts for the frontend
    return [
        {
            "id": str(lesson.id),
            "topic": lesson.topic,
            "mode": lesson.mode,
            "created_at": lesson.created_at.isoformat(),
            "title": lesson.content_json.get("title", "Untitled Lesson")
        } for lesson in lessons
    ]
