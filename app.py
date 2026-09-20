import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from groq import Groq

from employer_parser import parse_employer_query
from voice_pipeline import VoicePipeline
from database import get_db
import crud
from database import engine
import models

# Yeh line database mein tables create kar degi agar woh maujood nahi hain
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
pipeline = VoicePipeline()

# Groq client for Whisper STT
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.post("/process-voice/")
async def process_voice_endpoint(
    worker_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Temp file save karein
    temp_file_path = f"uploaded_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Voice Pipeline run karein
    result = pipeline.process_voice_command(temp_file_path)

    # Temporary uploaded file delete karein
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Dev 1 ka database function call karke save karein
    db_record = crud.create_voice_request(
        db=db, 
        worker_id=worker_id, 
        voice_data=result
    )

    return {
        "status": "success",
        "data": result,
        "db_record_id": db_record.id
    }

@app.post("/process-employer-voice/")
async def process_employer_voice(
    employer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Save temp audio file
        temp_audio_path = f"temp_employer_{file.filename}"
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Speech to Text via Whisper
        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                language="ur"
            )
        raw_text = transcription.text

        # Clean temp file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        # 2. Parse Employer Query via Llama
        parsed_data = parse_employer_query(raw_text)

        # 3. Save to Database
        db_record = crud.save_employer_request(
            db=db,
            employer_id=employer_id,
            service_type=parsed_data.get("service_type"),
            location=parsed_data.get("area"),
            urgency=parsed_data.get("urgency"),
            transcript=raw_text
        )

        return {
            "status": "success",
            "data": parsed_data,
            "transcript": raw_text,
            "db_record_id": db_record.id
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}