from openai import OpenAI
from app.core.settings import settings

def summarize(text: str) -> str:
    """
    Summarize meeting transcript using OpenAI GPT.
    """
    if not text or len(text.strip()) < 50:
        return text

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    print("[OpenAISummary] Sending to GPT for summarization...")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert meeting notes assistant. "
                    "Summarize the meeting transcript clearly and concisely. "
                    "Focus on decisions made, key discussion points, and outcomes."
                )
            },
            {
                "role": "user",
                "content": f"Please summarize this meeting transcript:\n\n{text}"
            }
        ],
        max_tokens=500,
        temperature=0.3
    )
    
    summary = response.choices[0].message.content.strip()
    print("[OpenAISummary] Done.")
    return summary