import streamlit as st

from core.assistant import ask, load_docs
from core.llm import LLMUnavailable
from ui import header

st.set_page_config(page_title="Ask · TownshipOS", layout="wide")
header("Ask TownshipOS", "Answers from your SLAs, SOPs and the Strata Management Act — every claim cited")

docs = load_docs()
st.caption("Loaded: " + " · ".join(d["title"] for d in docs))
examples = ["Penalty if OTIS misses the 4h SLA?", "Berapa lama kontraktor perlu siasat kebocoran antara tingkat?",
            "Can a resident hack walls on Sunday?", "What must the duty officer do if someone is trapped in a lift?"]
q = st.text_input("Question", placeholder=examples[0])
cols = st.columns(len(examples))
for c, ex in zip(cols, examples):
    if c.button(ex, use_container_width=True):
        q = ex
if q:
    try:
        with st.spinner("Reading the documents…"):
            ans = ask(q, docs)
    except LLMUnavailable as e:
        st.error(f"Assistant unavailable: {e}")
    else:
        if ans.refused:
            st.warning(ans.text)
        else:
            st.markdown(ans.text)
            if ans.citations:
                with st.expander(f"Sources ({len(ans.citations)})", expanded=True):
                    for c in ans.citations:
                        st.markdown(f"**{c.doc_title}** — “{c.cited_text.strip()}”")
            else:
                st.warning("Uncited answer — verify against the documents before acting.")
