from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from datetime import datetime
from database import Base

class Worker(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True, index=True)
    cnic = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)
    status = Column(String, default="inactive")
    area = Column(String)

class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    employer_id = Column(Integer, ForeignKey("employers.id"))
    status = Column(String, default="pending")

class VoiceRequest(Base):
    __tablename__ = "voice_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    
    transcript = Column(Text)
    intent = Column(String)
    area = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    reply_text = Column(Text)
    reply_audio_path = Column(String)

class EmployerRequest(Base):
    __tablename__ = "employer_requests"

    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=True)
    service_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)