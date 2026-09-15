from core.db import connect


def test_connect_creates_all_tables(tmp_path):
    conn = connect(tmp_path / "t.db")
    names = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"tickets", "assets", "service_logs", "utility_readings", "work_orders"} <= names


def test_connect_is_idempotent(tmp_path):
    p = tmp_path / "t.db"
    c1 = connect(p)
    c1.execute("INSERT INTO utility_readings(block, month, kwh, m3) VALUES ('A','2026-01',1,1)")
    c1.commit()
    conn = connect(p)  # second connect must not wipe data
    assert conn.execute("SELECT COUNT(*) AS n FROM utility_readings").fetchone()["n"] == 1
