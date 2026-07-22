from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List

from ..data_models import schemas, models
from ..data_models.database import get_db
from ..auth import require_admin

# Renamed router for clarity on the dashboard purpose
router = APIRouter(
    tags=["Analytics & Reporting"]
)

# ----------------------------------------------------
# Backend Engineer Day 4: GET /analytics
# ----------------------------------------------------
@router.get("/analytics", response_model=schemas.AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    _admin: models.Teacher = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Retrieves aggregated analytics data for the teacher dashboard, 
    including total lessons, average sentiment, and lesson distribution.
    """
    
    # 1. Total Lessons Generated
    total_lessons = db.query(models.Lesson).count()
    
    # 2. Average Student Sentiment
    # Calculate the average of all sentiment scores from the Feedback table
    avg_sentiment = db.query(
        func.avg(models.Feedback.sentiment_score)
    ).scalar() or 0.0 # Use 0.0 if there's no feedback yet

    # 3. Active Teachers (simple count of unique teacher_ids in Lesson table)
    active_teachers = db.query(models.Lesson.teacher_id).distinct().count()

    # 4. Lessons by Topic (Group lessons by topic and count them)
    lessons_by_topic_query = db.query(
        models.Lesson.topic, 
        func.count(models.Lesson.id).label("count")
    ).group_by(models.Lesson.topic).order_by(func.count(models.Lesson.id).desc()).limit(5).all()

    lessons_by_topic: List[Dict[str, Any]] = [
        {"topic": topic, "count": count} for topic, count in lessons_by_topic_query
    ]
    
    # 5. Activity Log (Last 5 events) - Simple log retrieval for dashboard feed
    # NOTE: Since no teacher_id is provided, this gets global activity.
    latest_activity_query = db.query(models.ActivityLog).order_by(models.ActivityLog.timestamp.desc()).limit(5).all()
    
    latest_activity = [
        {
            "event_type": log.event_type,
            "teacher_id": str(log.teacher_id),
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.event_metadata
        } for log in latest_activity_query
    ]

    return {
        "total_lessons": total_lessons,
        # Ensure sentiment is rounded to a readable format
        "avg_sentiment": round(avg_sentiment, 2), 
        "active_teachers": active_teachers,
        "lessons_by_topic": lessons_by_topic,
        "latest_activity": latest_activity
    }
