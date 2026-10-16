from __future__ import annotations
"""
Reminder tool. Extracts a rough "when" phrase from the request with
simple pattern matching and stores the reminder in-memory (swap for a
real DB / scheduler in production).
"""

import re
import uuid

_REMINDERS: dict[str, dict] = {}  # in-memory store, keyed by reminder id

_TIME_PATTERNS = [
    r"\btomorrow\b(?: at [\d:apm ]+)?",
    r"\btommorrow\b(?: at [\d:apm ]+)?",
    r"\btomorr\b(?: at [\d:apm ]+)?",
    r"\btmrw\b(?: at [\d:apm ]+)?",
    r"\bnext (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month)\b",
    r"\bevery (?:day|week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\bin \d+ days?\b",
    r"\bat \d{1,2}(:\d{2})? ?[ap]m\b",
    r"\bon (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
]

def _remove_context(text: str) -> str:
    return text.split("\n\nContext:\n")[0].strip()

def _extract_time_phrase(text: str) -> str:
    lowered = text.lower()
    for pattern in _TIME_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            return match.group(0)
    return "unspecified time - please confirm"

def _extract_task(text: str, time_phrase: str) -> str:
    cleaned = _remove_context(text)
    cleaned = re.sub(r"^(remind (me|the team)( about| to)?|set a reminder (to|for)?)\s*", "", cleaned, flags=re.IGNORECASE)
    if time_phrase != "unspecified time - please confirm":
        cleaned = cleaned.replace(time_phrase, "")
    return cleaned.strip(" .") or text.strip()


def run(input_text: str, context: dict) -> dict:
    time_phrase = _extract_time_phrase(input_text)
    task = _extract_task(input_text, time_phrase)
    is_recurring = bool(re.search(r"\bevery\b", input_text.lower()))

    reminder_id = str(uuid.uuid4())[:8]
    reminder = {
        "id": reminder_id,
        "task": task,
        "when": time_phrase,
        "recurring": is_recurring,
    }
    _REMINDERS[reminder_id] = reminder

    return {
        "result": f"I have set a reminder for you to '{task}'. This is scheduled for {time_phrase}.",
        "reminder": reminder,
        "status": "success",
    }
