import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any, List, Optional
import json

# --- Configuration ---
# Assuming your FastAPI backend is running on the default port
FASTAPI_BASE_URL = "http://localhost:8000"

# NOTE: Use a mock UUID. In a real app, this would come from Firebase Auth.
# Ensure this ID is used when testing the POST /lessons endpoint.
MOCK_TEACHER_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef"


# --- Data Fetching Functions ---

@st.cache_data(ttl=60) # Cache data for 60 seconds to prevent excessive API calls
def fetch_analytics_data() -> Optional[Dict[str, Any]]:
    """Fetches aggregated analytics data from the FastAPI backend."""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/analytics")
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error connecting to FastAPI analytics endpoint: {e}")
        st.info("Please ensure your FastAPI backend is running on port 8000.")
        return None

@st.cache_data(ttl=60)
def fetch_teacher_lessons(teacher_id: str) -> List[Dict[str, Any]]:
    """Fetches a list of lessons created by a specific teacher."""
    try:
        # Use the /lessons endpoint with the teacher_id query parameter
        response = requests.get(f"{FASTAPI_BASE_URL}/lessons/", params={"teacher_id": teacher_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching teacher lessons: {e}")
        return []

# --- Streamlit UI Layout ---

def render_dashboard(data: Dict[str, Any]):
    """Renders the main dashboard elements."""
    
    st.title("🌍 EduBridge AI Dashboard")
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
                meta = " | ".join(f"{k}: {v}" for k, v in log['metadata'].items())

                return f"**{time_str}**: {event} (User: {log['teacher_id'][:8]}...)\n*{meta}*"

            # Display the activity log as a list
            st.markdown("\n\n".join(
                format_log_entry(log) for log in data['latest_activity']
            ))
        else:
            st.info("No recent activity logged.")

    st.markdown("---")
    
    # 3. Teacher's Personal Lessons
    st.subheader(f"Your Lessons (ID: {MOCK_TEACHER_ID[:8]}...)")
    teacher_lessons = fetch_teacher_lessons(MOCK_TEACHER_ID)
    
    if teacher_lessons:
        # Select key fields for display
        lessons_df = pd.DataFrame(teacher_lessons)
        lessons_df['created_at'] = pd.to_datetime(lessons_df['created_at']).dt.strftime('%Y-%m-%d')
        lessons_df = lessons_df[['title', 'topic', 'mode', 'created_at']]
        lessons_df.columns = ['Lesson Title', 'Subject Topic', 'Mode', 'Created On']
        st.dataframe(lessons_df, use_container_width=True)
    else:
        st.warning(f"No lessons found for teacher ID starting with {MOCK_TEACHER_ID[:8]}...")


# --- Main Execution ---

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    
    analytics_data = fetch_analytics_data()
    
    if analytics_data:
        render_dashboard(analytics_data)
    else:
        st.warning("⚠️ Waiting for the backend service to become available to display the dashboard.")
