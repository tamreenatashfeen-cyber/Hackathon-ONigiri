from sqlalchemy import Column, Integer, String, ForeignKey, Text
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
    worker_id = Column(Integer, ForeignKey("workers.id")) # Link the request to the speaker
    
    # Columns requested by Tamreena aka dev 2 onigiri
    transcript = Column(Text)
    intent = Column(String)
    area = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    reply_text = Column(Text)
    reply_audio_path = Column(String)