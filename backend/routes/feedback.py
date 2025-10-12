from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..ai import sentiment as sentiment_core # <-- Import your sentiment logic
from ..data_model import schemas, models
from ..data_model.database import get_db

# Assuming you have a Pydantic schema for the feedback request:
# schemas.FeedbackSaveRequest is expected to contain: lesson_id, teacher_id, feedback_items (list of {emoji, comment})

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
    Receives feedback, calculates the sentiment score using local utility,
    and saves the record to the central PostgreSQL database.
    """
    
    # 1. Analyze Feedback to get the aggregated score
    analysis = sentiment_core.analyze_feedback_items(request.feedback_items)
    
    # Extract the average score calculated from the emojis
    avg_score = analysis.get("avg_score") 
    
    if avg_score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback must contain at least one emoji rating."
        )

    # 2. Create the new Feedback ORM object
    db_feedback = models.Feedback(
        lesson_id=request.lesson_id,
        teacher_id=request.teacher_id,
        rating=int(round(avg_score)), # Save the average score rounded to an integer (1-5)
        sentiment_score=avg_score,    # Save the precise average for analytics
        # Optionally, save the full items list in the ActivityLog metadata or a dedicated JSON field
    )

    # 3. Save to Database
    try:
        db.add(db_feedback)
        
        # Log the activity
        db_log = models.ActivityLog(
            teacher_id=request.teacher_id,
            event_type="FEEDBACK_SUBMITTED",
            metadata={"lesson_id": str(request.lesson_id), "rating": avg_score}
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
        "calculated_score": avg_score
    }
