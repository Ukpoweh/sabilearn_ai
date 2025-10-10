# backend/routes/feedback.py
from fastapi import APIRouter, Body
import sqlite3
import datetime
import os

router = APIRouter()

# --- Absolute, safe database path setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)  # ✅ ensure 'data' folder exists

DB_PATH = os.path.join(DATA_DIR, "feedback.db")

# --- Initialize the database ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT,
            lesson_topic TEXT,
            feedback_text TEXT,
            rating INTEGER,
            timestamp TEXT
        )
    """)
    conn.close()

init_db()  # ✅ runs once when the module loads


# --- Feedback Submission Endpoint ---
@router.post("/submit")
def submit_feedback(
    teacher_name: str = Body(...),
    lesson_topic: str = Body(...),
    feedback_text: str = Body(""),
    rating: int = Body(...),
):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO feedback (teacher_name, lesson_topic, feedback_text, rating, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (teacher_name, lesson_topic, feedback_text, rating, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"message": "Feedback submitted successfully"}
