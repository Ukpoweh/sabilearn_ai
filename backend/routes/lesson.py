from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from sqlalchemy.future import select
import uuid

from ..data_model import schemas, models
from ..data_model.database import get_db

router = APIRouter(
    prefix="/lessons",
    tags=["Lesson Management"]
)

# ----------------------------------------------------
# Backend Engineer Day 3: POST /lessons (Save Lesson)
# ----------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def save_lesson_metadata(
    request: schemas.LessonSaveRequest,
    db: Session = Depends(get_db)
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
        teacher_id=request.teacher_id,
        topic=request.topic,
        mode=request.mode,
        # Pydantic model is automatically converted to JSONB/JSON by SQLAlchemy
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
        teacher_id=request.teacher_id,
        event_type="LESSON_SAVED",
        metadata={"lesson_id": str(db_lesson.id), "topic": request.topic}
    )
    db.add(db_log)
    db.commit()

    return {
        "status": "Lesson saved successfully",
        "lesson_id": str(db_lesson.id),
        "created_at": db_lesson.created_at.isoformat()
    }

# ----------------------------------------------------
# Backend Engineer Day 1: GET /lessons (List Lessons by Teacher)
# ----------------------------------------------------
@router.get("/", response_model=List[Dict[str, Any]])
def list_teacher_lessons(
    teacher_id: uuid.UUID, # Query parameter for filtering
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Retrieves a list of lesson summaries for a given teacher.
    """
    lessons = db.query(models.Lesson).filter(models.Lesson.teacher_id == teacher_id).all()
    
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