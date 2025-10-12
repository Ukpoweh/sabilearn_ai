# SabiLearn AI

> **AI Copilot for Teachers in Nigeria** — designed to automate lesson plan generation, analyze classroom feedback, and integrate real-time data pipelines for continuous educational improvement.

---

## 🧠 Overview

SabiLearn AI is an intelligent education assistant built to support Nigerian teachers by:
- Generating **context-aware lesson plans** tailored to both **urban** and **rural** classrooms.
- Analyzing **student feedback** to understand sentiment, key learning themes, and engagement levels.
- Integrating with **Airflow** for automated data ingestion from external sources (e.g., curriculum datasets, performance metrics).

This backend leverages:
- **FastAPI** — for clean, modern API endpoints.
- **Google Gemini 2.5 Flash** — for AI-driven text generation and feedback analysis.
- **SQLite3** — for local data storage (lesson metadata, feedback logs).
- **Apache Airflow** — for ingestion and preprocessing pipelines (managed by the Data Engineering team).

---

## 🧩 Architecture

```
├── backend/
│   ├── ai/
│   │   ├── generator.py            # Gemini-based lesson plan generator
│   │   ├── sentiment.py    # Gemini-based feedback analysis module
│   │   ├── prompts/
│   │   │   ├── system_prompt.txt
│   │   │   └── user_prompt.txt
│   ├── data/
│   │   └── curriculum_sample.csv   # Curriculum snippets for context enrichment
│   ├── routes/
│   │   ├── lesson.py               # Lesson generation routes
│   │   ├── feedback.py             # Feedback submission routes
│   │   └── dashboard.py            # Dashboard analytics routes
│   ├── main.py                     # FastAPI entry point
│   ├── airflow/                    # Airflow ingestion DAGs (from Data Engineering)
│   └── data/feedback.db            # Local SQLite DB for feedback logs
├── .env                            # Environment variables (Gemini API key, etc.)
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/sabilearn_ai.git
cd sabilearn_ai/backend
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

Create a `.env` file in the **backend/** directory with:
```bash
GEMINI_API_KEY=your_google_gemini_api_key
```

If you’re using Airflow locally:
```bash
AIRFLOW_HOME=path_to_airflow_home
```

### 5. Run the FastAPI backend
```bash
uvicorn backend.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Access the API docs at:  
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧾 API Endpoints

### 🔹 Lesson Generation
**POST** `/lesson/generate`

Generates a contextual lesson plan:
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

---

### 🔹 Feedback Submission
**POST** `/feedback/submit`
```json
{
  "teacher_name": "Mr. Adebayo",
  "lesson_topic": "Photosynthesis",
  "feedback_text": "The students loved the demonstration.",
  "rating": 5
}
```

**Response:**
```json
{"message": "Feedback submitted successfully"}
```

---

### 🔹 Feedback Analysis (AI-powered)
**POST** `/dashboard/feedback-summary`

Analyzes submitted feedback (emojis + comments):
```json
{
  "feedback": [
    {"emoji": "😊", "comment": "I enjoyed this class!"},
    {"emoji": "😐", "comment": "The pace was too fast."}
  ]
}
```

**Response:**
```json
{
  "count": 2,
  "avg_score": 4.0,
  "ai_summary": {
    "overall_sentiment": "Positive",
    "key_themes": ["Engagement", "Pacing"],
    "summary": "Most feedback was positive, though some students struggled with the pace."
  }
}
```

---

## 🧮 Data Pipeline (Airflow Integration)

The **Airflow ingestion layer** (developed by the Data Engineering team) automatically:
- Fetches new datasets (e.g., curriculum updates, performance data).
- Cleans and stores them in the `/backend/data/` directory.
- Triggers metadata refresh for Gemini contextual prompts.

This ensures EduBridge AI+ always uses **fresh, curriculum-aligned data**.

---

## 🧑‍💻 Developer Notes

- All Gemini calls use **structured output schemas** to enforce predictable JSON responses.
- Async methods ensure concurrency when generating lessons or analyzing feedback.
- The SQLite database automatically initializes on first run (`feedback.db`).
- `data/curriculum_sample.csv` provides contextual snippets to improve prompt grounding.

---

## 🚀 Future Roadmap

- [ ] Multilingual lesson generation (Yoruba, Igbo, Hausa).
- [ ] Teacher analytics dashboard with Power BI integration.
- [ ] Offline-first mobile version using Streamlit.
- [ ] Integration with WAEC/NECO competency frameworks.

---
