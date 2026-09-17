import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_voice_intent(audio_path: str) -> dict:
    if not os.path.exists(audio_path):
        return {"error": f"Audio file '{audio_path}' not found."}
    
    try:
        # Step 1: STT with explicit Urdu language setting to stop language jumping
        with open(audio_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3-turbo",
                language="ur",  # Keeps Whisper stable in Pakistani/Urdu context
                response_format="text"
            )
        
        recognized_text = transcription.strip()
        
        # Step 2: Intent Parsing
        prompt = f"""
        User said: "{recognized_text}"
        
        Strict Categorization Rules:
        1. Classify the intent into EXACTLY ONE of these categories:
           - "AVAILABLE": User is free, ready to talk, or available.
           - "BUSY": User is occupied, unavailable, or asking to call later.
           - "UNKNOWN": Anything unrelated to availability (e.g. weather, random talk).
           
        2. Generate a professional and polite Urdu reply according to the intent.

        Respond strictly in JSON format:
        {{"intent": "BUSY|AVAILABLE|UNKNOWN", "reply": "Urdu response message"}}
        """

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        output_json = json.loads(response.choices[0].message.content)
        output_json["transcript"] = recognized_text
        return output_json

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    result = process_voice_intent("test_voice_3_mine.mp3")
    print(json.dumps(result, ensure_ascii=False, indent=2))