import uuid
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models.response_models import MeetingResponse, SentimentResult
from app.services.stt import stt_factory
from app.services.summary import summary_factory
from app.services.sentiment import sentiment_service
from app.services.keypoints import keypoints_service
from app.services.topics import topic_service
from app.core.settings import settings

router = APIRouter()

# 200 MB upload limit
MAX_FILE_SIZE = 200 * 1024 * 1024


@router.get("/status")
def get_status():
    return {
        "status": "ok",
        "mode": "openai" if settings.use_openai() else "local",
        "whisper_model": settings.WHISPER_MODEL,
        "summary_model": settings.SUMMARY_MODEL,
        "openai_key_set": bool(settings.OPENAI_API_KEY),
        "use_openai_flag": settings.USE_OPENAI,
        "max_file_size_mb": 200,
    }


@router.post("/process-meeting", response_model=MeetingResponse)
async def process_meeting(audio: UploadFile = File(...)):
    allowed_extensions = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
    ext = os.path.splitext(audio.filename)[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Use wav, mp3, m4a, ogg, flac, or webm."
        )

    meeting_id = str(uuid.uuid4())[:8].upper()
    print(f"\n{'='*50}")
    print(f"[Meeting {meeting_id}] Processing started")
    print(f"[Meeting {meeting_id}] File: {audio.filename}")
    print(f"{'='*50}")

    try:
        # --- Read audio (chunked for large files) ---
        print(f"[Meeting {meeting_id}] Reading audio file...")
        chunks = []
        total_size = 0

        while True:
            chunk = await audio.read(1024 * 1024)  # 1 MB at a time
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is 200 MB."
                )
            chunks.append(chunk)

        audio_bytes = b"".join(chunks)
        size_mb = len(audio_bytes) / 1024 / 1024
        print(f"[Meeting {meeting_id}] Audio size: {size_mb:.1f} MB")

        # Estimate processing time for user awareness
        est_minutes = max(1, int(size_mb / 5))
        print(f"[Meeting {meeting_id}] Estimated time: ~{est_minutes} minutes")

        # --- Step 1: Transcription ---
        print(f"[Meeting {meeting_id}] Step 1/5: Transcription (this takes longest)...")
        transcription, mode = stt_factory.transcribe(audio_bytes, audio.filename)

        if not transcription or len(transcription.strip()) < 5:
            raise HTTPException(
                status_code=422,
                detail="Could not transcribe audio. File may be silent or corrupted."
            )

        print(f"[Meeting {meeting_id}] Transcription done. Words: {len(transcription.split())}")

        # --- Step 2: Summary ---
        print(f"[Meeting {meeting_id}] Step 2/5: Summary...")
        summary = summary_factory.summarize(transcription)

        # --- Step 3: Sentiment ---
        print(f"[Meeting {meeting_id}] Step 3/5: Sentiment...")
        sentiment_raw = sentiment_service.analyze(transcription)
        sentiment = SentimentResult(**sentiment_raw)

        # --- Step 4: Key Points ---
        print(f"[Meeting {meeting_id}] Step 4/5: Key points...")
        key_points = keypoints_service.extract(transcription, num_points=8)
        action_items = keypoints_service.extract_action_items(transcription)

        # --- Step 5: Topics ---
        print(f"[Meeting {meeting_id}] Step 5/5: Topics...")
        topics = topic_service.extract(transcription, num_topics=10)

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
        print(f"[Meeting {meeting_id}] ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")