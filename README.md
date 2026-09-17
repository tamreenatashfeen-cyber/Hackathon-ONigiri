ONigiri - Voice AI Intent & Availability Engine 🎙️⚡
ONigiri is an end-to-end, high-performance Voice AI pipeline built for real-time speech processing and intent classification. Designed for high-speed hackathon environments and production integration, the engine ingests multilingual audio input (Urdu, English, and Roman Urdu/Code-switching) and extracts structured availability intent (BUSY, AVAILABLE, UNKNOWN) alongside contextual replies.

Powered by Groq Cloud Infrastructure for low-latency inference.

🏗️ Architecture & Pipeline Flow
The core architecture follows a decoupled, two-stage AI processing pipeline encapsulated within a single modular core function (process_voice_intent):

Stage 1: Speech-to-Text (STT) -> Model: whisper-large-v3-turbo (Groq) with Urdu/Pakistani speech context hints.

Stage 2: Intent Engine & LLM Reasoning -> Model: openai/gpt-oss-20b (Groq) returning a strict JSON object.

✨ Key Features & Technical Highlights
Bilingual & Code-Switching Resilience: Built to handle Urdu, English, and mixed Roman Urdu/Pakistani English speech seamlessly without misinterpreting scripts.

Strict Intent Categorization: Accurately classifies user availability into standardized states:

AVAILABLE: User is free, ready to talk, or accessible.

BUSY: User is occupied, in a meeting, or requesting a call back later.

UNKNOWN: General small talk, weather comments, or off-topic queries.

Deterministic JSON Schema: Uses strict LLM output formatting (json_object) to guarantee seamless integration with downstream services (FastAPI, Webhooks, Databases, TTS).

Sub-Second Latency: Leverages Groq LPU inference hardware for near-instant speech recognition and reasoning.

🛠️ Tech Stack & Dependencies
Language: Python 3.10+

Inference Provider: Groq API

Audio Processing: OpenAI Whisper Large v3 Turbo

Language Model: GPT-OSS-20B

Environment & Tools: python-dotenv, groq, Git, VS Code

📂 Repository Structure
Hackathon-ONigiri/
├── main.py              # Core Voice AI pipeline function (process_voice_intent)
├── test_pipeline.py     # Batch testing script for multi-voice verification
├── .env                 # API Keys and Environment configuration (Git-ignored)
├── .gitignore           # Ignored files (.venv, cache, secrets)
└── README.md            # Project documentation
⚙️ Installation & Setup Guide
1. Clone the Repository
git clone [https://github.com/tamreenatashfeen-cyber/Hackathon-ONigiri.git](https://github.com/tamreenatashfeen-cyber/Hackathon-ONigiri.git)
cd Hackathon-ONigiri

2. Set Up Virtual Environment
On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\activate

On macOS/Linux:
python -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install python-dotenv groq

4. Configure Environment Variables
Create a .env file in the root directory and add your Groq API Key:
GROQ_API_KEY=your_groq_api_key_here

🚀 Usage
Call process_voice_intent() passing the path to any .mp3 or .wav file:

Python
from main import process_voice_intent

# Execute pipeline
result = process_voice_intent("test_voice_3_mine.mp3")
print(result)
Example JSON Response
JSON
{
  "intent": "BUSY",
  "reply": "آپ کا پیغام موصول ہوا۔ براہِ کرم اپنا وقت خالی ہونے کے بعد دوبارہ رابطہ کریں۔ شکریہ۔",
  "transcript": "میں ابھی اویلیبل نہیں ہوں"
}
🧪 Testing Results (Day 1 Verification)
Tested across multiple voice samples for accuracy verification:

test_voice_1_ali.mp3: Audio Content: Availability query | Recognized Intent: AVAILABLE | Status: Pass

test_voice_2_ayan.mp3: Audio Content: Small talk ("Aaj mausam bohot acha hai") | Recognized Intent: UNKNOWN | Status: Pass

test_voice_3_mine.mp3: Audio Content: "Main abhi available nahi hoon" | Recognized Intent: BUSY | Status: Pass
