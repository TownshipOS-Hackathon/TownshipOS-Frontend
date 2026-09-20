"""Group-admin roll-up: every township and building in one place."""
import html as html_lib

import streamlit as st

from core.sustainability import GRID_FACTOR_KG_PER_KWH
from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, data_table, df, header,
                metric_card, section_label, topbar, txt)

topbar("GROUP PORTFOLIO · ALL TOWNSHIPS")
header("Portfolio Overview", "Consolidated operations across every township under management",
       eyebrow_tag="GROUP ADMIN", chips=[("ALL REGIONS", "dot"), ("Live roll-up", "plain")])

latest = df("SELECT MAX(month) AS m FROM utility_readings")["m"].iloc[0]

rollup = df("""
    SELECT p.id, p.name, p.state, p.district, p.manager,
           COUNT(DISTINCT b.id) AS buildings,
           COALESCE(SUM(DISTINCT b.units), 0) AS units
    FROM projects p LEFT JOIN buildings b ON b.project_id = p.id
    GROUP BY p.id ORDER BY p.name
""")
tickets = df("""
    SELECT b.project_id AS pid, t.urgency, t.status, t.building_id
    FROM tickets t JOIN buildings b ON b.id = t.building_id
""")
energy = df("SELECT b.project_id AS pid, r.building_id, r.kwh, r.m3 "
            "FROM utility_readings r JOIN buildings b ON b.id = r.building_id "
            "WHERE r.month = ?", (latest,))

open_t = tickets[tickets["status"].isin(["open", "assigned"])]
urgent_t = open_t[open_t["urgency"].isin(["high", "emergency"])]

# ── Group metrics ─────────────────────────────────────────────────────────────
cards = [
    metric_card("Townships", str(len(rollup)), "active", "— All Selangor region",
                "fa-solid fa-city"),
    metric_card("Buildings", str(int(rollup["buildings"].sum())), "blocks",
                f"— {int(rollup['units'].sum()):,} registered units", "fa-solid fa-building"),
    metric_card("Open tickets", str(len(open_t)), "portfolio-wide",
                f"— {len(urgent_t)} urgent across all sites", "fa-regular fa-clipboard",
                URGENCY_COLOR["high"] if len(urgent_t) else NAVY),
    metric_card("Group CO₂e", f"{energy['kwh'].sum() * GRID_FACTOR_KG_PER_KWH / 1000:,.1f}", "tonnes",
                f"— {latest} · grid {GRID_FACTOR_KG_PER_KWH} kg/kWh", "fa-solid fa-cloud"),
]
for col, card in zip(st.columns(4), cards):
    col.markdown(card, unsafe_allow_html=True)

# ── Township roll-up ──────────────────────────────────────────────────────────
st.write("")
section_label("Township Roll-Up", "fa-solid fa-layer-group", right=f"Utilities period: {latest}")
rows = []
for p in rollup.itertuples():
    pt = open_t[open_t["pid"] == p.id]
    pu = pt[pt["urgency"].isin(["high", "emergency"])]
    pe = energy[energy["pid"] == p.id]
    flag = (f"<span style='background:{URGENCY_BG['high']};color:{URGENCY_COLOR['high']};padding:3px 9px;"
            f"border-radius:5px;font-size:10px;font-weight:700'>{len(pu)} URGENT</span>" if len(pu)
            else f"<span style='background:#E8F5E9;color:#2E7D32;padding:3px 9px;border-radius:5px;"
                 f"font-size:10px;font-weight:700'>STEADY</span>")
    rows.append([
        f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>{p.id}</span>",
        f"<span style='font-weight:700;color:{NAVY}'>{txt(p.name)}</span>"
        f"<div style='font-size:11px;color:{FAINT}'>{txt(p.district, '')} {txt(p.state, '')}</div>",
        f"<span style='font-size:12px'>{txt(p.manager)}</span>",
        str(int(p.buildings)), f"{int(p.units):,}", str(len(pt)),
        f"{pe['kwh'].sum():,.0f}", f"{pe['m3'].sum():,.0f}",
        f"{pe['kwh'].sum() * GRID_FACTOR_KG_PER_KWH / 1000:,.2f}", flag,
    ])
