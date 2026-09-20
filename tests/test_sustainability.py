import pandas as pd
import pytest

from core import sustainability as s
from data import generate as g
from tests.fakes import FakeClient, refusal, text_result


def test_detect_anomalies_flags_injected_spikes_only():
    readings = pd.DataFrame(g.gen_readings())
    an = s.detect_anomalies(readings)
    water_c = an[(an.block == "C") & (an.utility == "m3")]
    assert len(water_c) == 1 and water_c.iloc[0]["month"] == "2026-08"
    assert water_c.iloc[0]["pct_vs_baseline"] > 30
    kwh_a = an[(an.block == "A") & (an.utility == "kwh")]
    assert len(kwh_a) == 1 and kwh_a.iloc[0]["month"] == "2026-05"
    assert len(an) <= 4  # no noisy false positives elsewhere


def test_short_history_block_is_skipped():
    readings = pd.DataFrame([{"block": "Z", "month": f"2026-0{i}", "kwh": 100, "m3": 10} for i in range(1, 6)])
    assert s.detect_anomalies(readings).empty


def test_monthly_summary():
    readings = pd.DataFrame(g.gen_readings())
    sm = s.monthly_summary(readings, "2026-08")
    assert set(sm["blocks"]) == set(g.BLOCKS)
    assert sm["total_kwh"] == sum(b["kwh"] for b in sm["blocks"].values())
    assert sm["co2e_tonnes"] == pytest.approx(sm["total_kwh"] * s.GRID_FACTOR_KG_PER_KWH / 1000, abs=0.01)
    assert "mom_kwh_pct" in sm and "mom_m3_pct" in sm


def test_esg_narrative_uses_client_and_caches():
    readings = pd.DataFrame(g.gen_readings())
    sm, an = s.monthly_summary(readings, "2026-08"), s.detect_anomalies(readings)
    client = FakeClient(text_result("## ESG Summary\nBlock C water +42%."))
    text = s.esg_narrative(sm, an, client=client)
    assert text.startswith("## ESG Summary")
    assert "2026-08" in client.calls[0]["messages"][1]["content"]
    assert s.esg_narrative(sm, an, client=FakeClient()) == text  # cached


def test_esg_narrative_refusal_returns_message():
    assert "declined" in s.esg_narrative({"month": "x"}, pd.DataFrame(), client=FakeClient(refusal("declined")))
