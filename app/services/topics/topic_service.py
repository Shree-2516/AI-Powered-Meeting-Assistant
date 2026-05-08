import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import numpy as np


# Curated topic seed phrases — these map raw keywords to clean topic labels
TOPIC_MAP = {
    'replac': 'Job Automation & Replacement',
    'job': 'Future of Jobs',
    'work': 'Future of Work',
    'artificial intelligence': 'Artificial Intelligence',
    'human': 'Human vs AI Capability',
    'emotion': 'AI Emotions & Empathy',
    'feel': 'AI Emotions & Empathy',
    'symbiotic': 'Human-AI Collaboration',
    'collaborat': 'Human-AI Collaboration',
    'ethical': 'AI Ethics & Governance',
    'framework': 'AI Ethics & Governance',
    'law': 'AI Regulation & Policy',
    'regulation': 'AI Regulation & Policy',
    'revolution': 'Industrial Revolution Analogy',
    'industrial': 'Industrial Revolution Analogy',
    'skill': 'Human Skill Development',
    'upskill': 'Human Skill Development',
    'creativ': 'Human Creativity',
    'brain': 'AI vs Human Intelligence',
    'neural': 'Neural Technology',
    'robot': 'Robotics',
    'data': 'AI Data & Learning',
    'develop': 'AI Development',
    'future': 'Future Predictions',
    'evolution': 'Technology Evolution',
    'automat': 'Job Automation & Replacement',
    'machine': 'Machine Learning',
    'labor': 'Labor & Employment',
    'capacit': 'AI Capability',
}


def extract(text: str, num_topics: int = 8) -> list[str]:
    """
    Extract meaningful topic phrases — not random single words.
    Uses keyword matching against curated topic map first,
    then falls back to TF-IDF bigrams.
    """
    if not text or len(text.strip()) < 30:
        return []

    # Step 1: Curated topic detection (highest quality)
    curated = _extract_curated_topics(text)

    # Step 2: TF-IDF bigram topics (fills remaining slots)
    tfidf_topics = _extract_tfidf_topics(text, num_topics * 2)

    # Merge: curated first, then TF-IDF for extras
    final = list(curated)
    for t in tfidf_topics:
        if t not in final and len(final) < num_topics:
            final.append(t)

    return final[:num_topics]


def _extract_curated_topics(text: str) -> list[str]:
    """Match text against known topic keywords."""
    text_lower = text.lower()
    found = []
    seen_labels = set()

    for keyword, label in TOPIC_MAP.items():
        if label not in seen_labels and keyword in text_lower:
            found.append(label)
            seen_labels.add(label)

    return found


def _extract_tfidf_topics(text: str, num: int) -> list[str]:
    """Extract important bigram/trigram phrases using TF-IDF."""
    try:
        stop_words = list(stopwords.words("english"))
    except Exception:
        nltk.download('stopwords', quiet=True)
        stop_words = list(stopwords.words("english"))

    extra_stops = [
        'uh', 'um', 'yeah', 'okay', 'like', 'also', 'think',
        'know', 'going', 'thing', 'people', 'right', 'even',
        'would', 'could', 'said', 'say', 'see', 'get', 'one',
        'will', 'also', 'actually', 'basically', 'really', 'just'
    ]
    all_stops = stop_words + extra_stops

    try:
        try:
            sentences = sent_tokenize(text)
        except Exception:
            nltk.download('punkt_tab', quiet=True)
            sentences = sent_tokenize(text)

        if len(sentences) < 2:
            sentences = [text]

        vectorizer = TfidfVectorizer(
            stop_words=all_stops,
            ngram_range=(2, 3),   # bigrams and trigrams only
            max_features=80,
            min_df=1
        )

        matrix = vectorizer.fit_transform(sentences)
        features = vectorizer.get_feature_names_out()
        scores = np.asarray(matrix.sum(axis=0)).flatten()
        top_indices = scores.argsort()[::-1][:num]

        topics = []
        for i in top_indices:
            phrase = features[i].title()
            # Filter: must be at least 2 words and meaningful length
            if len(phrase.split()) >= 2 and len(phrase) > 5:
                topics.append(phrase)

        return topics[:num]

    except Exception as e:
        print(f"[TopicService] TF-IDF failed: {e}")
        return _fallback_topics(text, num)


def _fallback_topics(text: str, num: int) -> list[str]:
    """Simple noun-phrase frequency fallback."""
    try:
        stop_words = set(stopwords.words("english"))
    except Exception:
        stop_words = set()

    words = word_tokenize(text.lower())
    words = [w for w in words if w.isalpha() and len(w) > 4 and w not in stop_words]
    freq = Counter(words)
    return [w.title() for w, _ in freq.most_common(num)]