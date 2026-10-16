from __future__ import annotations
"""
Tool registry. This is the dynamic tool-selection layer: the router looks
up the detected intent here and calls the matching tool's run() function.

Every tool exposes the same interface:
    def run(input_text: str, context: dict) -> dict
so the router never needs to know a tool's internals.
"""

from . import (
    email_tool,
    summarizer_tool,
    sentiment_tool,
    reminder_tool,
    faq_tool,
    document_search_tool,
    prioritization_tool,
)

TOOL_REGISTRY = {
    "email_generation": email_tool.run,
    "text_summarization": summarizer_tool.run,
    "sentiment_analysis": sentiment_tool.run,
    "reminder_creation": reminder_tool.run,
    "faq_answering": faq_tool.run,
    "document_search": document_search_tool.run,
    "task_prioritization": prioritization_tool.run,
}


def get_tool(intent: str):
    """Returns the tool function for an intent, or None if unmapped."""
    return TOOL_REGISTRY.get(intent)
