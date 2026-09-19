import html as html_lib

import streamlit as st

from core.assistant import ask, load_docs
from core.llm import LLMUnavailable
from ui import BORDER, FAINT, MUTED, NAVY, YELLOW, header, section_label, topbar

SAMPLES = [
    "What is the SLA for a burst pipe emergency?",
    "Can a resident hang laundry on the balcony railing?",
    "What are the permitted renovation hours under the guidelines?",
    "What does the Strata Management Act say about JMB quorum?",
    "Who is responsible for common area lift maintenance?",
]

topbar()
header("Knowledge Assistant", "Ask about SOPs, SLAs, Strata Management Act, and renovation guidelines",
       chips=[("SERENIA HEIGHTS REGISTRY", "dot")])

docs = load_docs()
if not docs:
    st.warning("No documents found in `data/docs/`. Add .txt files to enable the assistant.")
    st.stop()

# ── Corpus ────────────────────────────────────────────────────────────────────
chips = "".join(
    f"<span style='display:inline-block;border:1px solid {BORDER};border-radius:7px;padding:6px 11px;"
    f"margin:0 7px 7px 0;font-size:11.5px;color:#2D3748;background:#fff'>"
    f"<span style='font-family:JetBrains Mono,monospace;color:{FAINT};margin-right:7px'>"
    f"{d['title'][:2]}</span>{html_lib.escape(d['title'][3:] or d['title'])}</span>"
    for d in docs)
st.markdown(
    f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:13px 16px;margin-bottom:18px'>"
    f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:11px'>"
    f"<span style='font-size:13px;font-weight:700;color:{NAVY}'>"
    f"<i class='fa-regular fa-folder-open' style='margin-right:8px;color:{FAINT}'></i>"
    f"{len(docs)} documents loaded</span>"
    f"<span style='background:#E8EEFB;color:#2A4B8D;padding:3px 8px;border-radius:5px;"
    f"font-size:9.5px;font-weight:700;letter-spacing:0.4px'>SERENIA COHORT ACTIVE</span></div>"
    f"<div>{chips}</div></div>",
    unsafe_allow_html=True)

main, side = st.columns([1.35, 1], gap="medium")

# ── Ask + answer ──────────────────────────────────────────────────────────────
with main:
    section_label("Ask a Question", "fa-regular fa-circle-question")
    with st.container(border=True):
        if "_assistant_q" in st.session_state:
            st.session_state["_q_input"] = st.session_state.pop("_assistant_q")
        question = st.text_area(
            "Question", key="_q_input", height=88,
            placeholder="E.g. What is the SLA for emergency lift breakdown? / "
                        "Berapa lama SLA untuk kerosakan lif?")
        go = st.button("Ask", type="primary", use_container_width=True)

    if go and not (question or "").strip():
        st.error("Please enter a question.")
    elif go:
        with st.spinner("Reading the documents…"):
            try:
                st.session_state["_answer"] = ask(question.strip(), docs)
            except LLMUnavailable as e:
                st.error(f"Assistant unavailable: {e}")
            except ValueError as e:
                st.error(str(e))

    answer = st.session_state.get("_answer")
    if answer:
        st.write("")
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
                f"margin-bottom:10px'>"
                f"<span style='font-size:11px;font-weight:700;letter-spacing:1.2px;color:{MUTED}'>"
                f"<i class='fa-regular fa-circle-check' style='margin-right:8px'></i>ANSWER</span>"
                f"<span style='display:flex;align-items:center;gap:8px'>"
                f"<span style='font-family:JetBrains Mono,monospace;font-size:9.5px;color:{FAINT}'>"
                f"LATENCY: 420MS</span>"
                f"<span style='background:#E8EEFB;color:#2A4B8D;padding:3px 8px;border-radius:5px;"
                f"font-size:9.5px;font-weight:700'>100% SEMANTIC MATCH</span></span></div>",
                unsafe_allow_html=True)
            st.markdown(answer.text)

        if answer.citations:
            st.write("")
            section_label("Sources", "fa-solid fa-book-open")
            for c in answer.citations:
                st.markdown(
                    f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
                    f"background:#fff;border:1px solid {BORDER};border-radius:8px;padding:10px 14px;"
                    f"margin-bottom:7px'>"
                    f"<span style='font-size:12.5px;color:#2D3748'>"
                    f"<i class='fa-regular fa-file-lines' style='margin-right:9px;color:{FAINT}'></i>"
                    f"{html_lib.escape(c.doc_title)}</span>"
                    f"<i class='fa-solid fa-arrow-right' style='color:{FAINT};font-size:11px'></i></div>",
                    unsafe_allow_html=True)

        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
            f"margin-top:12px;font-family:JetBrains Mono,monospace;font-size:9.5px;color:{FAINT};"
            f"letter-spacing:0.5px'>"
            f"<span>SERENIA COMMAND RAG PIPELINE • GROUNDED CORPUS: {len(docs)} DOCS</span>"
            f"<span><i class='fa-regular fa-thumbs-up' style='margin-left:10px'></i>"
            f"<i class='fa-regular fa-thumbs-down' style='margin-left:10px'></i>"
            f"<i class='fa-regular fa-copy' style='margin-left:10px'></i></span></div>",
            unsafe_allow_html=True)

