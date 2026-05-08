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
- return response in language of the input audio/transcript.

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
    Use OpenAI GPT to generate all insights at once.
    Returns dict with summary, keyPoints, actionItems, topics.
    Returns None if OpenAI is not available.
    Prioritizes Groq if enabled, then falls back to OpenAI.
    """
    if not settings.use_groq() and not settings.use_openai():
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        print("[LLMInsights] Sending transcript to GPT for structured insights...")

        # Truncate very long transcripts to fit context window
        max_chars = 12000
        truncated = text[:max_chars] + ("..." if len(text) > max_chars else "")

        # --- Try Groq first ---
        if settings.use_groq():
            print("[LLMInsights] 🚀 Using Groq for structured insights...")
            try:
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
                print(f"[LLMInsights] ⚠ Groq failed for insights: {e}. Falling back to OpenAI...")

        # --- Fallback to OpenAI ---
        if not settings.use_openai():
            print("[LLMInsights] ✗ OpenAI not enabled or API key missing. Cannot generate insights.")
            return None

        from openai import OpenAI
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        print("[LLMInsights] Sending transcript to GPT for structured insights...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
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

        raw = response.choices[0].message.content.strip()
        result = _parse_and_validate_json(raw)
        result["insightsModel"] = "OpenAI gpt-3.5-turbo"
        return result

        # Validate structure
        required = ["summary", "keyPoints", "actionItems", "topics"]
        for key in required:
            if key not in data:
                raise ValueError(f"Missing key: {key}")

        print("[LLMInsights] GPT insights generated successfully.")
        return data

    except json.JSONDecodeError as e:
        print(f"[LLMInsights] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[LLMInsights] Error: {e}")
        return None

def _parse_and_validate_json(raw_json_string: str) -> dict:
    """Helper to parse JSON and validate structure."""
    # Strip markdown code fences if present
    raw_json_string = re.sub(r'^```json\s*', '', raw_json_string)
    raw_json_string = re.sub(r'^```\s*', '', raw_json_string)
    raw_json_string = re.sub(r'\s*```$', '', raw_json_string)

    data = json.loads(raw_json_string)

    # Validate structure
    required = ["summary", "keyPoints", "actionItems", "topics"]
    for key in required:
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    print("[LLMInsights] Insights generated successfully.")
    return data