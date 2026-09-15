"""Ask TownshipOS: SOP/SLA documents passed as cited document blocks. No vector DB."""
from dataclasses import dataclass
from pathlib import Path

from core.llm import API_ERRORS, BETAS, MODEL, LLMUnavailable, cache_key, cached, get_client, refusal_reason

MAX_QUESTION = 1000
DOCS_DIR = Path("data/docs")

SYSTEM = """You are TownshipOS, an assistant for a Malaysian township property-management team.
Answer only from the attached documents (SLAs, guidelines, SOPs, Strata Management Act extracts).
Cite the clause you rely on. If the documents do not answer the question, say so plainly and suggest who to ask.
Be concise: a direct answer first, then the supporting clause. Reply in the language of the question."""


@dataclass
class Citation:
    doc_title: str
    cited_text: str


@dataclass
class Answer:
    text: str
    citations: list[Citation]
    refused: bool


def load_docs(dir=DOCS_DIR) -> list[dict]:
    blocks = [{
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": p.read_text(encoding="utf-8")},
        "title": p.stem.replace("_", " "),
        "citations": {"enabled": True},
    } for p in sorted(Path(dir).glob("*.txt"))]
    if blocks:
        blocks[-1]["cache_control"] = {"type": "ephemeral"}  # cache the whole doc prefix
    return blocks


def _call(question: str, docs: list[dict], client) -> dict:
    try:
        with client.beta.messages.stream(
            model=MODEL, max_tokens=4096, system=SYSTEM,
            messages=[{"role": "user", "content": [*docs, {"type": "text", "text": question}]}],
            output_config={"effort": "high"}, betas=BETAS, fallbacks="default",
        ) as stream:
            r = stream.get_final_message()
    except API_ERRORS as e:
        raise LLMUnavailable(str(e)) from e
    reason = refusal_reason(r)
    if reason:
        return {"text": reason, "citations": [], "refused": True}
    text, cites = "", []
    for b in r.content:
        if b.type != "text":
            continue
        text += b.text
        for c in getattr(b, "citations", None) or []:
            cites.append({"doc_title": c.document_title, "cited_text": c.cited_text})
    return {"text": text, "citations": cites, "refused": False}


def ask(question: str, docs: list[dict], *, client=None) -> Answer:
    question = (question or "").strip()[:MAX_QUESTION]
    if not question:
        raise ValueError("Ask a question")
    key = cache_key("ask", question, [d["source"]["data"] for d in docs])  # doc edits invalidate cache
    data = cached(key, lambda: _call(question, docs, client or get_client()))
    return Answer(text=data["text"], citations=[Citation(**c) for c in data["citations"]], refused=data["refused"])
