from sqlalchemy.orm import Session
import models

def create_voice_request(db: Session, worker_id: int, voice_data: dict):
    db_voice = models.VoiceRequest(
        worker_id=worker_id,
        transcript=voice_data.get("transcript"),
        intent=voice_data.get("intent"),
        area=voice_data.get("area"),
        duration=voice_data.get("duration"),
        reply_text=voice_data.get("reply_text") or voice_data.get("reply"),
        reply_audio_path=voice_data.get("reply_audio_path")
    )
    db.add(db_voice)
    db.commit()
    db.refresh(db_voice)
    return db_voice

def save_employer_request(db: Session, employer_id: int, service_type: str, location: str, urgency: str, transcript: str):
    db_request = models.EmployerRequest(
        employer_id=employer_id,
        service_type=service_type,
        location=location,
        urgency=urgency,
        transcript=transcript
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request