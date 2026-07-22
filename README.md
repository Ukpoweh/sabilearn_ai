# SabiLearn AI

> **AI Copilot for Nigerian Teachers** — designed to automate lesson plan generation, analyze classroom feedback, and integrate real-time data pipelines for continuous educational improvement.

See `SabiLearn AI (2).docx` in this repo for the full product/architecture write-up (problem statement, data model, roadmap). This README covers the working MVP.

---

## 🧠 Overview

SabiLearn AI is an intelligent education assistant built to support Nigerian teachers by:
- Generating **context-aware lesson plans** tailored to both **urban** and **rural** classrooms.
- Analyzing **student feedback** to understand sentiment, key learning themes, and engagement levels.
- Integrating with **Airflow** for automated data ingestion from external sources (curriculum datasets, performance metrics) — a separate pipeline maintained by the Data Engineering track under `backend/airflow_mongoDB_postgres/`.

This backend leverages:
- **FastAPI** — for clean, modern API endpoints.
- **Google Gemini 2.5 Flash** — for AI-driven text generation and feedback analysis.
- **PostgreSQL** — for lesson, feedback, and activity-log storage.
- **Streamlit** — for the teacher/student/dashboard frontend.
- **Apache Airflow** — for ingestion and preprocessing pipelines (managed by the Data Engineering team, separate from the app above).

---

## 🧩 Architecture

```
├── backend/
│   ├── ai/
│   │   ├── generator.py            # Gemini-based lesson plan generator
│   │   ├── sentiment.py            # Gemini-based feedback analysis module
│   │   ├── prompts/
│   │   │   ├── system_prompt.txt
│   │   │   └── user_prompt.txt
│   ├── data_models/
│   │   ├── database.py             # SQLAlchemy engine/session, get_db(), init_db()
│   │   ├── models.py                # Lesson, Feedback, ActivityLog ORM models
│   │   └── schemas.py               # Pydantic request/response schemas
│   ├── routes/
│   │   ├── lesson.py                # Lesson generation + save/list routes
│   │   ├── feedback.py              # Feedback submission + AI summary routes
│   │   └── dashboard.py             # Dashboard analytics routes
│   ├── main.py                      # FastAPI entry point
│   └── airflow_mongoDB_postgres/    # Separate Airflow ingestion pipeline (Data Engineering)
├── frontend/
│   └── app.py                       # Streamlit app: Dashboard, Generate Lesson, Submit Feedback
├── docker-compose.yml                # Local PostgreSQL for the app
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Ukpoweh/sabilearn_ai.git
cd sabilearn_ai
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Then fill in:
```
GEMINI_API_KEY=your_google_gemini_api_key
DATABASE_URL=postgresql+psycopg2://sabilearn:sabilearn@localhost:5432/sabilearn
```

### 5. Start PostgreSQL
```bash
docker-compose up -d database
```

### 6. Run the FastAPI backend
```bash
uvicorn backend.main:app --reload
```
Tables are created automatically on startup. Access API docs at:
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7. Run the Streamlit frontend
```bash
streamlit run frontend/app.py
```
Use the sidebar to switch between **Dashboard**, **Generate Lesson**, and **Submit Feedback**.

---

## 🧾 API Endpoints

### 🔹 Lesson Generation
**POST** `/generate_lesson`

Generates a contextual lesson plan (no DB write yet — review before saving):
```json
{
  "subject": "Mathematics",
  "topic": "Fractions",
  "level": "Junior Secondary",
  "language": "English",
  "mode": "rural"
}
```

**Response (sample)**:
```json
{
  "title": "Understanding Fractions Through Local Materials",
  "objectives": ["Identify fractions", "Simplify fractions"],
  "introduction": "Fractions can be understood by sharing items like fruits...",
  "activities_rural": ["Use oranges to demonstrate fractions", "Divide yam pieces equally"],
  "resources": ["Oranges", "Blackboard"],
  "quiz": ["What is 1/2 of 10?", "Simplify 4/8"]
}
```

### 🔹 Save Lesson
**POST** `/lessons/`

Saves a reviewed lesson plan against a teacher:
```json
{
  "teacher_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "topic": "Fractions",
  "mode": "rural",
  "content_json": { "...": "the generated lesson plan above" }
}
```

### 🔹 List Lessons
**GET** `/lessons/?teacher_id=<uuid>` — lesson summaries for a given teacher.

### 🔹 Submit Feedback
**POST** `/feedback/`

One student response (emoji tap + optional comment) per call:
```json
{
  "lesson_id": "<uuid>",
  "student_id": null,
  "emoji": "😊",
  "comment": "The cassava example helped!"
}
```

### 🔹 Feedback Summary (AI-powered)
**GET** `/feedback/summary?lesson_id=<uuid>&limit=15`

Aggregates recent comments and asks Gemini for themes/sentiment:
```json
{
  "count": 12,
  "avg_score": 4.1,
  "ai_summary": {
    "overall_sentiment": "Positive",
    "key_themes": ["Engagement", "Pacing"],
    "summary": "Most feedback was positive, though some students struggled with the pace."
  }
}
```

### 🔹 Dashboard Analytics
**GET** `/analytics` — total lessons, average sentiment, active teachers, top topics, and recent activity.

---

## 🧮 Data Pipeline (Airflow Integration)

The **Airflow ingestion layer** under `backend/airflow_mongoDB_postgres/` (developed by the Data Engineering team) is a separate stack with its own Postgres/Mongo/docker-compose. It fetches and cleans curriculum datasets; `generator.py` reads its `curriculum_sample.csv` directly for prompt-grounding snippets.

---

## 🧑‍💻 Developer Notes

- All Gemini calls use **structured output schemas** to enforce predictable JSON responses.
- Async methods ensure concurrency when generating lessons or analyzing feedback.
- Tables (`lessons`, `feedback`, `activity_logs`) are created automatically on FastAPI startup via `init_db()` — no separate migration step is required for local dev.

---

## 🚀 Future Roadmap

- [ ] Offline-first sync (`/sync/batch`, IndexedDB queue) for low-connectivity classrooms.
- [ ] Multilingual lesson generation (Yoruba, Igbo, Hausa) and USSD/SMS feedback channels.
- [ ] JWT-based auth for teachers/administrators.
- [ ] Teacher analytics dashboard with regional filters and CSV export.

---
