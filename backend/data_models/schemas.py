import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LessonContent(BaseModel):
    title: str
    objectives: List[str]
    introduction: str
    activities_urban: List[str]
    activities_rural: List[str]
    resources: List[str]
    quiz: List[str]


class GenerateLessonRequest(BaseModel):
    subject: str
    topic: str
    level: str
    language: str = "English"
    mode: str = "urban"


class LessonSaveRequest(BaseModel):
    lesson_id: Optional[uuid.UUID] = None
    teacher_id: uuid.UUID
    topic: str
    mode: str
    content_json: LessonContent


class FeedbackSaveRequest(BaseModel):
    lesson_id: uuid.UUID
    student_id: Optional[str] = None
    emoji: str
    comment: Optional[str] = None


class TopicCount(BaseModel):
    topic: str
    count: int


class ActivityLogEntry(BaseModel):
    event_type: str
    teacher_id: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    total_lessons: int
    avg_sentiment: float
    active_teachers: int
    lessons_by_topic: List[TopicCount]
    latest_activity: List[ActivityLogEntry]
