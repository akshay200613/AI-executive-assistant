from __future__ import annotations
"""
Lexicon-based sentiment tool. Scores text by counting positive/negative
words. Simple and dependency-free; swap in a trained classifier or
HuggingFace pipeline for higher accuracy if you have network access.
"""

import re

POSITIVE_WORDS = {
    "good", "great", "excellent", "love", "happy", "pleased", "amazing",
    "fantastic", "wonderful", "thanks", "thank", "appreciate", "positive",
    "satisfied", "impressed", "enjoy", "delighted", "awesome", "perfect",
    "helpful", "smooth", "recommend", "best",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "poor", "hate", "angry", "upset", "disappointed",
    "awful", "worst", "delay", "delayed", "issue", "problem", "complaint",
    "frustrated", "broken", "fail", "failed", "unacceptable", "refund",
    "cancel", "slow", "never",
}


def _tokenize(text: str) -> list[str]:
    # simple lowercase word tokenizer
    return re.findall(r"\b[a-z]+\b", text.lower())


def _remove_context(text: str) -> str:
    return text.split("\n\nContext:\n")[0].strip()


def run(input_text: str, context: dict) -> dict:
    input_text = _remove_context(input_text)
    tokens = _tokenize(input_text)
    pos_hits = [t for t in tokens if t in POSITIVE_WORDS]
    neg_hits = [t for t in tokens if t in NEGATIVE_WORDS]

    score = len(pos_hits) - len(neg_hits)

    if score > 0:
        label = "Positive"
    elif score < 0:
        label = "Negative"
    else:
        label = "Neutral"

    total_hits = len(pos_hits) + len(neg_hits)
    confidence = round(abs(score) / total_hits, 2) if total_hits else 0.5

    pos_str = ", ".join(pos_hits) if pos_hits else "None"
    neg_str = ", ".join(neg_hits) if neg_hits else "None"
    return {
        "result": f"The sentiment is {label} (Confidence: {confidence}).\nPositive signals: {pos_str}\nNegative signals: {neg_str}",
        "confidence": confidence,
        "positive_signals": pos_hits,
        "negative_signals": neg_hits,
        "status": "success",
    }
