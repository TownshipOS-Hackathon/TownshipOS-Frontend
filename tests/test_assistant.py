from pathlib import Path

import pytest

from core import assistant as a
from tests.fakes import FakeClient, refusal, text_result


def test_load_docs_builds_title_content_pairs(tmp_path):
    (tmp_path / "01_A.txt").write_text("alpha", encoding="utf-8")
    (tmp_path / "02_B.txt").write_text("beta", encoding="utf-8")
    docs = a.load_docs(tmp_path)
    assert [d["title"] for d in docs] == ["01 A", "02 B"]
    assert docs[0]["content"] == "alpha" and docs[1]["content"] == "beta"


def test_real_docs_folder_has_five_files():
    assert len(a.load_docs(Path("data/docs"))) == 5


def test_ask_collects_text_and_citations():
    resp = "The penalty is RM 500 per incident. [Source: 01 Lift Maintenance SLA]"
    client = FakeClient(text_result(resp))
    docs = [{"title": "01 Lift Maintenance SLA", "content": "penalty of RM 500 per incident"}]
    ans = a.ask("Penalty if OTIS misses the 4h SLA?", docs, client=client)
    assert "RM 500" in ans.text
    assert ans.citations[0].doc_title == "01 Lift Maintenance SLA" and ans.refused is False
    kw = client.calls[0]
    assert kw["messages"][0]["role"] == "system"
    assert "Penalty" in kw["messages"][1]["content"]


def test_ask_no_tool_call_returns_empty_citations():
    ans = a.ask("q", [], client=FakeClient(refusal("no")))
    assert ans.citations == []


def test_ask_rejects_empty_question():
    with pytest.raises(ValueError):
        a.ask("  ", [])
