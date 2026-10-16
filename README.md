# AI Executive Assistant

An agentic AI assistant for a small team/startup: understands a natural-language
request, detects intent, routes to the right tool, executes it, and responds —
with short-term memory and basic monitoring.

## Architecture

```
User Query → Intent Detection → Task Planner → Tool Selection → Task Execution → Response Generation
```

- **Intent detection**: TF-IDF + Logistic Regression, trained on `data/aea_dataset.csv`
- **Planner**: rule-based; splits compound requests ("summarize this and draft a reply")
  and chains tool calls, passing output from one tool into the next
- **Tools**: email drafting, summarization, sentiment analysis, reminders, FAQ
  answering, document search, task prioritization — each behind a common
  `run(input_text, context) -> dict` interface
- **Memory**: in-memory per-session history for follow-up context
- **Logging**: JSONL request log + `/stats` endpoint (avg latency, error rate,
  task distribution) — swap for Prometheus/Grafana if you want dashboards
- **UI**: Streamlit chat interface showing detected intent + tool used per turn

## Local setup

```bash
pip install -r requirements.txt
python scripts/train_classifier.py        # trains models/intent_classifier.pkl

# terminal 1
uvicorn app.main:app --reload --port 8000

# terminal 2
streamlit run ui/streamlit_app.py
```

Open the Streamlit URL it prints (usually http://localhost:8501).

## Docker

```bash
docker-compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:8501

## API

| Endpoint | Method | Description |
|---|---|---|
| `/chat` | POST | `{session_id, message}` → `{response, intent, tool_used, latency_ms}` |
| `/stats` | GET | Aggregated monitoring stats |
| `/history/{session_id}` | GET | Session's conversation history |
| `/health` | GET | Liveness check |

## Deployment (free tier)

Any of these work with the Dockerfile as-is:
- **Render** — connect the repo, it auto-detects the Dockerfile
- **Railway** — `railway up` from the project root
- **Hugging Face Spaces** (Docker SDK) — push the repo, set the Space to Docker mode

After deploying, update `API_URL` in the Streamlit service's environment to the
API's public URL.

## Known limitations (by design, given the 3-day scope)

- Intent classifier is trained on ~15 examples/category — good enough to prove
  the pipeline, but expect occasional misroutes on short/ambiguous phrasing.
  Add more labeled examples to `data/aea_dataset.csv` and retrain to improve.
- `document_search` / `faq_answering` use TF-IDF retrieval over a small
  built-in knowledge base rather than a full RAG stack. Swap in ChromaDB +
  sentence embeddings for semantic search at scale (same pattern as a
  ChromaDB-based RAG app, just pointed at your own docs).
- Memory and reminders are in-process (lost on restart) — move to Redis/a
  database for persistence in production.

## Bonus features you could add

- Swap document_search/faq_tool for a real ChromaDB + embeddings RAG pipeline
- Autonomous task chaining beyond 2 steps
- Scheduling integration for reminders (e.g. APScheduler)
- PDF upload + parsing for document_search
