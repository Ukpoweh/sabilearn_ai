# backend/main.py
from fastapi import FastAPI
from backend.routes import lesson, feedback, dashboard, auth
from backend.data_models.database import init_db

app = FastAPI(title="SabiLearn AI", description="AI Copilot for Nigerian Teachers")


@app.on_event("startup")
def on_startup():
    init_db()


# Include routes (each router already declares its own path prefix)
app.include_router(auth.router)
app.include_router(lesson.generate_router)
app.include_router(lesson.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)


@app.get("/")
def home():
    return {"message": "Welcome to SabiLearn AI Backend!"}
