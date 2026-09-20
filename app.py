from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os

# 1. Aap ki pipeline import
from voice_pipeline import VoicePipeline

# 2. Dev 1 ki database files/functions import
from database import get_db       # Dev 1 ka DB connection
import crud                      # Dev 1 ke CRUD functions

app = FastAPI()
pipeline = VoicePipeline()

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

    # Voice Pipeline run karein (Aap ka code call hua)
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