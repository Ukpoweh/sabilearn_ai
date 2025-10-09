# backend/routes/feedback.py
from fastapi import APIRouter, Body
import sqlite3
import datetime

router = APIRouter()

DB_PATH = "data/feedback.db"

# Create table if not exists
conn = sqlite3.connect(DB_PATH)
conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT,
    lesson_topic TEXT,
    feedback_text TEXT,
    rating INTEGER,
    timestamp TEXT
)""")
conn.close()

@router.post("/submit")
def submit_feedback(
    teacher_name: str = Body(...),
    lesson_topic: str = Body(...),
    feedback_text: str = Body(""),
    rating: int = Body(...),
):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback (teacher_name, lesson_topic, feedback_text, rating, timestamp) VALUES (?, ?, ?, ?, ?)",
        (teacher_name, lesson_topic, feedback_text, rating, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"message": "Feedback submitted successfully"}
