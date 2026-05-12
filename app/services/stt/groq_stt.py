import io
import json
from groq import Groq
from app.core.config import settings

# Initialize Groq client
_client = None

def get_client():
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=settings.GROQ_API_KEY)
        print("[GroqSTT] Groq client initialized")
    return _client

def transcribe(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio using Groq's Whisper model.
    
    ✨ Groq Benefits:
    - FREE API (with rate limits)
    - Extremely fast transcription (real-time inference)
    - No local GPU needed
    - High accuracy with whisper-large-v3-turbo
    
    Args:
        audio_bytes: Raw audio data
        filename: Original filename (for content type detection)
    
    Returns:
        Transcribed text
    """
    try:
        client = get_client()
        
        # Convert bytes to file-like object
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        
        print(f"[GroqSTT] Transcribing using model: {settings.GROQ_SPEECH_MODEL}")
        print(f"[GroqSTT] File size: {len(audio_bytes) / 1024 / 1024:.2f} MB")
        
        # Groq transcription request
        transcript = client.audio.transcriptions.create(
            file=(filename, audio_file, _get_mime_type(filename)),
            model=settings.GROQ_SPEECH_MODEL,
            temperature=0.0  # For consistency
        )
        
        text = transcript.text.strip()
        print(f"[GroqSTT] ✓ Transcription complete: {len(text.split())} words")
        return text
        
    except Exception as e:
        print(f"[GroqSTT] ✗ Error: {str(e)}")
        raise

def _get_mime_type(filename: str) -> str:
    """Determine MIME type from filename."""
    ext = filename.lower().split('.')[-1] if '.' in filename else 'wav'
    
    mime_types = {
        'wav': 'audio/wav',
        'mp3': 'audio/mpeg',
        'm4a': 'audio/mp4',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'webm': 'audio/webm',
        'mp4': 'audio/mp4'
    }
    
    return mime_types.get(ext, 'audio/wav')