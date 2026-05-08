import uuid
import os
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.response_models import MeetingResponse, SentimentResult
from app.services.stt import stt_factory
from app.services.summary import summary_factory
from app.services.sentiment import sentiment_service
from app.services.keypoints import keypoints_service
from app.services.topics import topic_service
from app.services.cleaner import text_cleaner
from app.services.insights import llm_insights
from app.core.settings import settings

router = APIRouter()
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
            detail=f"Unsupported file type '{ext}'. Allowed: wav, mp3, m4a, ogg, flac, webm."
        )

    meeting_id = str(uuid.uuid4())[:8].upper()
    print(f"\n{'='*50}")
    print(f"[Meeting {meeting_id}] Processing started — {audio.filename}")
    print(f"{'='*50}")

    try:
        # ── Read audio (chunked) ──────────────────────────
        chunks = []
        total_size = 0
        while True:
            chunk = await audio.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large. Max 200 MB.")
            chunks.append(chunk)

        audio_bytes = b"".join(chunks)
        print(f"[Meeting {meeting_id}] Size: {len(audio_bytes)/1024/1024:.1f} MB")

        # ── Step 1: Transcription ─────────────────────────
        print(f"[Meeting {meeting_id}] Step 1/5: Transcription...")
        raw_transcription, mode = stt_factory.transcribe(audio_bytes, audio.filename)

        if not raw_transcription or len(raw_transcription.strip()) < 5:
            raise HTTPException(
                status_code=422,
                detail="Could not transcribe audio. File may be silent or too short."
            )

        print(f"[Meeting {meeting_id}] Transcript: {len(raw_transcription.split())} words")

        speech_model = {
            "groq": f"Groq {settings.GROQ_SPEECH_MODEL}",
            "openai": "OpenAI Whisper",
            "local": f"Local Whisper ({settings.WHISPER_MODEL})"
        }.get(mode, "Local Whisper")

        # ── Step 2: Clean transcript ──────────────────────
        print(f"[Meeting {meeting_id}] Step 2/5: Cleaning...")
        clean_text = text_cleaner.clean(raw_transcription)

        # ── Step 3: Generate all insights ────────────────
        print(f"[Meeting {meeting_id}] Step 3/5: Generating insights...")

        summary = None
        key_points = None
        action_items = None
        topics = None
        llm_result = None

        # Try LLM first (OpenAI) — best quality
        if settings.use_openai():
            print(f"[Meeting {meeting_id}] Using OpenAI for all insights...")
            llm_result = llm_insights.generate(clean_text)

            if llm_result:
                summary = llm_result.get("summary", "")
                key_points = llm_result.get("keyPoints", [])
                action_items = llm_result.get("actionItems", [])
                topics = llm_result.get("topics", [])
                print(f"[Meeting {meeting_id}] LLM insights: OK")
            else:
                print(f"[Meeting {meeting_id}] LLM failed, falling back to local...")

        # Local fallback (or if OpenAI not configured)
        if summary is None:
            print(f"[Meeting {meeting_id}] Using local models for insights...")
            summary = summary_factory.summarize(clean_text)

        if key_points is None:
            key_points = keypoints_service.extract(clean_text, num_points=8)

        if action_items is None:
            action_items = keypoints_service.extract_action_items(clean_text)

        if topics is None:
            topics = topic_service.extract(clean_text, num_topics=8)

        insights_model = llm_result.get("insightsModel") if llm_result else None
        if not insights_model:
            insights_model = f"Local summary + extraction ({settings.SUMMARY_MODEL})"

        # ── Step 4: Sentiment ─────────────────────────────
        print(f"[Meeting {meeting_id}] Step 4/5: Sentiment...")
        sentiment_raw = sentiment_service.analyze(clean_text)
        sentiment = SentimentResult(**sentiment_raw)

        # ── Step 5: Final validation ──────────────────────
        print(f"[Meeting {meeting_id}] Step 5/5: Finalising...")

        # Ensure no empty outputs
        if not key_points:
            key_points = ["No key points could be extracted from this audio."]
        if not action_items:
            action_items = ["Review meeting transcript for follow-up tasks."]
        if not topics:
            topics = ["General Discussion"]

        print(f"[Meeting {meeting_id}] ✅ Done!\n")

        return MeetingResponse(
            meetingId=meeting_id,
            mode=mode,
            transcription=raw_transcription,
            summary=summary,
            keyPoints=key_points,
            actionItems=action_items,
            sentiment=sentiment,
            topics=topics,
            speechModel=speech_model,
            insightsModel=insights_model
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Meeting {meeting_id}] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")