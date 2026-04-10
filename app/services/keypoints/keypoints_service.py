import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import math

def extract(text: str, num_points: int = 5) -> list[str]:
    """
    Extract key points using TextRank-style sentence scoring.
    Returns top N sentences as key points.
    """
    if not text or len(text.strip()) < 50:
        return [text] if text else []

    sentences = sent_tokenize(text)

    if len(sentences) <= num_points:
        return [s.strip() for s in sentences]

    # Score sentences by word frequency (TF-based TextRank simplified)
    scored = _score_sentences(sentences)
    
    # Sort by score but preserve order for readability
    top_indices = sorted(
        sorted(range(len(scored)), key=lambda i: scored[i], reverse=True)[:num_points]
    )

    key_points = [sentences[i].strip() for i in top_indices]
    return key_points


def extract_action_items(text: str) -> list[str]:
    """
    Extract action items by looking for task-like patterns.
    """
    action_patterns = [
        r'\b(will|shall|should|need to|needs to|must|going to|have to|has to)\b.{5,80}',
        r'\b(action item|follow up|follow-up|next step|task|todo|to-do|assign)\b.{5,80}',
        r'\b(deadline|by [A-Z][a-z]+day|by end of|before next)\b.{5,60}',
    ]
    
    sentences = sent_tokenize(text)
    action_items = []
    seen = set()

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15 or len(sentence) > 200:
            continue
        
        for pattern in action_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                # Deduplicate similar items
                key = sentence[:40].lower()
                if key not in seen:
                    seen.add(key)
                    action_items.append(sentence)
                break

    return action_items[:8]  # Cap at 8 action items


def _score_sentences(sentences: list[str]) -> list[float]:
    """Score sentences using word frequency."""
    try:
        stop_words = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        stop_words = set(stopwords.words("english"))

    # Count word frequencies across all sentences
    word_freq = Counter()
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [w for w in words if w.isalpha() and w not in stop_words]
        word_freq.update(words)

    # Score each sentence
    scores = []
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [w for w in words if w.isalpha() and w not in stop_words]
        
        if not words:
            scores.append(0.0)
            continue

        score = sum(word_freq[w] for w in words) / len(words)
        # Penalize very short and very long sentences
        length_penalty = 1.0
        if len(words) < 5:
            length_penalty = 0.5
        elif len(words) > 40:
            length_penalty = 0.7

        scores.append(score * length_penalty)

    return scores