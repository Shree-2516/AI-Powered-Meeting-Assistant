from transformers import pipeline
from app.core.settings import settings

_summarizer = None

def get_summarizer():
    global _summarizer
    if _summarizer is None:
        print(f"[LocalSummary] Loading model: {settings.SUMMARY_MODEL}")
        _summarizer = pipeline(
            "summarization",
            model=settings.SUMMARY_MODEL,
            device=-1  # CPU; change to 0 for GPU
        )
        print("[LocalSummary] Model loaded.")
    return _summarizer

def summarize(text: str) -> str:
    """
    Summarize text using local HuggingFace model.
    Handles long texts by chunking.
    """
    if not text or len(text.strip()) < 50:
        return text

    # BART has ~1024 token limit; chunk if needed
    max_chunk = 900  # characters per chunk (safe estimate)
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]

    summarizer = get_summarizer()
    summaries = []

    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 30:
            continue
        print(f"[LocalSummary] Summarizing chunk {i+1}/{len(chunks)}")
        result = summarizer(
            chunk,
            max_length=150,
            min_length=30,
            do_sample=False
        )
        summaries.append(result[0]["summary_text"])

    return " ".join(summaries)