import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def parse_employer_query(text: str) -> dict:
    system_prompt = """
    You are an AI parser for employer hiring requests on a worker platform.
    Extract the following details from the employer's text:
    - service_type: Type of worker needed (e.g., "maid", "driver", "cook", "cleaner"). Return null if missing.
    - area: Location mentioned (e.g., "Gulberg", "DHA"). Return null if missing.
    - urgency: Timeframe or urgency (e.g., "now", "today", "2 hours"). Return null if missing.

    Respond ONLY with a valid JSON object:
    {
      "service_type": "string or null",
      "area": "string or null",
      "urgency": "string or null"
    }
    """

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.1,
        max_tokens=300,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)