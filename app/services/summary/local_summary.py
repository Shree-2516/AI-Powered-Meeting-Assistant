import re
from app.core.settings import settings

_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        print(f"[LocalSummary] Loading model: {settings.SUMMARY_MODEL}")
        from transformers import pipeline
        _summarizer = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",  # smaller, faster, works offline
            device=-1
        )
        print("[LocalSummary] Model loaded.")
    return _summarizer

def summarize(text: str) -> str:
    if not text or len(text.strip()) < 50:
        return text

    # Try HuggingFace first
    try:
        max_chunk = 800
        chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
        summarizer = get_summarizer()
        summaries = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 30:
                continue
            print(f"[LocalSummary] Summarizing chunk {i+1}/{len(chunks)}")
            result = summarizer(
                chunk,
                max_length=130,
                min_length=30,
                do_sample=False
            )
            summaries.append(result[0]["summary_text"])
        return " ".join(summaries)

    except Exception as e:
        print(f"[LocalSummary] HuggingFace failed: {e}. Using extractive fallback.")
        return _extractive_summary(text)


def _extractive_summary(text: str, num_sentences: int = 4) -> str:
    """
    Simple extractive summary — no ML model needed.
    Picks the most important sentences by word frequency.
    """
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from collections import Counter

    try:
        sentences = sent_tokenize(text)
    except Exception:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        sentences = sent_tokenize(text)

    if len(sentences) <= num_sentences:
        return text

    try:
        stop_words = set(stopwords.words("english"))
    except Exception:
        nltk.download('stopwords', quiet=True)
        stop_words = set()

    words = word_tokenize(text.lower())
    words = [w for w in words if w.isalpha() and w not in stop_words]
    freq = Counter(words)

    scores = []
    for sentence in sentences:
        s_words = word_tokenize(sentence.lower())
        s_words = [w for w in s_words if w.isalpha() and w not in stop_words]
        score = sum(freq[w] for w in s_words) / max(len(s_words), 1)
        scores.append(score)

    top_indices = sorted(
        sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
    )

    return " ".join(sentences[i] for i in top_indices)