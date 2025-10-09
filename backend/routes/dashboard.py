# backend/routes/dashboard.py
from fastapi import APIRouter
import sqlite3

router = APIRouter()
DB_PATH = "data/feedback.db"

@router.get("/summary")
def get_dashboard_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT teacher_name, COUNT(*), AVG(rating) FROM feedback GROUP BY teacher_name")
    data = cur.fetchall()
    conn.close()

    summary = [{"teacher": d[0], "lessons": d[1], "avg_rating": round(d[2], 2)} for d in data]
    return {"summary": summary}