align = ["left", "left", "left", "right", "right", "right", "right", "right", "right", "right"]
st.markdown(data_table(
    ["Code", "Township", "FM Manager", "Blocks", "Units", "Open", "kWh", "m³", "tCO₂e", "Status"],
    rows, align,
    footer=["", "Portfolio total", "", str(int(rollup["buildings"].sum())),
            f"{int(rollup['units'].sum()):,}", str(len(open_t)),
            f"{energy['kwh'].sum():,.0f}", f"{energy['m3'].sum():,.0f}",
            f"{energy['kwh'].sum() * GRID_FACTOR_KG_PER_KWH / 1000:,.2f}", ""]),
    unsafe_allow_html=True)

# ── Building drill-down ───────────────────────────────────────────────────────
st.write("")
names = {p.name: p.id for p in rollup.itertuples()}
pick_col, _ = st.columns([1.2, 3])
chosen = pick_col.selectbox("Drill into township", list(names))
pid = names[chosen]

section_label("Building Breakdown", "fa-solid fa-building-circle-check",
              right=html_lib.escape(chosen))
blds = df("SELECT * FROM buildings WHERE project_id = ? ORDER BY block", (pid,))
rows = []
for b in blds.itertuples():
    bt = open_t[open_t["building_id"] == b.id]
    bu = bt[bt["urgency"].isin(["high", "emergency"])]
    be = energy[energy["building_id"] == b.id]
    rows.append([
        f"<span style='font-weight:700;color:{NAVY}'>Block {b.block}</span>"
        f"<div style='font-size:11px;color:{FAINT}'>{html_lib.escape(b.name)}</div>",
        f"<span style='background:#EEF2FA;color:{NAVY};padding:3px 8px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{html_lib.escape(b.type.upper())}</span>",
        f"{b.units:,}", str(b.floors), str(len(bt)),
        (f"<span style='color:{URGENCY_COLOR['emergency']};font-weight:700'>{len(bu)}</span>"
         if len(bu) else f"<span style='color:{FAINT}'>0</span>"),
        f"{be['kwh'].sum():,.0f}", f"{be['m3'].sum():,.0f}",
    ])
st.markdown(data_table(["Building", "Type", "Units", "Floors", "Open Tickets", "Urgent", "kWh", "m³"],
                       rows, ["left", "left", "right", "right", "right", "right", "right", "right"]),
            unsafe_allow_html=True)

# ── Contractor load ───────────────────────────────────────────────────────────
st.write("")
section_label("Contractor Load — Portfolio Wide", "fa-solid fa-helmet-safety",
              right="Open tickets by assigned contractor")
load = df("""
    SELECT t.contractor, COUNT(*) AS open_jobs,
           SUM(CASE WHEN t.urgency IN ('high','emergency') THEN 1 ELSE 0 END) AS urgent
    FROM tickets t WHERE t.status IN ('open','assigned') AND t.contractor IS NOT NULL
    GROUP BY t.contractor ORDER BY open_jobs DESC
""")
directory = {c["name"]: c for c in df("SELECT * FROM contractors").to_dict("records")}
rows = []
for c in load.itertuples():
    meta = directory.get(c.contractor, {})
    rows.append([
        f"<span style='font-weight:600;color:{NAVY}'>{html_lib.escape(c.contractor)}</span>",
        f"<span style='color:{MUTED};font-size:11.5px'>{html_lib.escape(str(meta.get('trade', '—')))}</span>",
        f"<span style='font-size:11.5px'>{html_lib.escape(str(meta.get('contact_person', '—')))}</span>",
        f"<span style='font-family:JetBrains Mono,monospace;font-size:11.5px'>"
        f"{html_lib.escape(str(meta.get('phone', '—')))}</span>",
        str(int(c.open_jobs)),
        (f"<span style='color:{URGENCY_COLOR['emergency']};font-weight:700'>{int(c.urgent)}</span>"
         if c.urgent else f"<span style='color:{FAINT}'>0</span>"),
    ])
st.markdown(data_table(["Contractor", "Trade", "Contact", "Phone", "Open Jobs", "Urgent"],
                       rows, ["left", "left", "left", "left", "right", "right"]),
            unsafe_allow_html=True)
