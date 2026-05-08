import re
from nltk.tokenize import sent_tokenize
import nltk

FILLER_WORDS = [
    r'\buh\b', r'\bum\b', r'\bhmm\b', r'\buhh\b', r'\bumm\b',
    r'\byou know\b', r'\bi mean\b', r'\blike uh\b', r'\buh like\b',
    r'\bso uh\b', r'\band uh\b', r'\bbut uh\b', r'\bi think uh\b',
]

MODERATOR_PATTERNS = [
    r'your topic for (the )?group discussion is[\w\s,\.\?\!]*',
    r'you have about \d+ minutes to prepare[\w\s,\.\?\!]*',
    r'good (morning|afternoon|evening)[\w\s,\.\?\!]{0,40}',
    r'(please|now) (begin|start|continue) (the )?discussion[\w\s,\.\?\!]*',
    r"we('ll| will) continue with the discussion[\w\s,\.\?\!]*",
    r'hello everyone[\w\s,\.\?\!]{0,40}',
]


def clean(text: str) -> str:
    """
    Full cleaning pipeline:
    1. Remove moderator/announcer lines
    2. Remove filler words
    3. Fix common transcription noise
    4. Deduplicate sentences
    5. Return clean text
    """
    if not text:
        return text

    # Step 1: Remove moderator lines
    text = _remove_moderator_lines(text)

    # Step 2: Remove filler words
    text = _remove_fillers(text)

    # Step 3: Fix spacing and punctuation noise
    text = _fix_noise(text)

    # Step 4: Deduplicate repeated sentences
    text = _deduplicate(text)

    return text.strip()


def get_sentences(text: str) -> list[str]:
    """Return clean, deduplicated sentence list."""
    try:
        sentences = sent_tokenize(text)
    except Exception:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        sentences = sent_tokenize(text)
    return sentences


def _remove_moderator_lines(text: str) -> str:
    for pattern in MODERATOR_PATTERNS:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    return text


def _remove_fillers(text: str) -> str:
    for pattern in FILLER_WORDS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Clean double spaces left behind
    text = re.sub(r' {2,}', ' ', text)
    return text


def _fix_noise(text: str) -> str:
    # Remove stutter repetitions like "the the" or "and and"
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    # Fix spacing before punctuation
    text = re.sub(r' ([,\.\?\!])', r'\1', text)
    # Ensure space after punctuation
    text = re.sub(r'([,\.\?\!])(\w)', r'\1 \2', text)
    return text


def _deduplicate(text: str) -> str:
    """Remove sentences that are nearly identical to a previous one."""
    try:
        sentences = sent_tokenize(text)
    except Exception:
        return text

    seen = []
    unique = []

    for sentence in sentences:
        s = sentence.strip()
        if len(s) < 15:
            continue

        # Normalize for comparison
        normalized = re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
        normalized_words = set(normalized.split())

        # Check similarity against already accepted sentences
        is_duplicate = False
        for prev in seen:
            prev_words = set(prev.split())
            if len(normalized_words) == 0:
                is_duplicate = True
                break
            # Jaccard similarity
            intersection = len(normalized_words & prev_words)
            union = len(normalized_words | prev_words)
            similarity = intersection / union if union > 0 else 0
            if similarity > 0.72:  # 72% similar = duplicate
                is_duplicate = True
                break

        if not is_duplicate:
            seen.append(normalized)
            unique.append(s)

    return ' '.join(unique)