from collections import Counter

from data import generate as g


def test_assets_count_and_blocks():
    assets = g.gen_assets()
    assert len(assets) == len(g.BLOCKS) * sum(t[0] for t in g.ASSET_TYPES.values())
    assert {a["block"] for a in assets} == set(g.BLOCKS)
    assert {a["type"] for a in assets} == {"lift", "pump", "genset", "chiller", "gate"}
    assert all(a["building_id"] == g.BUILDING_ID[a["block"]] for a in assets)


def test_service_logs_cover_24_months_and_have_breakdowns():
    assets = g.gen_assets()
    logs = g.gen_service_logs(assets)
    months = {l["date"][:7] for l in logs}
    assert len(months) >= 23
    kinds = Counter(l["kind"] for l in logs)
    assert kinds["breakdown"] > 0 and kinds["scheduled"] > kinds["breakdown"]


def test_readings_have_injected_block_c_water_spike():
    rows = g.gen_readings()
    assert len(rows) == len(g.BLOCKS) * 24
    c = sorted((r for r in rows if r["block"] == "C"), key=lambda r: r["month"])
    baseline = sum(r["m3"] for r in c[-13:-1]) / 12
    assert c[-1]["m3"] > 1.3 * baseline


def test_complaints_language_mix_and_labels():
    rows = g.gen_complaints(200)
    assert len(rows) == 200
    mix = Counter(r["language"] for r in rows)
    assert 0.40 <= mix["ms"] / 200 <= 0.60
    assert 0.25 <= mix["en"] / 200 <= 0.45
    assert 0.08 <= mix["zh"] / 200 <= 0.22
    assert all(r["category"] in g.CATEGORIES and r["urgency"] in g.URGENCIES for r in rows)
    assert any(r["urgency"] == "emergency" for r in rows)


def test_main_populates_db(tmp_path):
    conn = g.main(tmp_path / "t.db", out_dir=tmp_path)
    n = lambda t: conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
    assert n("assets") == len(g.BLOCKS) * sum(t[0] for t in g.ASSET_TYPES.values())
    assert n("service_logs") > 300 and n("utility_readings") == len(g.BLOCKS) * 24
    assert n("tickets") == 60
    assert (tmp_path / "complaints.jsonl").exists()
    assert (tmp_path / "triage_set.jsonl").exists()


def test_main_seeds_org_and_scopes_every_row(tmp_path):
    conn = g.main(tmp_path / "t.db", out_dir=tmp_path)
    n = lambda t: conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
    assert n("projects") == len(g.PROJECTS)
    assert n("buildings") == len(g.BLOCKS)
    assert n("users") == len(g.USERS) and n("contractors") == len(g.CONTRACTORS)
    for table in ("tickets", "assets", "utility_readings"):
        orphans = conn.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE building_id IS NULL "
            f"OR building_id NOT IN (SELECT id FROM buildings)").fetchone()["n"]
        assert orphans == 0, f"{table} has rows outside the portfolio"
