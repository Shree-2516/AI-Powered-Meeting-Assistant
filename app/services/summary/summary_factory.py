from app.core.settings import settings
from app.services.summary import local_summary, openai_summary

def summarize(text: str) -> str:
    """
    Auto-selects summary service based on settings.
    """
    if settings.use_openai():
        print("[SummaryFactory] Using OpenAI Summary")
        return openai_summary.summarize(text)
    else:
        print("[SummaryFactory] Using Local HuggingFace Summary")
        return local_summary.summarize(text)