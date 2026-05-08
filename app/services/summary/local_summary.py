import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from app.core.settings import settings


_summarizer = None


def get_summarizer():
    global _summarizer
    if _summarizer is None:
        try:
            from transformers import pipeline
            print(f"[LocalSummary] Loading model: {settings.SUMMARY_MODEL}")
            _summarizer = pipeline(
                "summarization",
                model=settings.SUMMARY_MODEL,
                device=-1
            )
            print("[LocalSummary] Model loaded.")
        except Exception as e:
            print(f"[LocalSummary] HuggingFace load failed: {e}. Will use extractive.")
            _summarizer = "fallback"
    return _summarizer


def summarize(text: str) -> str:
    if not text or len(text.strip()) < 50:
        return text

    model = get_summarizer()

    if model != "fallback":
        try:
            return _hf_summary(text, model)
        except Exception as e:
            print(f"[LocalSummary] HuggingFace inference failed: {e}. Using extractive.")

    return _extractive_summary(text)


def _hf_summary(text: str, model) -> str:
    """HuggingFace abstractive summary — chunked for long texts."""
    max_chunk = 800
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summaries = []
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 40:
            continue
        print(f"[LocalSummary] HF chunk {i+1}/{len(chunks)}")
        result = model(chunk, max_length=120, min_length=30, do_sample=False)
        summaries.append(result[0]["summary_text"])
    joined = " ".join(summaries)
    # Run one more pass on joined if multiple chunks
    if len(chunks) > 1 and len(joined) > 100:
        try:
            final = model(joined[:800], max_length=150, min_length=40, do_sample=False)
            return final[0]["summary_text"]
        except Exception:
            pass
    return joined


def _extractive_summary(text: str, num_sentences: int = 5) -> str:
    """
    Improved extractive summary with:
    - Aggressive deduplication
    - Sentence compression
    - Coherent flow
    """
    _ensure_nltk()

    sentences = sent_tokenize(text)
    sentences = [s.strip() for s in sentences if 30 < len(s.strip()) < 300]

    if not sentences:
        return text[:400]

    if len(sentences) <= num_sentences:
        return _compress_and_join(sentences)

    stop_words = _get_stop_words()

    # Score sentences
    word_freq = Counter()
    for s in sentences:
        words = _clean_words(s, stop_words)
        word_freq.update(words)

    scores = []
    for sentence in sentences:
        words = _clean_words(sentence, stop_words)
        if not words:
            scores.append(0.0)
            continue
        score = sum(word_freq[w] for w in words) / len(words)
        # Prefer medium length
        n = len(words)
        if n < 6:
            score *= 0.3
        elif n > 40:
            score *= 0.5
        scores.append(score)

    # Pick top N in original order
    top_indices = sorted(
        sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
    )

    top_sentences = [sentences[i] for i in top_indices]

    # Deduplicate and compress
    unique = _deduplicate_sentences(top_sentences)
    return _compress_and_join(unique)


def _compress_and_join(sentences: list) -> str:
    """Join sentences into a coherent paragraph."""
    compressed = []
    for s in sentences:
        c = _compress_sentence(s)
        if c:
            compressed.append(c)
    return " ".join(compressed)


def _compress_sentence(sentence: str) -> str:
    """
    Shorten very long sentences to their core meaning.
    Keeps sentences under ~25 words.
    """
    words = sentence.split()
    if len(words) <= 22:
        return sentence

    # Try to cut at a natural break point (comma, semicolon)
    for sep in [',', ';', ' but ', ' and ', ' so ']:
        parts = sentence.split(sep, 1)
        if len(parts) == 2 and len(parts[0].split()) >= 8:
            return parts[0].strip() + "."

    # Hard cut at 22 words
    return " ".join(words[:22]) + "."


def _get_stop_words() -> set:
    try:
        stops = set(stopwords.words("english"))
    except Exception:
        nltk.download('stopwords', quiet=True)
        stops = set(stopwords.words("english"))
    stops.update({
        'uh', 'um', 'hmm', 'yeah', 'okay', 'like', 'also',
        'think', 'know', 'going', 'right', 'even', 'would',
        'could', 'said', 'say', 'get', 'one', 'really', 'just',
        'actually', 'basically', 'thing', 'things', 'way'
    })
    return stops


def _clean_words(sentence: str, stop_words: set) -> list:
    words = word_tokenize(sentence.lower())
    return [w for w in words if w.isalpha() and len(w) > 3 and w not in stop_words]


def _deduplicate_sentences(sentences: list) -> list:
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
            if union > 0 and inter / union > 0.65:
                is_dup = True
                break
        if not is_dup:
            seen.append(normalized)
            unique.append(s)
    return unique


def _ensure_nltk():
    try:
        sent_tokenize("test sentence.")
    except Exception:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)