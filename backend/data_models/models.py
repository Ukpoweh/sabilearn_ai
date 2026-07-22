import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def _uuid4():
    return uuid.uuid4()


def _utcnow():
    return datetime.now(timezone.utc)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    school_id = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    role = Column(String, nullable=False, default="teacher")  # "teacher" | "admin"
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True)
    topic = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    content_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    feedback_items = relationship("Feedback", back_populates="lesson")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False, index=True)
    student_id = Column(String, nullable=True)
    emoji = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    lesson = relationship("Lesson", back_populates="feedback_items")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    # Mapped to DB column "metadata" — the Python attribute can't be named
    # `metadata` since that's reserved by SQLAlchemy's declarative Base.
    event_metadata = Column("metadata", JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
