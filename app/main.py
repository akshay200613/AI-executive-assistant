from __future__ import annotations
"""
FastAPI entrypoint for the AI Executive Assistant.

Run locally:
    uvicorn app.main:app --reload --port 8000

Endpoints:
    POST /chat   -> main agent pipeline
    GET  /stats  -> monitoring dashboard data
    GET  /health -> liveness check
"""

import time
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import memory, logger
from app.planner import plan_and_execute

app = FastAPI(title="AI Executive Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware for API Tracking ---
@app.middleware("http")
async def track_api_usage(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency_ms = (time.time() - start_time) * 1000
        logger.log_api_usage(request.url.path, request.method, status_code, latency_ms)
    return response
# -----------------------------------


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    tool_used: str
    latency_ms: float
    steps: list = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.time()

    try:
        mem_context = memory.get_context(req.session_id)
        plan_result = plan_and_execute(req.message, mem_context)

        primary_step = plan_result["steps"][0]
        intent = primary_step["intent"]
        tool_used = ",".join(s["intent"] for s in plan_result["steps"])
        final_response = plan_result["final_response"]

        memory.add_turn(req.session_id, req.message, intent, final_response)

        latency_ms = (time.time() - start) * 1000
        logger.log_request(req.session_id, req.message, intent, tool_used, latency_ms, "success")

        return ChatResponse(
            response=final_response,
            intent=intent,
            tool_used=tool_used,
            latency_ms=round(latency_ms, 2),
            steps=plan_result["steps"],
        )

    except Exception as e:
        logger.log_error(req.session_id, req.message, str(e))
        traceback.print_exc()
        latency_ms = (time.time() - start) * 1000
        return ChatResponse(
            response="Something went wrong processing that request.",
            intent="error",
            tool_used="none",
            latency_ms=round(latency_ms, 2),
            steps=[],
        )


@app.get("/stats")
def stats():
    return logger.get_stats()


@app.get("/history/{session_id}")
def history(session_id: str):
    return {"history": memory.get_history(session_id)}
