import os
import json
import time
from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Retry mechanism for API calls: Retries up to 3 times with exponential backoff (2s, 4s, 8s)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry_error_callback=lambda retry_state: {"error": "API calls failed after 3 attempts."}
)
def call_groq_llm(system_prompt: str, user_prompt: str) -> dict:
    """Helper function to execute Groq LLM completion with automatic retries."""
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def process_voice_intent(audio_path: str) -> dict:
    if not os.path.exists(audio_path):
        return {"error": f"Audio file '{audio_path}' not found."}
    
    # 1. Speech-to-Text with Exception Handling
    try:
        with open(audio_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3-turbo",
                language="ur",
                response_format="text"
            )
        recognized_text = transcription.strip()
    except Exception as e:
        return {"error": f"Whisper STT Failed: {str(e)}"}

    if not recognized_text:
        return {"error": "Audio transcription was empty."}

    # 2. System Prompt Formulation
    system_prompt = """
You are an AI assistant analyzing user intent and extracting contextual details regarding availability.

Classify intent into EXACTLY ONE category:
1. AVAILABLE: Free, ready to talk, or available.
2. BUSY: Occupied, unavailable, asking to call later, or expressing uncertainty.
3. UNKNOWN: Incomplete thoughts, random small talk, or off-topic comments.

Extract Entities:
- area: Specific location, area, or city mentioned (e.g., "Gulberg", "Rawalpindi"). If not mentioned, return null.
- duration: Timeframe or duration mentioned (e.g., "2 hours", "shaam tak"). If not mentioned, return null.

Respond ONLY with a valid JSON object matching this EXACT schema:
{
  "intent": "BUSY|AVAILABLE|UNKNOWN",
  "area": "Extracted location or null",
  "duration": "Extracted duration or null",
  "reply": "Contextual polite response in Urdu"
}

Examples:
- Transcript: "Gulberg mein 2 ghante free hoon" 
  -> {"intent": "AVAILABLE", "area": "Gulberg", "duration": "2 hours", "reply": "جی بہتر، میں آپ کی لوکیشن اور وقت نوٹ کر رہا ہوں۔"}
- Transcript: "Main abhi busy hoon 1 ghante tak" 
  -> {"intent": "BUSY", "area": null, "duration": "1 hour", "reply": "کال کا انتظار رہے گا، ایک گھنٹے بعد رابطہ کرتے ہیں۔"}
"""

    user_prompt = f'User transcript: "{recognized_text}"'

    # 3. Intent Parsing with Retry Logic
    try:
        output_json = call_groq_llm(system_prompt, user_prompt)
        output_json["transcript"] = recognized_text
        return output_json
    except Exception as e:
        return {
            "error": f"Intent LLM Processing Failed: {str(e)}",
            "transcript": recognized_text
        }


if __name__ == "__main__":
    result = process_voice_intent("test_audios/test_location.mp3")
    print(json.dumps(result, ensure_ascii=False, indent=2))