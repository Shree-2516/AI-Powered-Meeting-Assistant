import tempfile
import os
from openai import OpenAI
from app.core.settings import settings

def transcribe(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio bytes using OpenAI Whisper API.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    suffix = os.path.splitext(filename)[-1] or ".wav"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        print("[OpenAISTT] Sending audio to OpenAI Whisper API...")
        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        text = response.strip() if isinstance(response, str) else response
        print(f"[OpenAISTT] Done. Length: {len(text)} chars")
        return text
    finally:
        os.unlink(tmp_path)