# Standard Library Imports
import os
import random
from typing import Optional

# Core FastAPI Components
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# BoLocal Local Project Files
import models
from database import engine, get_db, test_db_connection
from voice_pipeline import VoicePipeline
from crud import create_voice_request

# Initialize app and CORS once
app = FastAPI(title="BoLocal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = VoicePipeline()

# Database setup
try:
    test_db_connection()
    models.Base.metadata.create_all(bind=engine)
except Exception as exc:
    raise RuntimeError(
        "Database is not running or DATABASE_URL is incorrect."
    ) from exc

# In-memory OTP cache
otp_cache = {}

# Pydantic Schemas
class OTPRequest(BaseModel):
    phone: str
    cnic: Optional[str] = None

class OTPVerify(BaseModel):
    phone: str
    otp: str

class EmployerVoiceSearch(BaseModel):
    service_type: str
    area: str
    urgency: Optional[str] = None

# --- Routes ---

@app.post("/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    generated_otp = str(random.randint(1000, 9999))
    otp_cache[request.phone] = {
        "otp": generated_otp,
        "cnic": request.cnic
    }
    print(f"--- MOCK SMS TO {request.phone}: Your OTP is {generated_otp} ---")
    return {"message": f"OTP sent successfully to {request.phone}"}

@app.post("/verify-otp")
def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    cached_data = otp_cache.get(request.phone)
    if not cached_data or cached_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    del otp_cache[request.phone]
    
    worker = db.query(models.Worker).filter(models.Worker.phone == request.phone).first()
    if not worker:
        if not cached_data.get("cnic"):
            raise HTTPException(status_code=400, detail="CNIC required for new worker registration")
            
        new_worker = models.Worker(
            phone=request.phone, 
            cnic=cached_data["cnic"], 
            status="inactive"
        )
        db.add(new_worker)
        db.commit()
        db.refresh(new_worker)
        return {"message": "New worker verified and registered", "worker_id": new_worker.id}

    return {"message": "Existing user verified successfully", "worker_id": worker.id}

@app.post("/process-voice/{worker_id}")
async def process_worker_voice(
    worker_id: int, 
    audio_file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    file_location = f"temp_{worker_id}_{audio_file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await audio_file.read())

        result = pipeline.process_voice_command(file_location)

        new_request = create_voice_request(
            db=db, 
            worker_id=worker_id, 
            voice_data=result
        )

        if result.get("intent") == "status_update_active":
            worker.status = "active"
        elif result.get("intent") == "status_update_inactive":
            worker.status = "inactive"

        if result.get("area"):
            worker.area = result.get("area")

        db.commit()

    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

    return {
        "message": "Voice processed successfully",
        "updated_status": worker.status,
        "pipeline_data": result,
        "request_id": new_request.id
    }

@app.post("/employer/search")
def search_active_workers(search: EmployerVoiceSearch, db: Session = Depends(get_db)):
    query = db.query(models.Worker).filter(models.Worker.status == "active")
    if search.area:
        query = query.filter(models.Worker.area.ilike(f"%{search.area}%"))
    if search.service_type:
        query = query.filter(models.Worker.service_type.ilike(f"%{search.service_type}%"))
        
    results = query.all()
    return {
        "message": "Search completed",
        "total_matches": len(results),
        "workers": results
    }