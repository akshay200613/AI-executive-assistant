"""
Streamlit chat UI for the AI Executive Assistant.

Run:
    streamlit run ui/streamlit_app.py

Expects the FastAPI backend running at API_URL (default localhost:8000,
override with the API_URL environment variable for Docker/deployment).
"""

import os
import uuid
import time
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Executive Assistant", page_icon="🧠", layout="centered")
st.title("🧠 AI Executive Assistant")
st.caption("Ask it to draft emails, summarize docs, check sentiment, set reminders, answer FAQs, search documents, or prioritize tasks.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (role, text, meta)

# Real-time response generator function
def stream_response(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

for role, text, meta in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(text)
        if meta and meta.get("steps"):
            with st.expander(f"Task Breakdown ({len(meta['steps'])} steps)"):
                for i, step in enumerate(meta["steps"]):
                    st.markdown(f"**Step {i+1}:** {step['intent'].replace('_', ' ').title()} (Confidence: {step['confidence']})")
                    st.json(step['tool_output'])
        elif meta:
            st.caption(f"Intent: `{meta.get('intent')}` · Tool: `{meta.get('tool_used')}` · {meta.get('latency_ms')} ms")

user_input = st.chat_input("Type a request...")

if user_input:
    st.session_state.chat_history.append(("user", user_input, None))
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"session_id": st.session_state.session_id, "message": user_input},
                    timeout=30,
                )
                data = resp.json()
                
                # Real-time streaming effect
                message_placeholder = st.empty()
                full_response = ""
                for chunk in stream_response(data["response"]):
                    full_response += chunk
                    message_placeholder.write(full_response + "▌")
                message_placeholder.write(full_response)
                
                # Task Visualization
                if data.get("steps"):
                    with st.expander(f"Task Breakdown ({len(data['steps'])} steps)"):
                        for i, step in enumerate(data["steps"]):
                            st.markdown(f"**Step {i+1}:** {step['intent'].replace('_', ' ').title()} (Confidence: {step['confidence']})")
                            st.json(step['tool_output'])
                else:
                    st.caption(f"Intent: `{data['intent']}` · Tool: `{data['tool_used']}` · {data['latency_ms']} ms")
                    
                st.session_state.chat_history.append(("assistant", data["response"], data))
            except Exception as e:
                st.error(f"Request failed: {e}")

with st.sidebar:
    st.header("Session")
    st.text(f"ID: {st.session_state.session_id[:8]}")
    if st.button("New session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.experimental_rerun()

    st.header("Stats")
    if st.button("Refresh stats"):
        try:
            stats = requests.get(f"{API_URL}/stats", timeout=10).json()
            st.json(stats)
        except Exception as e:
            st.error(f"Could not fetch stats: {e}")

    st.header("Previous Chats")
    # Show history of just the user's queries in the sidebar
    user_queries = [text for role, text, meta in st.session_state.chat_history if role == "user"]
    if not user_queries:
        st.caption("No chats yet.")
    else:
        for q in reversed(user_queries):
            st.caption(f"💬 {q}")
