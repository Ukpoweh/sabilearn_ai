import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List, Optional
import json

# --- Configuration ---
# Assuming your FastAPI backend is running on the default port
FASTAPI_BASE_URL = "http://localhost:8000"

EMOJI_OPTIONS = {"😊 I understood!": "😊", "😐 It was okay": "😐", "😞 I'm confused": "😞"}


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Data Fetching Functions ---

@st.cache_data(ttl=60) # Cache data for 60 seconds to prevent excessive API calls
def fetch_analytics_data(token: str) -> Optional[Dict[str, Any]]:
    """Fetches aggregated analytics data from the FastAPI backend (admin only)."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/analytics", headers=_auth_headers(token))
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error connecting to FastAPI analytics endpoint: {e}")
        st.info("Please ensure your FastAPI backend is running on port 8000.")
        return None

@st.cache_data(ttl=60)
def fetch_teacher_lessons(token: str) -> List[Dict[str, Any]]:
    """Fetches the logged-in teacher's own lessons."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/lessons/", headers=_auth_headers(token))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching your lessons: {e}")
        return []

# --- Auth Screens ---

def render_login():
    """Login + registration screen shown when no one is logged in."""
    st.title("🌍 SabiLearn AI")

    login_tab, register_tab = st.tabs(["Log in", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/auth/token",
                    data={"username": username, "password": password},
                )
                response.raise_for_status()
                data = response.json()
                st.session_state["token"] = data["access_token"]
                st.session_state["role"] = data["role"]
                st.session_state["username"] = data["username"]
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Login failed: {e}")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            name = st.text_input("Full name")
            school_id = st.text_input("School (optional)", value="")
            subject = st.text_input("Subject (optional)", value="")
            admin_code = st.text_input("Admin code (optional, leave blank for teacher accounts)", value="")
            submitted_reg = st.form_submit_button("Register")

        if submitted_reg:
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/auth/register",
                    json={
                        "username": new_username,
                        "password": new_password,
                        "name": name,
                        "school_id": school_id or None,
                        "subject": subject or None,
                        "admin_code": admin_code or None,
                    },
                )
                response.raise_for_status()
                st.success("Account created! Switch to the Log in tab to sign in.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Registration failed: {e}")


# --- Streamlit UI Layout ---

def render_dashboard(data: Dict[str, Any]):
    """Renders the global admin dashboard elements."""

    st.title("🌍 SabiLearn AI Dashboard")
    st.subheader("Real-Time Metrics Across All Educators")

    # 1. KPI Metrics Row (using st.metric)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Lessons Generated",
            value=f"{data['total_lessons']:,}",
            delta="Data since inception"
        )

    with col2:
        sentiment = data['avg_sentiment']
        # Calculate sentiment change delta for visual feedback
        # Assuming 3.0 is a "neutral" baseline for delta calculation
        sentiment_delta = round(sentiment - 3.0, 2)
        st.metric(
            label="Avg. Student Sentiment (Score 1-5)",
            value=f"{sentiment:.2f}",
            delta=f"{sentiment_delta} points vs. Baseline",
            delta_color="normal" if sentiment >= 3.0 else "inverse"
        )

    with col3:
        st.metric(
            label="Active Teachers",
            value=data['active_teachers'],
            delta="Unique users who created lessons"
        )

    st.markdown("---")


    # 2. Charts and Activity
    col_chart, col_activity = st.columns([2, 1])

    with col_chart:
        st.subheader("Top 5 Lesson Topics (Popularity)")
        if data['lessons_by_topic']:
            # Convert list of dicts to a pandas DataFrame for charting
            topic_df = pd.DataFrame(data['lessons_by_topic'])
            # Streamlit is smart enough to chart this automatically
            st.bar_chart(topic_df, x="topic", y="count")
        else:
            st.info("No lessons have been saved yet.")

    with col_activity:
        st.subheader("Latest Activity Log")
        if data['latest_activity']:

            def format_log_entry(log: Dict[str, Any]) -> str:
                """Formats a single activity log entry for display."""
                timestamp_obj = pd.to_datetime(log['timestamp'])
                time_str = timestamp_obj.strftime("%b %d, %H:%M")
                event = log['event_type'].replace("_", " ").title()

                # Format metadata nicely
                meta = " | ".join(f"{k}: {v}" for k, v in (log['metadata'] or {}).items())

                return f"**{time_str}**: {event} (User: {log['teacher_id'][:8]}...)\n*{meta}*"

            # Display the activity log as a list
            st.markdown("\n\n".join(
                format_log_entry(log) for log in data['latest_activity']
            ))
        else:
            st.info("No recent activity logged.")


def render_my_lessons(token: str, username: str):
    """Teacher's own saved lessons — available to every logged-in user."""
    st.title("📚 My Lessons")
    st.subheader(f"Lessons saved by {username}")

    teacher_lessons = fetch_teacher_lessons(token)

    if teacher_lessons:
        lessons_df = pd.DataFrame(teacher_lessons)
        lessons_df['created_at'] = pd.to_datetime(lessons_df['created_at']).dt.strftime('%Y-%m-%d')
        lessons_df = lessons_df[['title', 'topic', 'mode', 'created_at']]
        lessons_df.columns = ['Lesson Title', 'Subject Topic', 'Mode', 'Created On']
        st.dataframe(lessons_df, use_container_width=True)
    else:
        st.warning("No lessons found yet — generate and save one first.")


