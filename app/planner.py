from __future__ import annotations
"""
Task planner. Rule-based (no LLM needed for a 3-day scope):
  - single intent  -> run one tool
  - compound request ("summarize this and draft a reply") -> run tools
    in sequence, feeding each tool's output into the next as extra context
"""

from app.intent_classifier import predict_intent_with_confidence, split_compound_request
from app.tools import get_tool


def plan_and_execute(user_text: str, memory_context: dict) -> dict:
    """
    Returns:
        {
          "steps": [ {intent, confidence, tool_output}, ... ],
          "final_response": str,
        }
    """
    sub_requests = split_compound_request(user_text)
    steps = []
    running_context = dict(memory_context)  # carry conversational memory forward

    for sub_text in sub_requests:
        intent, confidence = predict_intent_with_confidence(sub_text)
        tool_fn = get_tool(intent)

        if tool_fn is None:
            step_result = {"result": f"No tool available for intent '{intent}'.", "status": "unmapped_intent"}
        else:
            # Handle short-term conversational memory: use last_result context for follow-up questions
            effective_text = sub_text
            # Only append context if it's a short command that likely refers to previous output
            if len(sub_text.split()) <= 6 and running_context.get("last_result"):
                effective_text = f"{sub_text}\n\nContext:\n{running_context['last_result']}"
                
            step_result = tool_fn(effective_text, running_context)

        # feed this step's output forward so a chained tool can use it
        # (e.g. summarizer's output becomes the email tool's "summary")
        running_context["summary"] = step_result.get("result", "")
        running_context["last_result"] = step_result.get("result", "")

        steps.append({
            "sub_request": sub_text,
            "intent": intent,
            "confidence": round(confidence, 2),
            "tool_output": step_result,
        })

    final_response = _compose_response(steps)
    return {"steps": steps, "final_response": final_response}


def _compose_response(steps: list[dict]) -> str:
    if len(steps) == 1:
        return steps[0]["tool_output"].get("result", "No result produced.")

    parts = [f"Step {i+1} ({s['intent']}): {s['tool_output'].get('result', '')}"
             for i, s in enumerate(steps)]
    return "\n".join(parts)
