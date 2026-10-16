from __future__ import annotations
"""
FAQ answering tool. TF-IDF similarity retrieval over a small internal
knowledge base. This is a lightweight RAG-lite pattern â€” swap the
_KNOWLEDGE_BASE + TF-IDF matching for ChromaDB + sentence embeddings
(same pattern as the AI Legal Adviser project) for production-grade
semantic search.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_KNOWLEDGE_BASE = [
    {"question": "What is our company's leave policy?",
     "answer": "Employees get 18 paid leave days annually."},
    {"question": "How do I raise an IT support ticket?",
     "answer": "Submit a ticket via the internal helpdesk portal under 'IT Requests'."},
    {"question": "What is the reimbursement process for travel expenses?",
     "answer": "Submit receipts via the finance portal within 15 days of travel."},
    {"question": "Who do I contact for payroll issues?",
     "answer": "Payroll queries go to the HR/payroll team via the internal portal."},
    {"question": "What is the company's remote work policy?",
     "answer": "Employees may work remotely up to 3 days per week with manager approval."},
    {"question": "How many sick leaves am I entitled to?",
     "answer": "10 paid sick leave days per year."},
    {"question": "What is the notice period for resignation?",
     "answer": "The standard notice period is 30 days."},
    {"question": "What benefits does the company offer?",
     "answer": "Health insurance, annual bonus, and a learning stipend."},
    {"question": "How do I book a meeting room?",
     "answer": "Meeting rooms are booked through the shared office calendar tool."},
    {"question": "What is the process to request new equipment?",
     "answer": "Submit an equipment request form to the admin team."},
]

_questions = [item["question"] for item in _KNOWLEDGE_BASE]
_vectorizer = TfidfVectorizer(stop_words="english")
_question_matrix = _vectorizer.fit_transform(_questions)


def _remove_context(text: str) -> str:
    return text.split("\n\nContext:\n")[0].strip()


def run(input_text: str, context: dict, threshold: float = 0.2) -> dict:
    input_text = _remove_context(input_text)
    query_vec = _vectorizer.transform([input_text])
    similarities = cosine_similarity(query_vec, _question_matrix).flatten()
    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])

    if best_score < threshold:
        return {
            "result": "I couldn't find a confident answer in the FAQ knowledge base.",
            "confidence": round(best_score, 2),
            "status": "no_match",
        }

    match = _KNOWLEDGE_BASE[best_idx]
    question = match["question"]
    answer = match["answer"]
    confidence = round(best_score, 2)
    return {
        "result": f"Based on your question, I found the following in the FAQ (Confidence: {confidence}):\n\nQ: {question}\nA: {answer}",
        "matched_question": question,
        "confidence": confidence,
        "status": "success",
    }
