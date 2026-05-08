import json
from groq import Groq
from app.core.settings import settings

# Initialize Groq client
_client = None

def get_client():
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=settings.GROQ_API_KEY)
        print("[GroqSummary] Groq client initialized")
    return _client

def summarize(text: str) -> str:
    """
    Generate a concise summary of the meeting transcript using Groq.
    
    ✨ Groq Benefits:
    - FREE API (with rate limits)
    - Ultra-fast inference (better than local models)
    - No GPU required
    - High-quality summaries with Mixtral 8x7B
    
    Args:
        text: Full meeting transcript
    
    Returns:
        Concise summary (3-5 sentences)
    """
    if not text or len(text.strip()) < 50:
        return text
    
    try:
        client = get_client()
        
        # Truncate if too long to save tokens
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        print(f"[GroqSummary] Generating summary using {settings.GROQ_LLM_MODEL}")
        print(f"[GroqSummary] Input length: {len(truncated_text)} chars")
        
        response = client.messages.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional meeting summarizer. Provide a concise, clear summary (3-5 sentences) of the meeting transcript. Focus on key points, decisions, and action items."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this meeting transcript:\n\n{truncated_text}"
                }
            ],
            temperature=0.5,  # Balanced between creativity and consistency
            max_tokens=300,
            top_p=0.9
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"[GroqSummary] ✓ Summary generated: {len(summary.split())} words")
        return summary
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error generating summary: {str(e)}")
        # Fallback to extractive summary
        return _extractive_fallback(text)

def extract_key_points(text: str, num_points: int = 8) -> list:
    """
    Extract key points from meeting transcript using Groq LLM.
    
    Args:
        text: Full meeting transcript
        num_points: Number of key points to extract
    
    Returns:
        List of key point strings
    """
    if not text or len(text.strip()) < 50:
        return ["No substantial content to extract key points."]
    
    try:
        client = get_client()
        
        # Truncate if too long
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        print(f"[GroqSummary] Extracting {num_points} key points...")
        
        response = client.messages.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a meeting analyst. Extract exactly {num_points} clear, concise key points from the meeting transcript. Return ONLY a JSON array of strings, no other text."
                },
                {
                    "role": "user",
                    "content": f"Meeting transcript:\n\n{truncated_text}\n\nExtract {num_points} key points as JSON array:"
                }
            ],
            temperature=0.3,
            max_tokens=500,
            top_p=0.9
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        try:
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            key_points = json.loads(response_text)
            if isinstance(key_points, list):
                print(f"[GroqSummary] ✓ Extracted {len(key_points)} key points")
                return key_points[:num_points]
        except json.JSONDecodeError:
            print(f"[GroqSummary] ⚠ Failed to parse JSON response, returning raw text")
            return [point.strip() for point in response_text.split('\n') if point.strip()][:num_points]
        
        return key_points
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error extracting key points: {str(e)}")
        return _extract_key_points_fallback(text, num_points)

def extract_action_items(text: str) -> list:
    """
    Extract action items and follow-ups from meeting transcript using Groq LLM.
    
    Args:
        text: Full meeting transcript
    
    Returns:
        List of action items
    """
    if not text or len(text.strip()) < 50:
        return ["Review the full transcript for action items."]
    
    try:
        client = get_client()
        
        # Truncate if too long
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        print(f"[GroqSummary] Extracting action items...")
        
        response = client.messages.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a meeting coordinator. Extract all action items, tasks, and follow-ups from the meeting. Return ONLY a JSON array of strings describing each action item, no other text."
                },
                {
                    "role": "user",
                    "content": f"Meeting transcript:\n\n{truncated_text}\n\nExtract action items as JSON array:"
                }
            ],
            temperature=0.3,
            max_tokens=400,
            top_p=0.9
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        try:
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            action_items = json.loads(response_text)
            if isinstance(action_items, list):
                print(f"[GroqSummary] ✓ Extracted {len(action_items)} action items")
                return action_items if action_items else ["Review transcript for action items."]
        except json.JSONDecodeError:
            print(f"[GroqSummary] ⚠ Failed to parse JSON, returning raw text")
            return [item.strip() for item in response_text.split('\n') if item.strip()]
        
        return action_items if action_items else ["Review transcript for action items."]
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error extracting action items: {str(e)}")
        return ["Review transcript for action items."]

def _extractive_fallback(text: str) -> str:
    """Fallback: simple extractive summary if Groq fails."""
    sentences = text.split('.')
    if len(sentences) > 3:
        return '. '.join(sentences[:3]) + '.'
    return text[:500] + '...'

def _extract_key_points_fallback(text: str, num_points: int) -> list:
    """Fallback: extract key points using simple heuristics."""
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return sentences[:num_points] if sentences else ["Unable to extract key points."]