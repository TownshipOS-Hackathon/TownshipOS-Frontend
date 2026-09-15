from core import llm
from tests.fakes import parsed, refusal


def test_cached_runs_fn_once():
    calls = []
    fn = lambda: calls.append(1) or {"a": 1}
    assert llm.cached("k1", fn) == {"a": 1}
    assert llm.cached("k1", fn) == {"a": 1}
    assert calls == [1]
    assert (llm.CACHE_DIR / "k1.json").exists()


def test_cache_key_is_stable_and_handles_bytes():
    assert llm.cache_key("triage", "hi", b"\x00\x01") == llm.cache_key("triage", "hi", b"\x00\x01")
    assert llm.cache_key("triage", "hi", None) != llm.cache_key("triage", "hi", b"\x00")


def test_refusal_reason():
    assert llm.refusal_reason(parsed(None)) is None
    assert llm.refusal_reason(refusal("nope")) == "nope"
