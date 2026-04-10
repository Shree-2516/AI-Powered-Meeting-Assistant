import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.models.response_models import MeetingResponse, SentimentResult
from app.services.stt import stt_factory
from app.services.summary import summary_factory
from app.services.sentiment import sentiment_service
from app.services.keypoints import keypoints_service
from app.services.topics import topic_service
from app.core.settings import settings

router = APIRouter()


@router.get("/status")
def get_status():
    """Check which mode (local vs openai) is active."""
    return {
        "status": "ok",
        "mode": "openai" if settings.use_openai() else "local",
        "whisper_model": settings.WHISPER_MODEL,
        "summary_model": settings.SUMMARY_MODEL,
        "openai_key_set": bool(settings.OPENAI_API_KEY),
        "use_openai_flag": settings.USE_OPENAI,
    }


@router.post("/process-meeting", response_model=MeetingResponse)
async def process_meeting(audio: UploadFile = File(...)):
    """
    Main endpoint.
    Input : audio file (wav, mp3, m4a, ogg, flac, webm)
    Output: full meeting insights as JSON
    """

    # --- Validate file type ---
    allowed_types = {
        "audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a",
        "audio/ogg", "audio/flac", "audio/webm",
        "audio/x-wav", "audio/x-m4a", "video/webm"
    }
    allowed_extensions = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

    import os
    ext = os.path.splitext(audio.filename)[-1].lower()

    if audio.content_type not in allowed_types and ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {audio.content_type}. Use wav, mp3, m4a, ogg, flac, or webm."
        )

    meeting_id = str(uuid.uuid4())[:8].upper()
    print(f"\n{'='*50}")
    print(f"[Meeting {meeting_id}] Processing started")
    print(f"[Meeting {meeting_id}] File: {audio.filename}, Mode: {'openai' if settings.use_openai() else 'local'}")
    print(f"{'='*50}")

    try:
        # --- Step 1: Read audio bytes ---
        audio_bytes = await audio.read()
        print(f"[Meeting {meeting_id}] Audio size: {len(audio_bytes) / 1024:.1f} KB")

        # --- Step 2: Transcription ---
        print(f"[Meeting {meeting_id}] Step 1/5: Transcription...")
        transcription, mode = stt_factory.transcribe(audio_bytes, audio.filename)

        if not transcription or len(transcription.strip()) < 5:
            raise HTTPException(
                status_code=422,
                detail="Could not transcribe audio. File may be too short or silent."
            )

        # --- Step 3: Summary ---
        print(f"[Meeting {meeting_id}] Step 2/5: Summary...")
        summary = summary_factory.summarize(transcription)

        # --- Step 4: Sentiment ---
        print(f"[Meeting {meeting_id}] Step 3/5: Sentiment analysis...")
        sentiment_raw = sentiment_service.analyze(transcription)
        sentiment = SentimentResult(**sentiment_raw)

        # --- Step 5: Key Points ---
        print(f"[Meeting {meeting_id}] Step 4/5: Key points...")
        key_points = keypoints_service.extract(transcription, num_points=5)
        action_items = keypoints_service.extract_action_items(transcription)

        # --- Step 6: Topics ---
        print(f"[Meeting {meeting_id}] Step 5/5: Topics...")
        topics = topic_service.extract(transcription, num_topics=8)

        print(f"[Meeting {meeting_id}] ✅ All steps complete!\n")

        return MeetingResponse(
            meetingId=meeting_id,
            mode=mode,
            transcription=transcription,
            summary=summary,
            keyPoints=key_points,
            actionItems=action_items,
            sentiment=sentiment,
            topics=topics
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Meeting {meeting_id}] ❌ Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )