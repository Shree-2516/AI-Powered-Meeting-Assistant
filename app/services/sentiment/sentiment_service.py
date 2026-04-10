from textblob import TextBlob

def analyze(text: str) -> dict:
    """
    Analyze sentiment of meeting transcript.
    Returns label, score, and tone description.
    Always runs locally — fast and free.
    """
    if not text or len(text.strip()) < 5:
        return {"label": "NEUTRAL", "score": 0.5, "tone": "No content to analyze"}

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity       # -1.0 to 1.0
    subjectivity = blob.sentiment.subjectivity  # 0.0 to 1.0

    # Map polarity to label
    if polarity > 0.15:
        label = "POSITIVE"
        tone = _positive_tone(polarity, subjectivity)
    elif polarity < -0.15:
        label = "NEGATIVE"
        tone = _negative_tone(polarity, subjectivity)
    else:
        label = "NEUTRAL"
        tone = _neutral_tone(subjectivity)

    # Normalize score to 0–1 range
    score = round((polarity + 1) / 2, 3)

    return {
        "label": label,
        "score": score,
        "tone": tone
    }

def _positive_tone(polarity: float, subjectivity: float) -> str:
    if polarity > 0.6:
        return "Very enthusiastic and optimistic meeting"
    elif subjectivity > 0.6:
        return "Positive and energetic discussion"
    else:
        return "Constructive and productive meeting"

def _negative_tone(polarity: float, subjectivity: float) -> str:
    if polarity < -0.6:
        return "Highly critical or tense meeting"
    elif subjectivity > 0.6:
        return "Emotional or frustrated discussion"
    else:
        return "Challenging topics discussed"

def _neutral_tone(subjectivity: float) -> str:
    if subjectivity < 0.3:
        return "Objective and factual discussion"
    else:
        return "Balanced, mixed-tone meeting"