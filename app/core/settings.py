import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    USE_OPENAI: bool = os.getenv("USE_OPENAI", "false").lower() == "true"
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    SUMMARY_MODEL: str = os.getenv("SUMMARY_MODEL", "facebook/bart-large-cnn")

    def use_openai(self) -> bool:
        """Returns True only if key is set AND USE_OPENAI flag is true."""
        return bool(self.OPENAI_API_KEY) and self.USE_OPENAI

settings = Settings()