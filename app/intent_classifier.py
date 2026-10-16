from __future__ import annotations
"""
Loads the trained intent classifiers and exposes predict_intent().
Supports TF-IDF + Logistic Regression, Naive Bayes, and Sentence Transformers.
Defaults to Sentence Transformers.
"""

import os
import re
import joblib
from sentence_transformers import SentenceTransformer

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "intent_classifier.pkl")

_ACTION_VERBS = r"draft|write|compose|summarize|remind|set|check|analyze|find|search|prioritize|rank|sort"
_SPLIT_PATTERN = re.compile(
    rf"\s+(?:and then|then|and)\s+(?=(?:{_ACTION_VERBS})\b)",
    flags=re.IGNORECASE,
)

_models = None
_embedder = None


def _load():
    global _models, _embedder
    if _models is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"No trained model found at {MODEL_PATH}. "
                "Run scripts/train_classifier.py first."
            )
        _models = joblib.load(MODEL_PATH)
        # Load the sentence transformer only once when needed
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _models, _embedder


def predict_intent_with_confidence(text: str, model_type: str = "st_lr") -> tuple[str, float]:
    """
    Returns (intent, confidence). 
    model_type can be 'st_lr' (Sentence Transformers + LR), 'tfidf_lr', or 'tfidf_nb'.
    """
    models, embedder = _load()
    
    if model_type == "st_lr":
        vec = embedder.encode([text])
        clf = models["st_lr_model"]
    else:
        vec = models["tfidf_vectorizer"].transform([text])
        clf = models["lr_model"] if model_type == "tfidf_lr" else models["nb_model"]
        
    proba = clf.predict_proba(vec)[0]
    classes = clf.classes_
    best_idx = proba.argmax()
    return classes[best_idx], float(proba[best_idx])


def predict_intent(text: str, model_type: str = "st_lr") -> str:
    intent, _ = predict_intent_with_confidence(text, model_type)
    return intent


def split_compound_request(text: str) -> list[str]:
    parts = _SPLIT_PATTERN.split(text)
    return [p.strip() for p in parts if p.strip()]
