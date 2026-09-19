import streamlit as st

from core.assistant import load_docs, ask
from core.llm import LLMUnavailable
from ui import NAVY, YELLOW, header, section_label

header("Knowledge Assistant",
       "Ask about SOPs, SLAs, Strata Management Act, and renovation guidelines")

docs = load_docs()

if not docs:
    st.warning("No documents found in `data/docs/`. Add .txt files to enable the assistant.")
    st.stop()

# ── Available documents ────────────────────────────────────────────────────────
with st.expander(f"{len(docs)} documents loaded"):
    for d in docs:
        st.markdown(f"- {d['title']}")

st.write("")

# ── Question input ─────────────────────────────────────────────────────────────
if "_assistant_q" in st.session_state:
    st.session_state["_q_input"] = st.session_state.pop("_assistant_q")

section_label("Ask a Question", "fa-solid fa-circle-question")
question = st.text_input(
    "Question",
    key="_q_input",
    placeholder="E.g. What is the SLA for emergency lift breakdown? / Berapa lama SLA untuk kerosakan lif?",
)
go = st.button("Ask", type="primary", use_container_width=True)

# ── Answer ─────────────────────────────────────────────────────────────────────
if go and not question.strip():
    st.error("Please enter a question.")
elif go:
    with st.spinner("Reading the documents…"):
        try:
            answer = ask(question.strip(), docs)
        except LLMUnavailable as e:
            st.error(f"Assistant unavailable: {e}")
            st.stop()
        except ValueError as e:
            st.error(str(e))
            st.stop()

    st.markdown(
        f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
        f"padding:20px 22px;margin-top:8px'>"
        f"<div style='font-size:11px;font-weight:600;letter-spacing:1.5px;color:#6B7A99;"
        f"text-transform:uppercase;margin-bottom:12px'>Answer</div>"
        f"</div>",
        unsafe_allow_html=True)
    st.markdown(answer.text)

    if answer.citations:
        st.write("")
        section_label("Sources", "fa-solid fa-book-open")
        for c in answer.citations:
            st.markdown(
                f"<div style='background:#F4F7FB;border:1px solid #E4EBF5;border-radius:8px;"
                f"padding:8px 14px;margin-bottom:6px;font-size:13px;color:{NAVY}'>"
                f"{c.doc_title}</div>",
                unsafe_allow_html=True)

# ── Sample questions ───────────────────────────────────────────────────────────
st.write("")
section_label("Sample Questions", "fa-solid fa-list-ul")
samples = [
    "What is the SLA for a burst pipe emergency?",
    "Can a resident hang laundry on the balcony railing?",
    "What are the permitted renovation hours under the guidelines?",
    "What does the Strata Management Act say about JMB quorum?",
    "Who is responsible for common area lift maintenance?",
]
for q in samples:
    if st.button(q, use_container_width=True):
        st.session_state["_assistant_q"] = q
        st.rerun()