def render_generate_lesson():
    """Teacher flow: generate a lesson with Gemini, preview it, then save it."""
    st.title("📝 Generate a Lesson")

    with st.form("generate_lesson_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject", value="Mathematics")
            topic = st.text_input("Topic", value="Fractions")
            level = st.text_input("Level", value="Junior Secondary")
        with col2:
            language = st.text_input("Language", value="English")
            mode = st.selectbox("Mode", ["urban", "rural"])
        submitted = st.form_submit_button("Generate Lesson")

    token = st.session_state["token"]

    if submitted:
        with st.spinner("Generating lesson with Gemini..."):
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/generate_lesson",
                    json={
                        "subject": subject,
                        "topic": topic,
                        "level": level,
                        "language": language,
                        "mode": mode,
                    },
                    headers=_auth_headers(token),
                )
                response.raise_for_status()
                st.session_state["generated_lesson"] = response.json()
                st.session_state["generated_lesson_meta"] = {"topic": topic, "mode": mode}
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error generating lesson: {e}")

    lesson = st.session_state.get("generated_lesson")
    if lesson:
        st.markdown("---")
        st.subheader(lesson.get("title", "Untitled Lesson"))

        st.markdown("**Objectives**")
        for obj in lesson.get("objectives", []):
            st.markdown(f"- {obj}")

        st.markdown("**Introduction**")
        st.write(lesson.get("introduction", ""))

        col_urban, col_rural = st.columns(2)
        with col_urban:
            st.markdown("**Urban Activities**")
            for act in lesson.get("activities_urban", []):
                st.markdown(f"- {act}")
        with col_rural:
            st.markdown("**Rural Activities**")
            for act in lesson.get("activities_rural", []):
                st.markdown(f"- {act}")

        st.markdown("**Resources**")
        for res in lesson.get("resources", []):
            st.markdown(f"- {res}")

        st.markdown("**Quiz**")
        for q in lesson.get("quiz", []):
            st.markdown(f"- {q}")

        st.markdown("---")
        if st.button("💾 Save & Mark Delivered"):
            meta = st.session_state.get("generated_lesson_meta", {})
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/lessons/",
                    json={
                        "topic": meta.get("topic", ""),
                        "mode": meta.get("mode", "urban"),
                        "content_json": lesson,
                    },
                    headers=_auth_headers(token),
                )
                response.raise_for_status()
                result = response.json()
                st.success(f"Lesson saved! ID: {result['lesson_id']}")
                del st.session_state["generated_lesson"]
                fetch_teacher_lessons.clear()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error saving lesson: {e}")


def render_submit_feedback():
    """Student flow: tap an emoji + optional comment for a lesson.

    Uses the logged-in teacher's own lesson list — this screen is handed to
    students on the teacher's device/tab during class, so no separate student
    login exists (anonymous by design).
    """
    st.title("🙋 Submit Feedback")

    token = st.session_state["token"]
    teacher_lessons = fetch_teacher_lessons(token)
    if not teacher_lessons:
        st.warning("No saved lessons yet — generate and save one first.")
        return

    options = {f"{l['title']} ({l['topic']})": l["id"] for l in teacher_lessons}
    selected_label = st.selectbox("Which lesson?", list(options.keys()))
    lesson_id = options[selected_label]

    emoji_label = st.radio("How was today's lesson?", list(EMOJI_OPTIONS.keys()))
    comment = st.text_area("Optional comment", value="")
    student_id = st.text_input("Student ID (optional, anonymous if left blank)", value="")

    if st.button("Submit Feedback"):
        try:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/feedback/",
                json={
                    "lesson_id": lesson_id,
                    "student_id": student_id or None,
                    "emoji": EMOJI_OPTIONS[emoji_label],
                    "comment": comment or None,
                },
            )
            response.raise_for_status()
            st.success("Feedback submitted — thank you!")
            fetch_analytics_data.clear()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error submitting feedback: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    st.set_page_config(layout="wide")

    if "token" not in st.session_state:
        render_login()
    else:
        role = st.session_state.get("role", "teacher")
        token = st.session_state["token"]

        st.sidebar.write(f"Logged in as **{st.session_state.get('username')}** ({role})")
        if st.sidebar.button("Log out"):
            for key in ("token", "role", "username"):
                st.session_state.pop(key, None)
            st.rerun()
        st.sidebar.markdown("---")

        nav_options = ["Generate Lesson", "My Lessons", "Submit Feedback"]
        if role == "admin":
            nav_options.insert(0, "Dashboard")
        page = st.sidebar.radio("Navigate", nav_options)

        if page == "Generate Lesson":
            render_generate_lesson()
        elif page == "My Lessons":
            render_my_lessons(token, st.session_state.get("username", ""))
        elif page == "Submit Feedback":
            render_submit_feedback()
        else:
            analytics_data = fetch_analytics_data(token)
            if analytics_data:
                render_dashboard(analytics_data)
            else:
                st.warning("⚠️ Waiting for the backend service to become available to display the dashboard.")
