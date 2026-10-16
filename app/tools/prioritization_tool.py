from __future__ import annotations
"""
Task prioritization tool. Splits a request into individual task phrases
and ranks them using simple urgency/importance keyword scoring.
"""

import re

_URGENT_WORDS = {"urgent", "asap", "critical", "immediately", "today", "deadline", "client", "security"}
_LOW_PRIORITY_WORDS = {"later", "eventually", "sometime", "minor", "optional"}


def _parse_tasks(text: str) -> list[str]:
    # Try splitting by common bullet/comma delimiters
    text = re.sub(r"^(prioritize|sort|rank|order)( these( tasks)?)?[:\s]*", "", text, flags=re.IGNORECASE)
    if "\n" in text:
        tasks = text.split("\n")
    elif "," in text:
        tasks = text.split(",")
    else:
        tasks = re.split(r"\band\b", text)

    return [t.strip("-* ") for t in tasks if t.strip("-* ")]


def _remove_context(text: str) -> str:
    return text.split("\n\nContext:\n")[0].strip()


def _score(task: str) -> int:
    lowered = task.lower()
    score = 0
    score += sum(2 for w in _URGENT_WORDS if w in lowered)
    score -= sum(1 for w in _LOW_PRIORITY_WORDS if w in lowered)
    return score


def run(input_text: str, context: dict) -> dict:
    input_text = _remove_context(input_text)
    tasks = _parse_tasks(input_text)

    if not tasks:
        return {"result": "No individual tasks detected to prioritize.", "status": "no_match"}

    ranked = sorted(tasks, key=_score, reverse=True)
    numbered = [f"{i+1}) {task}" for i, task in enumerate(ranked)]
    formatted_list = "\n".join(numbered)

    return {
        "result": f"Here is the prioritized order for your tasks:\n{formatted_list}",
        "ranked_tasks": ranked,
        "status": "success",
    }
