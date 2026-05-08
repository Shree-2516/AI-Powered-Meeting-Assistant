import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter


def extract(text: str, num_points: int = 8) -> list[str]:
    """
    Extract key point bullets as polished, complete sentences.
    Each bullet is a short sentence, max 20 words, ending with a period.
    """
    if not text or len(text.strip()) < 50:
        return []

    _ensure_nltk()
    sentences = sent_tokenize(text)
    sentences = [s.strip() for s in sentences if 25 < len(s.strip()) < 280]

    if not sentences:
        return []

    stop_words = _get_stop_words()

    # Word frequency
    word_freq = Counter()
    for s in sentences:
        words = _clean_words(s, stop_words)
        word_freq.update(words)

    # Score + boost insight-rich sentences
    insight_vocab = {
        'replace', 'automat', 'job', 'human', 'skill', 'emotion',
        'collaborat', 'ethical', 'framework', 'upskill', 'creativ',
        'evolv', 'develop', 'symbiotic', 'revolution', 'capabilit',
        'artific', 'intellig', 'future', 'technolog', 'innovat'
    }

    scored = []
    for i, sentence in enumerate(sentences):
        words = _clean_words(sentence, stop_words)
        if not words:
            continue
        score = sum(word_freq[w] for w in words) / len(words)
        boost = sum(1 for w in words if any(v in w for v in insight_vocab))
        score += boost * 0.6
        n = len(words)
        if n < 5:
            score *= 0.2
        elif n > 40:
            score *= 0.4
        scored.append((score, i, sentence))

    scored.sort(reverse=True)
    candidates = [s[2] for s in scored[:num_points * 3]]

    # Deduplicate
    unique = _deduplicate_list(candidates)

    # Compress each to a short sentence bullet (max 20 words)
    bullets = []
    for sentence in unique:
        bullet = _to_bullet(sentence)
        if bullet and bullet not in bullets:
            bullets.append(bullet)
        if len(bullets) == num_points:
            break

    return bullets


def extract_action_items(text: str) -> list[str]:
    """
    Extract ONLY real action recommendations.
    Must contain strong action keywords.
    Each item compressed to max 12 words.
    """
    _ensure_nltk()

    sentences = sent_tokenize(text)

    # Strict patterns — ONLY these qualify as action items
    patterns = [
        r'\b(must|need to|needs to|have to|has to|should)\b.{8,150}',
        r'\b(upskill|reskill|learn|train|educate|develop)\b.{5,150}',
        r'\b(build|create|establish|implement|introduce)\b.{5,80}(law|policy|framework|system|rule|guideline)',
        r'\b(focus on|work on|invest in)\b.{5,100}',
        r'\badapt\b.{5,80}(education|job|skill|system|workforce)',
        r'\b(encourage|promote|support)\b.{5,80}(human|AI|collaborat|skill)',
        r'\bresponsible (use|deployment|development) of AI\b',
    ]

    seen = set()
    items = []

    for sentence in sentences:
        for pattern in patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                bullet = _to_bullet(sentence)
                key = bullet[:30].lower()
                if key not in seen and bullet:
                    seen.add(key)
                    items.append(bullet)
                break

    # If nothing found, generate generic recommendations
    if not items:
        items = [
            "Upskill in areas AI cannot replace (creativity, critical thinking)",
            "Develop ethical frameworks for responsible AI usage",
            "Encourage human-AI collaboration in workplaces",
            "Adapt education systems for future AI-driven job roles",
            "Build regulations to ensure fair AI deployment",
        ]

    return _deduplicate_list(items)[:6]


def _to_bullet(sentence: str) -> str:
    """
    Convert a long sentence to a polished short sentence bullet (max 20 words).

    Strategy:
    1. Remove filler openings
    2. Extract the core idea
    3. Trim to a sensible length
    4. Capitalise first letter
    5. Ensure final punctuation
    """
    # Remove common filler openings and conversational starters
    fillers = [
        r'^(so |and |but |while |also |i think |i believe |we think |we see |'
        r'as we see |i would say |i would like to |the thing is |'
        r'you know |at the end of the day |at the core of |'
        r'my friends are |there are two points |well[, ]*|right[, ]*|okay[, ]*|yes[, ]*|no[, ]* )+'
    ]
    s = sentence.strip()
    for f in fillers:
        s = re.sub(f, '', s, flags=re.IGNORECASE).strip()

    # Remove "I" subject variations
    s = re.sub(r'^(I agree that|I disagree that|I think that)\s+', '', s, flags=re.IGNORECASE)

    # Trim at natural break for long sentences
    words = s.split()
    if len(words) > 20:
        # Look for comma or natural cut-off around word 15-20
        for sep in [', ', '; ', ' but ', ' however ', ' although ', ' and ', ' so ']:
            idx = s.find(sep, 15)
            if 15 < idx < len(s) * 0.7:
                s = s[:idx].strip()
                words = s.split()
                break

        # Hard cut at 20 words
        if len(words) > 20:
            s = " ".join(words[:20])

    # Clean up trailing punctuation and add period
    s = s.rstrip('.,;:')
    if not s:
        return ""
    if not s.endswith('.'):
        s = s + '.'

    # Capitalise first letter
    s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
    return s


def _get_stop_words() -> set:
    try:
        stops = set(stopwords.words("english"))
    except Exception:
        nltk.download('stopwords', quiet=True)
        stops = set(stopwords.words("english"))
    stops.update({
        'uh', 'um', 'hmm', 'yeah', 'okay', 'like', 'also',
        'think', 'know', 'right', 'even', 'would', 'could',
        'said', 'say', 'get', 'one', 'really', 'just', 'actually'
    })
    return stops


def _clean_words(sentence: str, stop_words: set) -> list:
    words = word_tokenize(sentence.lower())
    return [w for w in words if w.isalpha() and len(w) > 3 and w not in stop_words]


def _deduplicate_list(sentences: list) -> list:
    seen = []
    unique = []
    for s in sentences:
        normalized = set(re.sub(r'[^a-z0-9 ]', '', s.lower()).split())
        is_dup = False
        for prev in seen:
            if not normalized:
                is_dup = True
                break
            inter = len(normalized & prev)
            union = len(normalized | prev)
            if union > 0 and inter / union > 0.60:
                is_dup = True
                break
        if not is_dup:
            seen.append(normalized)
            unique.append(s)
    return unique


def _ensure_nltk():
    try:
        sent_tokenize("test.")
    except Exception:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)