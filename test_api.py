import os
import json
import re
import time
import asyncio
from dotenv import load_dotenv
# --- UPDATED IMPORTS FOR THE NEW SDK ---
from google import genai 
from google.genai import types 
# ----------------------------------------
import pandas as pd
from typing import Dict, Any, Optional

# Load environment variables (from root .env)
load_dotenv()

# --- Configuration and Initialization ---

# Get API Key
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    # Use standard Python exception for environment checks
    raise RuntimeError("❌ GEMINI_API_KEY not found in .env")

# Model choice
MODEL_NAME = "gemini-2.5-flash"

# Define the absolute path to the prompts directory based on user input
# NOTE: Using a raw string (r"...") is best practice for Windows paths.
PROMPT_DIR = r"C:\Users\Ukpoweh Gift\Documents\edubridge_ai\backend\ai\prompts"

# Define the Lesson Plan Schema for structured output
LessonPlanSchema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "title": types.Schema(type=types.Type.STRING, description="The catchy title of the lesson."),
        "objectives": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="A list of measurable learning objectives for the student."
        ),
        "introduction": types.Schema(type=types.Type.STRING, description="A script for the introduction connecting the topic to local context in Nigeria."),
        "activities_urban": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="A list of practical activities suitable for an urban classroom setting."
        ),
        "activities_rural": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="A list of practical activities suitable for a rural classroom setting, using local materials."
        ),
        "resources": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="A list of required teaching resources (e.g., blackboard, chalk, specific items)."
        ),
        "quiz": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="A list of 3-5 quiz questions to check understanding."
        ),
    },
    required=["title", "objectives", "introduction", "activities_urban", "activities_rural", "resources", "quiz"]
)


# Initialize the Asynchronous Client Globally
try:
    # Initialize the synchronous client first (using genai.Client)
    # Then access the asynchronous interface using .aio
    ASYNC_CLIENT = genai.Client(api_key=GEMINI_KEY).aio
except Exception as e:
    # Update the error message to reflect the attempt to initialize the async part
    print(f"FATAL: Could not initialize Async client. Ensure 'google-genai' is installed: {e}")
    ASYNC_CLIENT = None

# Curriculum data (optional)
# --- FIX: Ensure correct relative path and improve error logging ---
# Path should be relative to this file: ai_core.py (backend/ai/) -> one up (backend/) -> data/ -> curriculum_sample.csv
CURRICULUM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "data", "curriculum_sample.csv")
try:
    _curr_df = pd.read_csv(CURRICULUM_PATH)
    print("✅ Curriculum data loaded.")
except FileNotFoundError:
    _curr_df = None
    print(f"⚠️ Curriculum data NOT loaded. File not found at path: {CURRICULUM_PATH}")
except Exception as e:
    _curr_df = None
    print(f"❌ Curriculum data loading error: {type(e).__name__}: {e}")


# --- Helper Functions ---

