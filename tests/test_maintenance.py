from datetime import date

import pandas as pd
import pytest

from core import maintenance as m
from core.db import connect
from data import generate as g


def tiny():
    assets = pd.DataFrame([
        {"id": "L1-A", "installed_at": "2016-01-01"},
        {"id": "P1-A", "installed_at": "2025-01-01"},
        {"id": "G1-A", "installed_at": "2020-06-01"},
    ])
    logs = pd.DataFrame([
        {"asset_id": "L1-A", "date": "2026-01-10", "kind": "scheduled", "runtime_hours": 500, "vibration_score": 0.4},
        {"asset_id": "L1-A", "date": "2026-05-20", "kind": "breakdown", "runtime_hours": 520, "vibration_score": 0.9},
        {"asset_id": "L1-A", "date": "2026-06-15", "kind": "breakdown", "runtime_hours": 480, "vibration_score": 1.1},
        {"asset_id": "P1-A", "date": "2026-05-01", "kind": "scheduled", "runtime_hours": 300, "vibration_score": 0.3},
        {"asset_id": "P1-A", "date": "2026-06-20", "kind": "breakdown", "runtime_hours": 310, "vibration_score": 0.5},
    ])
    return logs, assets


def test_build_features_exact_values():
    logs, assets = tiny()
    f = m.build_features(logs, assets, as_of=date(2026, 6, 1)).set_index("asset_id")
    l1 = f.loc["L1-A"]
    assert l1["age_months"] == 125
    assert l1["days_since_service"] == 12          # 2026-05-20 -> 2026-06-01
    assert l1["breakdowns_last_12m"] == 1          # only the May one is before as_of
    assert l1["avg_runtime_hours"] == pytest.approx(510)
    assert l1["vibration_score"] == pytest.approx(0.9)
    assert l1["failed_within_30d"] == 1            # breakdown on 06-15
    p1 = f.loc["P1-A"]
    assert p1["breakdowns_last_12m"] == 0 and p1["failed_within_30d"] == 1
    g1 = f.loc["G1-A"]                              # no logs at all
    assert g1["days_since_service"] == m.NO_SERVICE_DAYS and g1["vibration_score"] == 0 and g1["failed_within_30d"] == 0


def test_training_frame_and_train_reach_auc_floor():
    assets = pd.DataFrame(g.gen_assets())
    logs = pd.DataFrame(g.gen_service_logs(g.gen_assets()))
    frame = m.training_frame(logs, assets)
    rate = frame["failed_within_30d"].mean()
    assert 0.08 <= rate <= 0.25, f"label base rate {rate:.2f} outside sane band"
    model, metrics = m.train(frame)
    assert metrics["auc"] >= 0.75
    assert set(metrics["importances"]) == set(m.FEATURES)


def test_score_shape_and_drivers():
    assets = pd.DataFrame(g.gen_assets())
    logs = pd.DataFrame(g.gen_service_logs(g.gen_assets()))
    model, _ = m.train(m.training_frame(logs, assets))
    scored = m.score(model, m.build_features(logs, assets, as_of=g.END))
    assert list(scored.columns) == ["asset_id", "risk", "top_drivers"]
    assert scored["risk"].between(0, 1).all()
    assert scored["risk"].is_monotonic_decreasing
    assert all(len(d) == 2 and set(d) <= set(m.FEATURES) for d in scored["top_drivers"])


def test_create_work_order(tmp_path):
    conn = connect(tmp_path / "t.db")
    conn.execute("INSERT INTO assets(id,name,type,block,installed_at,contractor,sla_hours) "
                 "VALUES('L3-B','Lift L3, Block B','lift','B','2015-01-01','OTIS Malaysia',4)")
    wid = m.create_work_order(conn, "L3-B", 0.78, "High vibration; 2 breakdowns in 12 months")
    row = conn.execute("SELECT * FROM work_orders WHERE id=?", (wid,)).fetchone()
    assert row["asset_id"] == "L3-B" and row["status"] == "open" and row["risk"] == 0.78
