from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import os
import models
from database import engine, get_db, test_db_connection

# VoicePipeLine() import
from fastapi import UploadFile, File, HTTPException
from voice_pipeline import VoicePipeline
pipeline = VoicePipeline()

# crud functions for voice requests
from crud import create_voice_request

try:
    test_db_connection()
    models.Base.metadata.create_all(bind=engine)
except Exception as exc:
    raise RuntimeError(
        "PostgreSQL is not running or DATABASE_URL is incorrect. "
        "Start PostgreSQL and confirm the .env value is correct."
    ) from exc

app = FastAPI(title="Blue-Collar Hiring Hub API")

# Pydantic Schemas for Validation
class OTPRequest(BaseModel):
    phone: str
    cnic: Optional[str] = None  # Optional for employers

class OTPVerify(BaseModel):
    phone: str
    otp: str


import random
from fastapi import HTTPException

# Lightweight in-memory cache for OTPs during development (Phone -> OTP)
otp_cache = {}

@app.post("/send-otp")

def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    # 1. Generate a random 4-digit OTP
    generated_otp = str(random.randint(1000, 9999))
    
    # 2. Store it in the cache against the phone number
    otp_cache[request.phone] = {
        "otp": generated_otp,
        "cnic": request.cnic # Temporarily hold the CNIC if provided for registration
    }
    
    # TODO: Implement actual SMS gateway (Twilio/SNS) here. 
    # For now, print to terminal so you can test end-to-end without a real SMS service.
    print(f"--- MOCK SMS TO {request.phone}: Your OTP is {generated_otp} ---")
    
    return {"message": f"OTP sent successfully to {request.phone}"}

@app.post("/verify-otp")

def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    # 1. Check if OTP exists and matches
    cached_data = otp_cache.get(request.phone)
    
    if not cached_data or cached_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP") # Replaces the mock on line 40
        
    # 2. Clear the OTP from cache to prevent reuse
    del otp_cache[request.phone]
    
    # 3. Check if the user already exists in the database
    worker = db.query(models.Worker).filter(models.Worker.phone == request.phone).first()
    
    # 4. If they don't exist, create a new worker record
    if not worker:
        if not cached_data.get("cnic"):
            raise HTTPException(status_code=400, detail="CNIC required for new worker registration")
            
        new_worker = models.Worker(
            phone=request.phone, 
            cnic=cached_data["cnic"], 
            status="inactive" # Defaults to inactive as per your models.py
        )
        db.add(new_worker)
        db.commit()
        db.refresh(new_worker)
        return {"message": "New worker verified and registered", "worker_id": new_worker.id}

    return {"message": "Existing user verified successfully", "worker_id": worker.id}

@app.post("/process-voice/{worker_id}")
async def process_worker_voice(worker_id: int, audio_file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Verify the worker exists
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # 2. Save the uploaded audio file temporarily to disk
    file_location = f"temp_{worker_id}_{audio_file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await audio_file.read())
            
        # 3. Call Dev 2's pipeline function
        result = pipeline.process_voice_command(file_location)
        
        # 4. Log the interaction in the new VoiceRequest table
        new_request = models.VoiceRequest(
            worker_id=worker_id,
            transcript=result.get("transcript"),
            intent=result.get("intent"),
            area=result.get("area"),
            duration=result.get("duration"),
            reply_text=result.get("reply_text"),
            reply_audio_path=result.get("reply_audio_path")
        )
        db.add(new_request)
        
        # 5. Update the worker's status based on the parsed intent
        if result.get("intent") == "status_update_active":
            worker.status = "active"
        elif result.get("intent") == "status_update_inactive":
            worker.status = "inactive"
            
        if result.get("area"):
            worker.area = result.get("area")
            
        db.commit()
        
    finally:
        # Clean up the temporary file
        if os.path.exists(file_location):
            os.remove(file_location)
            
    return {
        "message": "Voice processed successfully", 
        "updated_status": worker.status,
        "pipeline_data": result
    }

@app.post("/process-voice/{worker_id}")
async def process_worker_voice(
    worker_id: int, 
    audio_file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # 1. Check if worker exists in DB
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # 2. Save incoming audio file to disk
    file_location = f"temp_{worker_id}_{audio_file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await audio_file.read())

        # 3. Process voice command through pipeline
        result = pipeline.process_voice_command(file_location)

        # 4. Save voice request record to DB via CRUD function
        new_request = create_voice_request(
            db=db, 
            worker_id=worker_id, 
            voice_data=result
        )

        # 5. Update worker status and area based on intent
        if result.get("intent") == "status_update_active":
            worker.status = "active"
        elif result.get("intent") == "status_update_inactive":
            worker.status = "inactive"

        if result.get("area"):
            worker.area = result.get("area")

        db.commit()

    finally:
        # 6. Delete temporary file
        if os.path.exists(file_location):
            os.remove(file_location)

    # 7. Return complete response
    return {
        "message": "Voice processed successfully",
        "updated_status": worker.status,
        "pipeline_data": result,
        "request_id": new_request.id
    }