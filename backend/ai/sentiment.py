import os
import sys
import asyncio
import re
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Windows consoles default to cp1252, which can't encode the emoji used in
# the log prints below — force UTF-8 so this doesn't crash on startup.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- Configuration ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY not found in .env")

MODEL_NAME = "gemini-flash-latest"

# --- Initialize Async Gemini Client ---
try:
    ASYNC_CLIENT = genai.Client(api_key=GEMINI_KEY).aio
except Exception as e:
    print(f"FATAL: Could not initialize Async client. Ensure 'google-genai' is installed: {e}")
    ASYNC_CLIENT = None

# --- Emoji Mapping ---
_EMOJI_MAP = {
    "😡": 1,
    "😢": 2,
    "😞": 2,
    "😐": 3,
    "🙂": 4,
    "😊": 5,
    "😀": 5
}

def emoji_to_score(emoji: str) -> int:
    """Convert emoji to numeric satisfaction score."""
    return _EMOJI_MAP.get(emoji.strip(), 3)


# --- Helper: JSON Extractor ---
def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON safely from Gemini response text."""
    try:
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return None
    except Exception as e:
        print(f"⚠️ JSON extraction failed: {e}")
        return None


# --- Schema for Gemini structured output ---
FeedbackSummarySchema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "overall_sentiment": types.Schema(
            type=types.Type.STRING,
            description="Overall feedback sentiment: Positive, Neutral, or Negative."
        ),
        "key_themes": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="List of major themes or recurring feedback points."
        ),
        "summary": types.Schema(
            type=types.Type.STRING,
            description="Short natural-language summary of user feedback (1–2 sentences)."
        ),
    },
    required=["overall_sentiment", "key_themes", "summary"]
)


# --- Gemini Call ---
async def analyze_with_gemini(feedback_text: str) -> Optional[str]:
    """Send feedback text to Gemini for structured analysis."""
    if ASYNC_CLIENT is None:
        print("❌ Gemini client unavailable.")
        return None

    config = types.GenerateContentConfig(
        max_output_tokens=1000,
        response_mime_type="application/json",
        response_schema=FeedbackSummarySchema
    )

    prompt = f"""
    Analyze the following feedback messages. Summarize their key themes, determine the overall sentiment (Positive, Neutral, or Negative),
    and provide a concise summary (2 sentences max).

    Feedback:
    {feedback_text}
    """

    try:
        response = await ASYNC_CLIENT.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config
        )
        if response.text:
            print("✅ Gemini response received.")
            return response.text.strip()
    except Exception as e:
        print(f"🔥 Gemini API error: {e}")
    return None


# --- Main Feedback Analysis Function ---
async def analyze_feedback_items(items: List[Dict]) -> Dict[str, Any]:
    """
    items: list of { 'emoji': '😊', 'comment': 'Loved the lesson!' }
    Returns: {
        "count": int,
        "avg_score": float,
        "ai_summary": {...Gemini structured output...}
    }
    """
    scores = []
    comments = []

    for item in items:
        if emoji := item.get("emoji"):
            scores.append(emoji_to_score(emoji))
        if comment := item.get("comment"):
            comments.append(comment)

    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    ai_summary = None
    if comments:
        joined_text = "\n".join(comments[:15])  # limit to first 15 comments
        text = await analyze_with_gemini(joined_text)
        ai_summary = extract_json_from_text(text) if text else None

    return {
        "count": len(items),
        "avg_score": avg_score,
        "ai_summary": ai_summary
    }


# --- Example Usage ---
if __name__ == "__main__":
    async def main():
        sample_feedback = [
            {"emoji": "😊", "comment": "I really enjoyed this lesson!"},
            {"emoji": "😐", "comment": "It was okay, but a bit fast."},
            {"emoji": "😡", "comment": "Too hard to follow and no examples."}
        ]
        result = await analyze_feedback_items(sample_feedback)
        print("\n📊 Final Feedback Analysis:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
