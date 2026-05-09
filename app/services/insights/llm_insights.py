import json
import re
from app.core.settings import settings
from groq import Groq


PROMPT = """You are an expert meeting notes assistant. Analyse the transcript below and return ONLY a valid JSON object with no extra text.

Important:
- Rewrite incomplete or fragmented speaker statements into complete, meaningful sentences.
- Do not return sentence fragments, trailing words, or unfinished thoughts.
- Use full, grammatical sentences for summary, keyPoints, and actionItems.

Rules:
- summary: 4-5 sentences max. Cohesive paragraph. Combine all ideas. No repetition.
- keyPoints: exactly 6-8 items. Each max 20 words. Start with a verb or noun. Use complete sentences only, ending with a period.
- actionItems: exactly 4-6 items. Real recommendations only. Start with an action verb. Max 20 words each, ending with a period.
- topics: exactly 6-8 items. 2-4 word phrases only. Real subjects discussed.
- CRITICAL: Return the response in the SAME LANGUAGE as the input transcript. If the transcript is in Hindi, the summary and points must be in Hindi.

Return this exact JSON format:
{
  "summary": "...",
  "keyPoints": ["...", "..."],
  "actionItems": ["...", "..."],
  "topics": ["...", "..."]
}

Transcript:
"""


def generate(text: str) -> dict | None:
    """
    Use Groq LLM to generate all insights at once.
    Returns dict with summary, keyPoints, actionItems, topics.
    Returns None if Groq is not available.
    """
    if not settings.use_groq():
        return None

    try:
        print("[LLMInsights] 🚀 Using Groq for structured insights...")
        
        # Truncate very long transcripts to fit context window
        max_chars = 12000
        truncated = text[:max_chars] + ("..." if len(text) > max_chars else "")

        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        groq_response = groq_client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert meeting analyst. Always respond with valid JSON only. No markdown, no explanation."
                },
                {
                    "role": "user",
                    "content": PROMPT + truncated
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )
        raw = groq_response.choices[0].message.content.strip()
        result = _parse_and_validate_json(raw)
        result["insightsModel"] = f"Groq {settings.GROQ_LLM_MODEL}"
        return result

    except Exception as e:
        print(f"[LLMInsights] ⚠ Groq failed for insights: {e}")
        return None


def _parse_and_validate_json(raw_json_string: str) -> dict:
    """Helper to parse JSON and validate structure."""
    # Strip markdown code fences if present
    raw_json_string = re.sub(r'^```json\s*', '', raw_json_string)
    raw_json_string = re.sub(r'^```\s*', '', raw_json_string)
    raw_json_string = re.sub(r'\s*```$', '', raw_json_string)

    try:
        data = json.loads(raw_json_string)
        # Validate structure
        required = ["summary", "keyPoints", "actionItems", "topics"]
        for key in required:
            if key not in data:
                raise ValueError(f"Missing key: {key}")
        print("[LLMInsights] Insights generated successfully.")
        return data
    except json.JSONDecodeError as e:
        print(f"[LLMInsights] JSON parse error: {e}")
        raise