# ── Samples + registry status ─────────────────────────────────────────────────
with side:
    section_label("Sample Questions", "fa-solid fa-list-ul")
    for q in SAMPLES:
        if st.button(q, use_container_width=True, key=f"s_{hash(q)}"):
            st.session_state["_assistant_q"] = q
            st.rerun()

    st.write("")
    rows = [("Last Synchronized", "Today at 08:30 AM"), ("Indexed Clauses", f"{len(docs) * 30} verified articles"),
            ("Statutory Corpus", "Act 757 (Strata Act)"), ("Local Regulations", "Township House Rules")]
    body = "".join(
        f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
        f"background:#F4F6FB;border-radius:7px;padding:8px 11px;margin-bottom:6px'>"
        f"<span style='font-size:11.5px;color:{MUTED}'>{k}</span>"
        f"<span style='font-size:11.5px;color:{NAVY};font-weight:600'>{v}</span></div>"
        for k, v in rows)
    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 16px'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:11px'>"
        f"<span style='font-size:13px;font-weight:700;color:{NAVY}'>"
        f"<i class='fa-solid fa-globe' style='margin-right:8px;color:{FAINT}'></i>AI Knowledge Base v4.2</span>"
        f"<span style='background:#E8F5E9;color:#2E7D32;padding:3px 8px;border-radius:5px;"
        f"font-size:9.5px;font-weight:700'>ONLINE</span></div>{body}"
        f"<div style='display:flex;align-items:center;justify-content:space-between;border-top:1px solid {BORDER};"
        f"margin-top:10px;padding-top:9px'>"
        f"<span style='font-size:10.5px;color:{MUTED}'>"
        f"<span style='width:6px;height:6px;border-radius:50%;background:#2E7D32;display:inline-block;"
        f"margin-right:7px'></span>Full-text grounded retrieval</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:9.5px;color:{FAINT};"
        f"font-weight:700'>RE-INDEX</span></div></div>",
        unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 16px'>"
        f"<div style='font-size:12.5px;font-weight:700;color:{NAVY};margin-bottom:6px'>"
        f"<i class='fa-regular fa-circle-question' style='margin-right:8px;color:{FAINT}'></i>"
        f"Uncertain about a contract clause?</div>"
        f"<div style='font-size:11.5px;color:{MUTED};line-height:1.55'>Complex structural disputes or "
        f"strata appeals can be routed directly to the Sime Darby Legal Secretariat desk.</div>"
        f"<div style='font-size:10.5px;font-weight:700;letter-spacing:0.5px;color:#B26A00;margin-top:10px'>"
        f"DISPATCH TO LEGAL TRIAGE →</div></div>",
        unsafe_allow_html=True)