def get_curriculum_snippet(topic: str) -> str:
    """Retrieve a short summary from curriculum CSV matching the topic."""
    if _curr_df is None:
        return ""
    matches = _curr_df[_curr_df['topic'].str.contains(topic, case=False, na=False)]
    if not matches.empty:
        return matches.sample(1).iloc[0]['summary']
    return ""


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from Gemini response text, handling markdown blocks."""
    try:
        # 1. Try to find JSON inside a markdown block (most common LLM format)
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            return json.loads(json_str)

        # 2. Fallback: Try to find a standalone JSON object 
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            json_str = match.group(0).strip()
            # Clean up the JSON string before loading (e.g., remove trailing characters)
            return json.loads(json_str)

        print("⚠️ No JSON found in Gemini response.")
        return None
    except Exception as e:
        print(f"❌ JSON extraction/parsing failed: {e}")
        return None


async def generate_with_gemini(prompt: str, max_output_tokens: int = 3000, retries: int = 3) -> Optional[str]:
    """Send a structured prompt to Gemini using the asynchronous client."""
    if ASYNC_CLIENT is None:
        print("❌ Gemini client not available.")
        return None
        
    print(f"\n🔹 Using Gemini model: {MODEL_NAME}")
    print(f"🧩 Prompt preview:\n{prompt[:200]}...\n")

    # Use GenerationConfig class for explicit typing and structured output
    config = types.GenerateContentConfig(
        # *** CHANGED: Increased token limit from 1500 to 3000 to prevent truncation ***
        max_output_tokens=max_output_tokens,
        # MANDATORY: Set the response format to JSON
        response_mime_type="application/json",
        # MANDATORY: Provide the structure the model must follow
        response_schema=LessonPlanSchema
    )

    for attempt in range(retries):
        try:
            # Await the asynchronous function call
            response = await ASYNC_CLIENT.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config
            )

            # NOTE: When response_mime_type="application/json", response.text should contain pure JSON.
            if response.text and response.text.strip():
                print("✅ Gemini returned text successfully.")
                return response.text.strip()
            
            # --- DEBUGGING LOGIC: Log reason for empty response ---
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason.name if candidate.finish_reason else "UNKNOWN"
                print(f"⚠️ Gemini returned empty text (Attempt {attempt + 1}). Finish reason: {finish_reason}")
                
                if response.prompt_feedback:
                    # Log safety settings blocks if any
                    safety_ratings = [f"{r.category.name}: {r.probability.name}" 
                                      for r in response.prompt_feedback.safety_ratings]
                    print(f"   Safety Ratings: {', '.join(safety_ratings)}")

            else:
                print(f"⚠️ Gemini returned an unexpected response structure (Attempt {attempt + 1}). Retrying...")

            # --- END DEBUGGING LOGIC ---

            # Use asyncio.sleep for async wait
            await asyncio.sleep(2 * (attempt + 1)) 

        except Exception as e:
            # Implement exponential backoff for API calls
            wait_time = 2 ** (attempt + 1)
            # Log the full API error
            print(f"🔥 Gemini API Request Error (attempt {attempt + 1}): {type(e).__name__}: {e}. Waiting {wait_time}s.")
            await asyncio.sleep(wait_time) 

    print("❌ All Gemini attempts failed.")
    return None


# --- Main Lesson Generator ---

async def generate_lesson(
    subject: str, 
    topic: str, 
    level: str, 
    language: str = "English", 
    mode: str = "urban"
) -> Dict[str, Any]:
    """Asynchronously generates a lesson plan."""
    snippet = get_curriculum_snippet(topic)

    # Load prompt templates
    try:
        # NOTE: Using the absolute path defined by PROMPT_DIR
        system_prompt_path = os.path.join(PROMPT_DIR, "system_prompt.txt")
        user_prompt_path = os.path.join(PROMPT_DIR, "user_prompt.txt")

        # Synchronous file reading is fine as it's typically fast setup
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

        with open(user_prompt_path, "r", encoding="utf-8") as f:
            user_prompt_template = f.read()
    except FileNotFoundError as e:
        print(f"❌ Prompt file missing: {e}")
        # Default fallback prompts
        system_prompt = "You are an expert curriculum developer. Your task is to generate a lesson plan in JSON format. Only output the JSON object that conforms to the required schema."
        user_prompt_template = "Generate a lesson plan about {topic} for {subject} at {level} level in a {mode} setting, using {language}. Output the lesson plan as a single JSON object."


    # Format prompt
    user_prompt = user_prompt_template.format(
        topic=topic,
        subject=subject,
        level=level,
        mode=mode,
        language=language
    )

    full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nCurriculum snippet: {snippet or ''}"

    print(f"\n🧠 Generating lesson for: {topic}")

    # Await the asynchronous function call
    text = await generate_with_gemini(full_prompt) 
    
    print(f"\n🔹 Gemini raw output preview:\n{text[:500] if text else 'No text returned.'}\n")

    # When using structured output, text should be pure JSON, but we use the extractor as a safety net.
    parsed = extract_json_from_text(text) if text else None

    if parsed:
        print("✅ Parsed Gemini JSON successfully.")
        return parsed

    # --- Fallback in case Gemini fails or returns invalid JSON ---
    print("⚠️ Gemini output invalid or empty. Using fallback.")
    fallback = {
        "title": f"{topic} - fallback lesson",
        "objectives": [f"Understand basic ideas about {topic}."],
        "introduction": f"This is a fallback short introduction connecting {topic} to daily life in Nigeria.",
        "activities_urban": ["Class discussion; write notes."],
        "activities_rural": ["Storytelling; field observation."],
        "resources": ["Local materials, chalk, paper."],
        "quiz": [f"What is one key idea about {topic}?"]
    }

    return fallback


# --- Main Execution Block ---

if __name__ == "__main__":
    # Example parameters for testing
    test_subject = "Mathematics"
    test_topic = "Calculating Area and Perimeter"   
    test_level = "Primary 6"
    test_mode = "urban"  # or "rural"
   
    print(f"\n🚀 Running Lesson Generator for: {test_topic} ({test_subject}, {test_mode})")
    print("-" * 60)
    
    # Check if the client initialized successfully
    if ASYNC_CLIENT is None:
        print("\nFATAL: Cannot run. Async client failed to initialize (check API Key and SDK install).")
    else:
        try:
            # Use asyncio.run to execute the main asynchronous function
            lesson_plan = asyncio.run(generate_lesson(
                test_subject, 
                test_topic, 
                test_level, 
                mode=test_mode
            ))
            
            # Print final result
            print("\n" + "=" * 60)
            print("✅ GENERATION COMPLETE")
            # Nicely formatted JSON output
            print(json.dumps(lesson_plan, indent=4))
            print("=" * 60)

        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        except Exception as e:
            # Catch any other unexpected runtime exceptions
            print(f"\nAn unhandled error occurred during execution: {e}")
