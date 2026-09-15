from pathlib import Path

import pytest

from core import assistant as a
from tests.fakes import FakeClient, citation, message, refusal, text_block


def test_load_docs_builds_document_blocks_with_citations_and_single_cache_control(tmp_path):
    (tmp_path / "01_A.txt").write_text("alpha", encoding="utf-8")
    (tmp_path / "02_B.txt").write_text("beta", encoding="utf-8")
    docs = a.load_docs(tmp_path)
    assert [d["title"] for d in docs] == ["01 A", "02 B"]
    assert all(d["type"] == "document" and d["citations"] == {"enabled": True} for d in docs)
    assert docs[0]["source"] == {"type": "text", "media_type": "text/plain", "data": "alpha"}
    assert "cache_control" not in docs[0] and docs[1]["cache_control"] == {"type": "ephemeral"}


def test_real_docs_folder_has_five_files():
    assert len(a.load_docs(Path("data/docs"))) == 5


def test_ask_collects_text_and_citations():
    resp = message(text_block("The penalty is "),
                   text_block("RM 500 per incident", [citation("01 Lift Maintenance SLA", "penalty of RM 500 per incident")]),
                   text_block("."))
    client = FakeClient(resp)
    docs = [{"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": "x"}, "title": "T", "citations": {"enabled": True}}]
    ans = a.ask("Penalty if OTIS misses the 4h SLA?", docs, client=client)
    assert ans.text == "The penalty is RM 500 per incident."
    assert ans.citations[0].doc_title == "01 Lift Maintenance SLA" and ans.refused is False
    kw = client.calls[0]
    assert kw["messages"][0]["content"][:-1] == docs and kw["messages"][0]["content"][-1]["text"].startswith("Penalty")
    assert kw["fallbacks"] == "default"


def test_ask_refusal():
    ans = a.ask("q", [], client=FakeClient(refusal("no")))
    assert ans.refused is True and ans.citations == []


def test_ask_rejects_empty_question():
    with pytest.raises(ValueError):
        a.ask("  ", [])
