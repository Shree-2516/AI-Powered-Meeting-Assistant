from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/status")
def get_status():
    return {
        "status": "ok",
        "mode": "groq" if settings.use_groq() else "local",
        "whisper_model": settings.WHISPER_MODEL,
        "summary_model": settings.SUMMARY_MODEL,
        "groq_key_set": bool(settings.GROQ_API_KEY),
        "use_groq_flag": settings.USE_GROQ,
        "max_file_size_mb": 200,
    }
