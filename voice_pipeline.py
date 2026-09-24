import os
import json
import asyncio
from dotenv import load_dotenv
from groq import Groq
import edge_tts
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

class VoicePipeline:
    def __init__(self, tts_voice: str = "ur-PK-AsadNeural"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.tts_voice = tts_voice

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry_error_callback=lambda retry_state: {"error": "Groq API call failed after 3 attempts."}
    )
    def _call_intent_llm(self, system_prompt: str, user_prompt: str) -> dict:
        """Internal helper method to query LLM with structured output and retry logic."""
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def _generate_audio_reply(self, text: str, output_audio_path: str) -> str:
        """Generates Urdu audio speech response using Edge-TTS."""
        communicate = edge_tts.Communicate(text, self.tts_voice)
        await communicate.save(output_audio_path)
        return output_audio_path

    def process_voice_command(self, audio_path: str, output_reply_audio: str = "reply.mp3") -> dict:
        """
        Main pipeline function:
        1. Transcribes incoming audio (STT via Whisper)
        2. Classifies intent & extracts entities (NER via LLM)
        3. Generates Urdu spoken audio reply (TTS via Edge-TTS)
        
        Returns final structured JSON dictionary.
        """
        if not os.path.exists(audio_path):
            return {"error": f"Audio file '{audio_path}' not found."}

        # Step 1: Speech-to-Text (STT)
        try:
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_path, file.read()),
                    model="whisper-large-v3-turbo",
                    language="ur",
                    response_format="text"
                )
            recognized_text = transcription.strip()
        except Exception as e:
            return {"error": f"Whisper STT failed: {str(e)}"}

        if not recognized_text:
            return {"error": "Transcription returned empty text."}

        # Step 2: Intent Classification & Entity Extraction
        system_prompt = """
You are an AI assistant analyzing user intent and extracting contextual details regarding availability.

Classify intent into EXACTLY ONE category:
1. AVAILABLE: Free, ready to talk, or available right now.
2. BUSY: Occupied, unavailable, asking to call later, or expressing uncertainty/ambiguity.
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

        try:
            output_json = self._call_intent_llm(system_prompt, user_prompt)
            output_json["transcript"] = recognized_text
        except Exception as e:
            return {
                "error": f"Intent LLM processing failed: {str(e)}",
                "transcript": recognized_text
            }

        # Step 3: Text-to-Speech (TTS) - Safe Event Loop Execution
        if "reply" in output_json and output_json["reply"]:
            try:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    audio_file_saved = loop.run_until_complete(
                        self._generate_audio_reply(output_json["reply"], output_reply_audio)
                    )
                else:
                    audio_file_saved = loop.run_until_complete(
                        self._generate_audio_reply(output_json["reply"], output_reply_audio)
                    )

                output_json["reply_audio_path"] = audio_file_saved
            except Exception as e:
                output_json["reply_audio_path"] = None
                output_json["tts_error"] = str(e)

        return output_json


# Quick execution block for standalone testing
if __name__ == "__main__":
    pipeline = VoicePipeline()
    sample_audio = "test_audios/test_location.mp3"
    
    print(f"Processing audio input: {sample_audio} ...")
    result = pipeline.process_voice_command(sample_audio)
    
    print("\n--- FINAL PIPELINE OUTPUT ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))