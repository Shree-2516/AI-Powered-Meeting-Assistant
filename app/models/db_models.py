from sqlalchemy import Column, String, Text, JSON, DateTime, Integer
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import uuid

class MeetingRecord(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id_short = Column(String(20), index=True)  # The 8-char ID shown in UI
    
    # Content
    transcription = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Insights (stored as JSON)
    key_points = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)
    sentiment = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    
    # Metadata
    mode = Column(String(20))
    speech_model = Column(String(50))
    insights_model = Column(String(50))
    
    # Vector for Semantic Search (384 dimensions for all-MiniLM-L6-v2)
    summary_vector = Column(Vector(384), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MeetingRecord(id={self.id}, meeting_id_short={self.meeting_id_short})>"
