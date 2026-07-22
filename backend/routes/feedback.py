from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid

from ..ai import sentiment as sentiment_core
from ..data_models import schemas, models
from ..data_models.database import get_db
from ..auth import get_current_teacher

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback and Sentiment"]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    request: schemas.FeedbackSaveRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Receives a single student's feedback (one emoji tap + optional comment) for
    a lesson, scores it, and saves the record to the database.
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.id == request.lesson_id).first()
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found."
        )

    score = sentiment_core.emoji_to_score(request.emoji)

    db_feedback = models.Feedback(
        lesson_id=request.lesson_id,
        student_id=request.student_id,
        emoji=request.emoji,
        sentiment_score=score,
        comment=request.comment,
    )

    try:
        db.add(db_feedback)

        db_log = models.ActivityLog(
            teacher_id=lesson.teacher_id,
            event_type="FEEDBACK_SUBMITTED",
            event_metadata={"lesson_id": str(request.lesson_id), "score": score}
        )
        db.add(db_log)

        db.commit()
        db.refresh(db_feedback)

    except Exception as e:
        db.rollback()
        print(f"Database error during feedback submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback due to a database error."
        )

    return {
        "message": "Feedback successfully recorded",
        "feedback_id": str(db_feedback.id),
        "score": score
    }


@router.get("/summary")
async def feedback_summary(
    lesson_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=15, le=50),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher),
) -> Dict[str, Any]:
    """
    Pulls the most recent feedback comments (optionally filtered to one lesson)
    and asks Gemini for an AI-powered sentiment/theme summary.
    """
    query = db.query(models.Feedback)
    if lesson_id is not None:
        lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
        if lesson is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found.")
        if current_teacher.role != "admin" and lesson.teacher_id != current_teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this lesson's feedback.",
            )
        query = query.filter(models.Feedback.lesson_id == lesson_id)
    elif current_teacher.role != "admin":
        own_lesson_ids = db.query(models.Lesson.id).filter(models.Lesson.teacher_id == current_teacher.id)
        query = query.filter(models.Feedback.lesson_id.in_(own_lesson_ids))

    rows = query.order_by(models.Feedback.timestamp.desc()).limit(limit).all()

    count = len(rows)
    avg_score = round(sum(r.sentiment_score for r in rows) / count, 2) if count else None

    comments = [r.comment for r in rows if r.comment]
    ai_summary = None
    if comments:
        joined_text = "\n".join(comments)
        text = await sentiment_core.analyze_with_gemini(joined_text)
        ai_summary = sentiment_core.extract_json_from_text(text) if text else None

    return {
        "count": count,
        "avg_score": avg_score,
        "ai_summary": ai_summary
    }
