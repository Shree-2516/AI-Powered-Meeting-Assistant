from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import io

from app.db.session import get_db
from app.db.models import MeetingRecord
from app.schemas.meeting import MeetingHistory, MeetingResponse, SentimentResult
from app.services.embeddings import embedding_service
from app.services.pdf import generate_meeting_pdf

router = APIRouter()

@router.get("/", response_model=List[MeetingHistory])
async def get_history(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Fetch recent meeting history."""
    try:
        result = await db.execute(
            select(MeetingRecord)
            .order_by(desc(MeetingRecord.created_at))
            .limit(limit)
        )
        meetings = result.scalars().all()
        return [
            MeetingHistory(
                meetingId=m.meeting_id_short,
                summary=m.summary,
                topics=m.topics or [],
                created_at=m.created_at.isoformat()
            )
            for m in meetings
        ]
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

@router.get("/search", response_model=List[MeetingHistory])
async def search_meetings(query: str, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Perform semantic search using pgvector."""
    if not query:
        return []
        
    try:
        # Fallback to simple text search if pgvector is not available
        result = await db.execute(
            select(MeetingRecord)
            .where(MeetingRecord.summary.ilike(f"%{query}%"))
            .order_by(desc(MeetingRecord.created_at))
            .limit(limit)
        )
        meetings = result.scalars().all()
        
        return [
            MeetingHistory(
                meetingId=m.meeting_id_short,
                summary=m.summary,
                topics=m.topics or [],
                created_at=m.created_at.isoformat(),
            )
            for m in meetings
        ]
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting_detail(meeting_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch full details of a specific meeting."""
    try:
        result = await db.execute(
            select(MeetingRecord).where(MeetingRecord.meeting_id_short == meeting_id.upper())
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        return MeetingResponse(
            meetingId=meeting.meeting_id_short,
            mode=meeting.mode,
            transcription=meeting.transcription,
            summary=meeting.summary,
            keyPoints=meeting.key_points or [],
            actionItems=meeting.action_items or [],
            sentiment=SentimentResult(**meeting.sentiment) if meeting.sentiment else SentimentResult(label="NEUTRAL", score=0.0, tone="Unknown"),
            topics=meeting.topics or [],
            speechModel=meeting.speech_model,
            insightsModel=meeting.insights_model,
            createdAt=meeting.created_at.isoformat() if meeting.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch meeting details")

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific meeting."""
    try:
        from sqlalchemy import delete
        result = await db.execute(
            delete(MeetingRecord).where(MeetingRecord.meeting_id_short == meeting_id.upper())
        )
        await db.commit()
        return {"status": "success", "message": f"Meeting {meeting_id} deleted"}
    except Exception as e:
        print(f"Error deleting meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete meeting")

@router.get("/{meeting_id}/pdf")
async def download_meeting_pdf(meeting_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a text-based PDF report."""
    try:
        # 1. Fetch meeting data
        result = await db.execute(
            select(MeetingRecord).where(MeetingRecord.meeting_id_short == meeting_id.upper())
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        # 2. Convert to dictionary for PDF service
        data = {
            "meetingId": meeting.meeting_id_short,
            "transcription": meeting.transcription,
            "summary": meeting.summary,
            "keyPoints": meeting.key_points or [],
            "actionItems": meeting.action_items or [],
            "sentiment": meeting.sentiment or {},
            "topics": meeting.topics or [],
            "speechModel": meeting.speech_model,
            "createdAt": meeting.created_at.isoformat() if meeting.created_at else None
        }
        
        # 3. Generate PDF
        pdf_bytes = generate_meeting_pdf(data)
        
        # 4. Return as Response
        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Meeting_Report_{meeting_id}.pdf"}
        )
    except Exception as e:
        print(f"Error generating PDF for {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
