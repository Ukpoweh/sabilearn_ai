import os
import pytest
from backend.ai.generator import generate_lesson, extract_json_from_text

def test_extract_json():
    text = "Here is the lesson: {\"title\":\"T1\",\"objectives\":[\"o1\"]}"
    parsed = extract_json_from_text(text)
    assert parsed.get("title") == "T1"

@pytest.mark.parametrize("topic", ["Photosynthesis", "Fractions"])
def test_generate_lesson_returns_dict(topic):
    # This test will attempt to call Gemini; skip if no key
    if not os.getenv("GEMINI_API_KEY") and os.getenv("FALLBACK_TO_LOCAL","false").lower() not in ("1","true","yes"):
        pytest.skip("No Gemini key and no fallback configured.")
    res = generate_lesson("Biology", topic, "JSS2", language="English", mode="rural")
    assert isinstance(res, dict)
    assert "title" in res or "raw" in res
