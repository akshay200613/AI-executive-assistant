from __future__ import annotations
"""
Logging module. Tracks both agent task metrics (intent distribution)
and general API usage metrics (latency, endpoints).
"""

import json
import os
import time
from collections import Counter

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
CHAT_LOG_FILE = os.path.join(LOG_DIR, "chat_requests.jsonl")
API_LOG_FILE = os.path.join(LOG_DIR, "api_usage.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)


def log_request(session_id: str, user_text: str, intent: str,
                 tool_used: str, latency_ms: float, status: str) -> None:
    entry = {
        "timestamp": time.time(),
        "session_id": session_id,
        "user_text": user_text,
        "intent": intent,
        "tool_used": tool_used,
        "latency_ms": round(latency_ms, 2),
        "status": status,
    }
    with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_error(session_id: str, user_text: str, error: str) -> None:
    log_request(session_id, user_text, intent="error", tool_used="none",
                latency_ms=0.0, status=f"error: {error}")


def log_api_usage(endpoint: str, method: str, status_code: int, latency_ms: float) -> None:
    entry = {
        "timestamp": time.time(),
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
    }
    with open(API_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_stats() -> dict:
    stats = {
        "api": {"total_requests": 0, "avg_latency_ms": 0.0, "error_rate": 0.0, "endpoints": {}},
        "agent": {"total_tasks": 0, "task_distribution": {}}
    }

    # API Stats
    if os.path.exists(API_LOG_FILE):
        with open(API_LOG_FILE, "r", encoding="utf-8") as f:
            api_entries = [json.loads(line) for line in f if line.strip()]
        
        if api_entries:
            total_api = len(api_entries)
            errors = sum(1 for e in api_entries if e["status_code"] >= 400)
            avg_latency = sum(e["latency_ms"] for e in api_entries) / total_api
            endpoints = Counter(e["endpoint"] for e in api_entries)
            
            stats["api"] = {
                "total_requests": total_api,
                "error_rate": round(errors / total_api, 3),
                "avg_latency_ms": round(avg_latency, 2),
                "endpoints": dict(endpoints)
            }

    # Agent / Task Stats
    if os.path.exists(CHAT_LOG_FILE):
        with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
            chat_entries = [json.loads(line) for line in f if line.strip()]
        
        if chat_entries:
            intents = Counter(e["intent"] for e in chat_entries if e["intent"] != "error")
            stats["agent"] = {
                "total_tasks": len(chat_entries),
                "task_distribution": dict(intents)
            }

    return stats
