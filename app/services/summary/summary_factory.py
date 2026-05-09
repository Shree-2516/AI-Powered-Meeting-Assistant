from app.core.settings import settings
from app.services.summary import local_summary, groq_summary

def summarize(text: str) -> str:
    """
    Auto-selects summary service based on settings priority:
    1. Groq (FREE, FAST, HIGH QUALITY) ✨
    2. Local HuggingFace
    
    Returns summary text
    """
    
    # ✨ Try Groq first (FREE & FAST)
    if settings.use_groq():
        print("[SummaryFactory] 🚀 Using Groq LLM (FASTEST & FREE)")
        try:
            summary = groq_summary.summarize(text)
            return summary
        except Exception as e:
            print(f"[SummaryFactory] ⚠ Groq failed: {e}. Falling back...")
    
    # Fallback to local HuggingFace
    print("[SummaryFactory] Using Local HuggingFace")
    summary = local_summary.summarize(text)
    return summary

def extract_key_points(text: str, num_points: int = 8) -> list:
    """
    Extract key points using Groq if available, otherwise fallback.
    """
    if settings.use_groq():
        print(f"[KeyPointsFactory] 🚀 Using Groq for key point extraction")
        try:
            points = groq_summary.extract_key_points(text, num_points)
            return points
        except Exception as e:
            print(f"[KeyPointsFactory] ⚠ Groq failed: {e}. Falling back...")
    
    # Fallback to local
    print(f"[KeyPointsFactory] Using Local extraction")
    return local_summary._extract_key_points_fallback(text, num_points)

def extract_action_items(text: str) -> list:
    """
    Extract action items using Groq if available, otherwise fallback.
    """
    if settings.use_groq():
        print(f"[ActionItemsFactory] 🚀 Using Groq for action item extraction")
        try:
            items = groq_summary.extract_action_items(text)
            return items
        except Exception as e:
            print(f"[ActionItemsFactory] ⚠ Groq failed: {e}. Falling back...")
    
    # Fallback to local
    print(f"[ActionItemsFactory] Using Local extraction")
    return local_summary._extract_key_points_fallback(text, 5)