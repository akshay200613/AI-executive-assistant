from __future__ import annotations
"""
Short-term conversational memory. In-memory per-session store â€” swap for
Redis/DB if you need persistence across server restarts.
"""

import time
from collections import defaultdict

_SESSION_HISTORY: dict[str, list[dict]] = defaultdict(list)
_MAX_TURNS_KEPT = 10  # cap per session so memory doesn't grow unbounded


def add_turn(session_id: str, user_text: str, intent: str, result: str) -> None:
    history = _SESSION_HISTORY[session_id]
    history.append({
        "timestamp": time.time(),
        "user_text": user_text,
        "intent": intent,
        "result": result,
    })
    if len(history) > _MAX_TURNS_KEPT:
        _SESSION_HISTORY[session_id] = history[-_MAX_TURNS_KEPT:]


def get_history(session_id: str) -> list[dict]:
    return _SESSION_HISTORY.get(session_id, [])


def get_context(session_id: str) -> dict:
    """
    Builds a lightweight context dict tools can read from â€” e.g. the
    last result, so 'summarize it shorter' can refer back to prior output.
    """
    history = get_history(session_id)
    if not history:
        return {}
    last_turn = history[-1]
    return {
        "last_intent": last_turn["intent"],
        "last_result": last_turn["result"],
    }


def clear_session(session_id: str) -> None:
    _SESSION_HISTORY.pop(session_id, None)
