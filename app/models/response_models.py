from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SentimentResult(BaseModel):
    label: str           # POSITIVE / NEGATIVE / NEUTRAL
    score: float         # 0.0 to 1.0
    tone: str            # friendly description

class MeetingResponse(BaseModel):
    meetingId: str
    mode: str            # "local" or "openai"
    transcription: str
    summary: str
    keyPoints: List[str]
    actionItems: List[str]
    sentiment: SentimentResult
    topics: List[str]
    error: Optional[str] = None