from pydantic import BaseModel
from typing import List, Optional

class SentimentResult(BaseModel):
    label: str           # POSITIVE / NEGATIVE / NEUTRAL
    score: float         # 0.0 to 1.0
    tone: str            # friendly description

class MeetingResponse(BaseModel):
    meetingId: str
    mode: str            # "local", "openai", or "groq"
    transcription: str
    summary: str
    keyPoints: List[str]
    actionItems: List[str]
    sentiment: SentimentResult
    topics: List[str]
    speechModel: str
    insightsModel: str
    createdAt: Optional[str] = None
    error: Optional[str] = None

class MeetingHistory(BaseModel):
    meetingId: str
    summary: Optional[str]
    topics: List[str]
    created_at: str

    class Config:
        from_attributes = True
