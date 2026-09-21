# Standard Library Imports
import os        # Used to clean up/delete the temporary audio files from the server after processing
import random    # Used to generate the random 4-digit numbers for your OTP verification

# Type Hinting
from typing import Optional  # Allows you to define optional fields in your schemas (like 'cnic' or 'urgency')

# Core FastAPI Components
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
# FastAPI: Initializes your core application
# Depends: Injects the database session into your route functions
# HTTPException: Allows you to return proper API errors (like 404 Not Found or 400 Invalid OTP)
# UploadFile, File: Handles parsing and receiving the audio files sent from the frontend

# Data Validation
from pydantic import BaseModel # Used as the base class to define your JSON request schemas (e.g., EmployerVoiceSearch)

# Database Architecture
from sqlalchemy.orm import Session # Provides the type hint for your active database connection inside your routes

# Your Local Project Files
import models # Imports your SQLAlchemy table definitions (Worker, Employer, VoiceRequest)
from database import engine, get_db, test_db_connection 
# engine: The actual connection string to your PostgreSQL/SQLite database
# get_db: The generator function that opens and closes database sessions for each request
# test_db_connection: Verifies the database is running when the app starts

from voice_pipeline import VoicePipeline # Tamreena's AI pipeline that converts audio to text and extracts intents
from crud import create_voice_request    # A helper function to cleanly save the voice interaction logs to the database

pipeline = VoicePipeline()

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

class EmployerVoiceSearch(BaseModel):
    service_type: str
    area: str
    urgency: Optional[str] = None


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

@app.post("/employer/search")
def search_active_workers(search: EmployerVoiceSearch, db: Session = Depends(get_db)):
    # 1. Base query: Only look for workers who are currently "active"
    query = db.query(models.Worker).filter(models.Worker.status == "active")
    
    # 2. Filter by area if the employer provided one (case-insensitive)
    if search.area:
        query = query.filter(models.Worker.area.ilike(f"%{search.area}%"))
        
    # 3. Filter by service_type (e.g., "plumber", "electrician")
    if search.service_type:
        query = query.filter(models.Worker.service_type.ilike(f"%{search.service_type}%"))
        
    # Execute the query and fetch results
    results = query.all()
    
    return {
        "message": "Search completed",
        "total_matches": len(results),
        "workers": results
    } 