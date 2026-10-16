from __future__ import annotations
"""
Extractive summarizer. Ranks sentences by TF-IDF importance and returns
the top N â€” no external model download required, so it works fully
offline/in-container. Swap in a HuggingFace pipeline later if you have
network access to the model hub.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s]

def _clean_input(text: str) -> str:
    clean = re.sub(r"^(please\s+)?(summarize|summarise)(\s+(the\s+following|this|it))?[:,\s]*", "", text, flags=re.IGNORECASE)
    return clean.strip()

def run(input_text: str, context: dict, num_sentences: int = 3) -> dict:
    input_text = _clean_input(input_text)
    sentences = _split_sentences(input_text)

    if len(sentences) <= num_sentences:
        summary = " ".join(sentences)
        return {"result": f"Here is a summary of the provided text:\n\n{summary}", "status": "success", "note": "input already short"}

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(sentences)

    # Score each sentence by the sum of its TF-IDF weights
    scores = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
    top_idx = sorted(np.argsort(scores)[-num_sentences:])  # keep original order

    bullets = [f"- {sentences[i]}" for i in top_idx]
    summary = "\n".join(bullets)

    return {
        "result": f"Here is a summary of the provided text:\n{summary}",
        "sentences_used": len(top_idx),
        "sentences_total": len(sentences),
        "status": "success",
    }
