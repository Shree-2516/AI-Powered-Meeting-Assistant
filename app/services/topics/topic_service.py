import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def extract(text: str, num_topics: int = 8) -> list[str]:
    """
    Extract main topics from text using TF-IDF.
    Returns top N topic keywords.
    """
    if not text or len(text.strip()) < 30:
        return []

    # Clean text
    clean = _clean_text(text)

    try:
        stop_words = list(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        stop_words = list(stopwords.words("english"))

    # Add meeting-specific stop words
    meeting_stops = [
        "yeah", "okay", "right", "like", "think", "know",
        "going", "said", "thing", "people", "time", "way",
        "um", "uh", "hmm", "actually", "basically", "kind"
    ]
    all_stops = stop_words + meeting_stops

    try:
        # Use TF-IDF on the full text treated as one document
        # Split into sentences as mini-documents for better scoring
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(clean)
        
        if len(sentences) < 2:
            sentences = [clean]

        vectorizer = TfidfVectorizer(
            stop_words=all_stops,
            ngram_range=(1, 2),   # single words + bigrams
            max_features=100,
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()
        
        # Sum scores across all sentences
        scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
        
        # Get top indices
        top_indices = scores.argsort()[::-1][:num_topics]
        topics = [feature_names[i].title() for i in top_indices]
        
        # Filter out single-char topics
        topics = [t for t in topics if len(t) > 2]
        
        return topics[:num_topics]

    except Exception as e:
        print(f"[TopicService] TF-IDF failed: {e}. Falling back to frequency method.")
        return _fallback_topics(clean, num_topics)


def _clean_text(text: str) -> str:
    """Remove filler words, lowercase, strip special chars."""
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _fallback_topics(text: str, num_topics: int) -> list[str]:
    """Simple word frequency fallback."""
    try:
        stop_words = set(stopwords.words("english"))
    except Exception:
        stop_words = set()

    words = word_tokenize(text.lower())
    words = [w for w in words if w.isalpha() and len(w) > 3 and w not in stop_words]

    from collections import Counter
    freq = Counter(words)
    return [w.title() for w, _ in freq.most_common(num_topics)]