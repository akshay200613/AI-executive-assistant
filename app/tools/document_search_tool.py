from __future__ import annotations
"""
Document search tool. Splits a document into paragraphs and returns the
paragraph(s) most relevant to the query via TF-IDF cosine similarity.

context["document_text"] should hold the full document to search.
Falls back to a small sample contract for demo purposes if none is given.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_SAMPLE_DOCUMENT = """
1. Scope of Work. The vendor agrees to provide the services described in Exhibit A.
2. Payment Terms. Invoices are due net-30 from the date of receipt.
3. Confidentiality. Both parties agree to keep shared information confidential for 5 years.
4. Termination. Either party may terminate this agreement with 30 days written notice.
5. Data Privacy. Customer data will be handled in accordance with applicable data protection law.
6. Refunds. Refund requests are processed within 14 business days of approval.
"""


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r"\n+", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _remove_context(text: str) -> str:
    return text.split("\n\nContext:\n")[0].strip()

def run(input_text: str, context: dict, top_k: int = 1) -> dict:
    input_text = _remove_context(input_text)
    document_text = context.get("document_text", _SAMPLE_DOCUMENT)
    paragraphs = _split_paragraphs(document_text)

    if not paragraphs:
        return {"result": "No document content available to search.", "status": "no_match"}

    vectorizer = TfidfVectorizer(stop_words="english")
    para_matrix = vectorizer.fit_transform(paragraphs)
    query_vec = vectorizer.transform([input_text])

    similarities = cosine_similarity(query_vec, para_matrix).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]

    matches = [
        {"text": paragraphs[i], "score": round(float(similarities[i]), 2)}
        for i in top_indices
    ]

    if matches:
        score = matches[0]["score"]
        text = matches[0]["text"]
        result_text = f"Found relevant section (Score: {score}):\n\n\"{text}\""
    else:
        result_text = "No relevant section found."

    return {
        "result": result_text,
        "matches": matches,
        "status": "success",
    }
