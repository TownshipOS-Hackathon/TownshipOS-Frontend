import base64
import io

import pytest
from PIL import Image
from pydantic import ValidationError

from core import triage as t
from core.db import connect
from tests.fakes import FakeClient, parsed, refusal


def llm(**over):
    base = dict(category="lift", urgency="high", location="Blok B tingkat 5", language="ms",
                summary_en="Lift making strange noise", reply_bm="Terima kasih.", reply_en="Thank you.",
                confidence=0.92)
    return t.TriageLLM(**{**base, **over})


def test_route_uses_table_and_emergency_rules():
    assert t.route("lift", "high", 0.9) == ("OTIS Malaysia", 4, False)
    assert t.route("lift", "emergency", 0.9) == ("OTIS Malaysia", 1, True)
    assert t.route("plumbing", "medium", 0.4) == ("AquaFix Plumbing Sdn Bhd", 8, True)  # low confidence


def test_llm_model_rejects_unknown_category():
    with pytest.raises(ValidationError):
        llm(category="rocket")


def test_triage_happy_path_calls_parse_with_expected_shape():
    client = FakeClient(parsed(llm()))
    r = t.triage("Lif rosak tingkat 5, bunyi pelik", client=client)
    assert r.category == "lift" and r.contractor == "OTIS Malaysia" and r.sla_hours == 4
    assert r.needs_human is False and r.error is None
    kw = client.calls[0]
    assert kw["model"] == "claude-opus-5" and kw["output_format"] is t.TriageLLM
    assert kw["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in kw["betas"]
    assert kw["messages"][0]["content"][-1]["type"] == "text"


def test_triage_is_cached_second_call_makes_no_request():
    client = FakeClient(parsed(llm()))
    t.triage("same text", client=client)
    t.triage("same text", client=FakeClient())  # no responses queued: would raise if called
    assert len(client.calls) == 1


def test_triage_refusal_routes_to_human():
    r = t.triage("some text", client=FakeClient(refusal("policy")))
    assert r.needs_human is True and r.confidence == 0 and r.error == "policy"
    assert r.category == "other"


def test_triage_retries_once_on_incomplete_then_falls_back():
    client = FakeClient(parsed(None, stop_reason="max_tokens"), parsed(None, stop_reason="max_tokens"))
    r = t.triage("text", client=client)
    assert len(client.calls) == 2 and r.needs_human is True and "incomplete" in r.error


def test_triage_retry_succeeds_second_time():
    client = FakeClient(parsed(None, stop_reason="max_tokens"), parsed(llm()))
    assert t.triage("text2", client=client).category == "lift"


def test_triage_rejects_empty_input():
    with pytest.raises(ValueError):
        t.triage("   ")


def _png(w=3000, h=2000):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), "red").save(buf, format="PNG")
    return buf.getvalue()


def test_prepare_image_downscales_and_returns_jpeg():
    b64, mt = t.prepare_image(_png())
    assert mt == "image/jpeg"
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    assert max(img.size) == t.MAX_IMAGE_SIDE


def test_prepare_image_rejects_oversize_and_bad_format():
    with pytest.raises(ValueError):
        t.prepare_image(b"x" * (t.MAX_IMAGE_BYTES + 1))
    with pytest.raises(ValueError):
        t.prepare_image(b"not an image")


def test_triage_with_image_puts_image_block_first():
    client = FakeClient(parsed(llm()))
    t.triage("leak", image_bytes=_png(100, 100), client=client)
    content = client.calls[0]["messages"][0]["content"]
    assert content[0]["type"] == "image" and content[0]["source"]["media_type"] == "image/jpeg"


def test_ticket_insert_then_apply(tmp_path):
    conn = connect(tmp_path / "t.db")
    tid = t.insert_ticket(conn, "Bocor dari atas", None)
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
    assert row["status"] == "untriaged" and row["raw_text"] == "Bocor dari atas"
    result = t.triage("Bocor dari atas", client=FakeClient(parsed(llm(category="plumbing"))))
    t.apply_triage(conn, tid, result)
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
    assert row["status"] == "open" and row["category"] == "plumbing" and row["contractor"] == "AquaFix Plumbing Sdn Bhd"
