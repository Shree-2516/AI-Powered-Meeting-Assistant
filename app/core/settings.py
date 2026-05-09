import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Local Whisper (optional)
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    
    # Local Summary (optional)
    SUMMARY_MODEL: str = os.getenv("SUMMARY_MODEL", "facebook/bart-large-cnn")
    
    # ✨ GROQ - NEW CONFIGURATION
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    USE_GROQ: bool = os.getenv("USE_GROQ", "false").lower() == "true"
    GROQ_SPEECH_MODEL: str = os.getenv("GROQ_SPEECH_MODEL", "whisper-large-v3-turbo")
    GROQ_LLM_MODEL: str = os.getenv("GROQ_LLM_MODEL", "mixtral-8x7b-32768")
    
    # 🗄️ DATABASE - NEW CONFIGURATION
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_db")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

    def use_groq(self) -> bool:
        """Returns True only if Groq key is set AND USE_GROQ flag is true."""
        return bool(self.GROQ_API_KEY) and self.USE_GROQ

settings = Settings()