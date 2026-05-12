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
        print("[GroqSummary] Groq client initialized")
    return _client

def summarize(text: str) -> str:
    """
    Generate a concise summary of the meeting transcript using Groq.
    """
    if not text or len(text.strip()) < 50:
        return text
    
    try:
        client = get_client()
        
        # Truncate if too long
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        print(f"[GroqSummary] Generating summary using {settings.GROQ_LLM_MODEL}")
        
        response = client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional meeting summarizer. Provide a concise summary (3-5 sentences). CRITICAL: Output must be in the SAME LANGUAGE as the input transcript."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this meeting transcript in its original language:\n\n{truncated_text}"
                }
            ],
            temperature=0.5,
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"[GroqSummary] ✓ Summary generated: {len(summary.split())} words")
        return summary
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error generating summary: {str(e)}")
        return _extractive_fallback(text)

def extract_key_points(text: str, num_points: int = 8) -> list:
    """
    Extract key points using Groq LLM.
    """
    if not text or len(text.strip()) < 50:
        return ["No substantial content to extract key points."]
    
    try:
        client = get_client()
        
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        print(f"[GroqSummary] Extracting {num_points} key points...")
        
        response = client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"Extract exactly {num_points} key points. Return ONLY a JSON array of strings. CRITICAL: Output MUST be in the SAME LANGUAGE as the input transcript."
                },
                {
                    "role": "user",
                    "content": f"Transcript:\n\n{truncated_text}\n\nExtract {num_points} key points as JSON array in original language:"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        try:
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            key_points = json.loads(response_text.strip())
            if isinstance(key_points, list):
                return key_points[:num_points]
        except:
            return [point.strip() for point in response_text.split('\n') if point.strip()][:num_points]
        
        return ["Error parsing key points."]
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error: {str(e)}")
        return _extract_key_points_fallback(text, num_points)

def extract_action_items(text: str) -> list:
    """
    Extract action items using Groq LLM.
    """
    if not text or len(text.strip()) < 50:
        return ["Review transcript."]
    
    try:
        client = get_client()
        
        max_chars = 8000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        response = client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Extract action items as a JSON array of strings. CRITICAL: Output MUST be in the SAME LANGUAGE as the input transcript."
                },
                {
                    "role": "user",
                    "content": f"Transcript:\n\n{truncated_text}\n\nExtract action items as JSON array in original language:"
                }
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        response_text = response.choices[0].message.content.strip()
        
        try:
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            action_items = json.loads(response_text.strip())
            return action_items if isinstance(action_items, list) else ["No action items found."]
        except:
            return [item.strip() for item in response_text.split('\n') if item.strip()]
        
    except Exception as e:
        print(f"[GroqSummary] ✗ Error: {str(e)}")
        return ["Review transcript."]

def _extractive_fallback(text: str) -> str:
    sentences = text.split('.')
    return '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else text[:500]

def _extract_key_points_fallback(text: str, num_points: int) -> list:
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    return sentences[:num_points] if sentences else ["Unable to extract."]