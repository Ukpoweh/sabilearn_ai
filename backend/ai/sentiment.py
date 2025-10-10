from typing import List, Dict
from transformers import pipeline
import os

# Simple emoji mapping
_EMOJI_MAP = {
    "😡": 1,
    "😢": 2,
    "😐": 3,
    "🙂": 4,
    "😊": 5,
    "😀": 5
}

# Optional HF sentiment pipeline (English) - used for comments
_sentiment_pipeline = None
try:
    _sentiment_pipeline = pipeline("sentiment-analysis")
except Exception:
    _sentiment_pipeline = None

def emoji_to_score(emoji: str) -> int:
    return _EMOJI_MAP.get(emoji.strip(), 3)

def analyze_feedback_items(items: List[Dict]) -> Dict:
    """
    items: list of { 'emoji': '😊', 'comment': 'I liked the lesson' }
    Returns aggregated stats: counts, avg_score, top_issues (naive)
    """
    scores = []
    texts = []
    for it in items:
        emoji = it.get("emoji")
        if emoji:
            scores.append(emoji_to_score(emoji))
        if it.get("comment"):
            texts.append(it.get("comment"))

    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    # quick sentiment for comments if HF pipeline available
    top_issue = None
    if _sentiment_pipeline and texts:
        # analyze only first few for speed
        joined = " ".join(texts[:5])
        try:
            out = _sentiment_pipeline(joined)
            top_issue = out
        except Exception:
            top_issue = None

    return {
        "count": len(items),
        "avg_score": avg_score,
        "top_issue": top_issue
    }
