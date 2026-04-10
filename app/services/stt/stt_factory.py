from app.core.settings import settings
from app.services.stt import local_stt, openai_stt

def transcribe(audio_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Auto-selects STT service based on settings.
    Returns (transcription_text, mode_used)
    """
    if settings.use_openai():
        print("[STTFactory] Using OpenAI STT")
        text = openai_stt.transcribe(audio_bytes, filename)
        return text, "openai"
    else:
        print("[STTFactory] Using Local Whisper STT")
        text = local_stt.transcribe(audio_bytes, filename)
        return text, "local"