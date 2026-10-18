"""A very small Streamlit UI.

It has three parts:
  1. A button to load the sample data.
  2. A box to ask a question.
  3. The answer, plus the graph facts and documents that were used.
"""
import os

import requests
import streamlit as st

# Where the backend API lives.
API = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Simple Graph RAG", page_icon="🧠")
st.title("🧠 Simple Graph RAG")

# A short, plain explanation for the class.
st.info(
    "This assistant answers questions in 3 steps:\n\n"
    "1. **Graph search** — finds relationships in Neo4j (who reports to whom, "
    "who works on what).\n"
    "2. **Document search** — finds similar text in the documents (pgvector).\n"
    "3. **LLM** — reads both and writes the final answer."
)

# ── 1. Load sample data ──────────────────────────────────────────────────
if st.button("① Load sample data"):
    with st.spinner("Building the graph and reading the documents…"):
        result = requests.post(f"{API}/seed", timeout=120).json()
    st.success(f"Loaded {result['people']} people and {result['documents']} documents.")

st.divider()

# ── 2. Ask a question ────────────────────────────────────────────────────
st.subheader("② Ask a question")

samples = [
    "Who reports to Rahul?",
    "Who works on the Knowledge Assistant?",
    "Who knows Python?",
    "Tell me about the CRM System.",
]
cols = st.columns(2)
for i, s in enumerate(samples):
    if cols[i % 2].button(s):
        st.session_state.question = s

question = st.text_input("Your question", value=st.session_state.get("question", ""))

if st.button("Ask", type="primary") and question:
    with st.spinner("Thinking…"):
        data = requests.post(f"{API}/ask", json={"question": question}, timeout=120).json()

    # ── 3. Show the answer and the evidence ──────────────────────────────
    st.markdown("### Answer")
    st.write(data["answer"])

    with st.expander(f"🔗 Graph facts from Neo4j ({len(data['graph_facts'])})", expanded=True):
        if data["graph_facts"]:
            for fact in data["graph_facts"]:
                st.write("• " + fact)
        else:
            st.caption("No graph facts matched this question.")

    with st.expander(f"📄 Documents from pgvector ({len(data['documents'])})"):
        for doc in data["documents"]:
            st.write(f"**{doc['source']}** (similarity {doc['score']})")
            st.caption(doc["content"])
