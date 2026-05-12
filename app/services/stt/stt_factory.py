from app.core.config import settings
from app.services.stt import local_stt, groq_stt

def transcribe(audio_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Auto-selects STT service based on settings priority:
    1. Groq (FREE, FASTEST) ✨
    2. Local Whisper
    
    Returns (transcription_text, mode_used)
    """
    
    # ✨ Try Groq first (FREE & FAST)
    if settings.use_groq():
        print("[STTFactory] 🚀 Using Groq STT (FASTEST & FREE)")
        try:
            text = groq_stt.transcribe(audio_bytes, filename)
            return text, "groq"
        except Exception as e:
            print(f"[STTFactory] ⚠ Groq failed: {e}. Falling back...")
    
    # Fallback to local Whisper
    print("[STTFactory] Using Local Whisper STT")
    text = local_stt.transcribe(audio_bytes, filename)
    return text, "local"