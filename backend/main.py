# backend/main.py
from fastapi import FastAPI
from backend.routes import lesson, feedback, dashboard

app = FastAPI(title="EduBridge AI+", description="AI Copilot for Teachers")

# Include routes
app.include_router(lesson.router, prefix="/lesson", tags=["Lesson"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

@app.get("/")
def home():
    return {"message": "Welcome to EduBridge AI+ Backend!"}
