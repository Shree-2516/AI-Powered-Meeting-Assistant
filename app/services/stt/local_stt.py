import whisper
import tempfile
import os
from app.core.settings import settings

# Load model once at module level (avoids reloading on every request)
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"[LocalSTT] Loading Whisper model: {settings.WHISPER_MODEL}")
        _model = whisper.load_model(settings.WHISPER_MODEL)
        print("[LocalSTT] Model loaded.")
    return _model

def transcribe(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio bytes using local Whisper model.
    Saves to a temp file, runs Whisper, returns transcript string.
    """
    suffix = os.path.splitext(filename)[-1] or ".wav"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_model()
        print(f"[LocalSTT] Transcribing file: {tmp_path}")
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        print(f"[LocalSTT] Done. Length: {len(text)} chars")
        return text
    finally:
        os.unlink(tmp_path)