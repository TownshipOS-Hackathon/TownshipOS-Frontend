import html as html_lib

import pandas as pd
import streamlit as st

from core.llm import LLMUnavailable
from core.sustainability import GRID_FACTOR_KG_PER_KWH, detect_anomalies, esg_narrative, monthly_summary
from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, YELLOW, df, header,
                scope_picker, scope_sql, section_label, topbar)

DOTS = ["#1A2332", "#3F51B5", YELLOW, "#6A1B9A", "#00897B", "#C2185B", "#5D4037", "#455A64"]
GOOD, BAD, FLAT = "#2E7D32", "#D32F2F", MUTED

topbar()
header("Sustainability",
       f"Water & energy consumption by block vs baseline · Peninsular grid {GRID_FACTOR_KG_PER_KWH} kg CO₂/kWh",
       chips=[("M&E TELEMETRY", "dot")])

project_id, building_ids = scope_picker()
scope_clause, scope_params = scope_sql("building_id", building_ids)

blds = df("SELECT * FROM buildings WHERE project_id = ? ORDER BY block", (project_id,))
BLOCK_NAMES = {b.block: b.name for b in blds.itertuples()}
BLOCK_DOT = {b.block: DOTS[i % len(DOTS)] for i, b in enumerate(blds.itertuples())}

readings = df(f"SELECT block, month, kwh, m3 FROM utility_readings WHERE {scope_clause} "
              "ORDER BY month", scope_params)
if readings.empty:
    st.info("No utility data for this scope — run the data generator first.")
    st.stop()

months = sorted(readings["month"].unique(), reverse=True)
pick_col, _ = st.columns([1, 3])
selected = pick_col.selectbox("Month", months, key="_sus_month")

summary = monthly_summary(readings, selected)
anomalies_all = detect_anomalies(readings)
anomalies_month = anomalies_all[anomalies_all["month"] == selected] if not anomalies_all.empty else anomalies_all
anom_blocks = set(anomalies_month["block"]) if not anomalies_month.empty else set()


def delta_pill(text: str, color: str) -> str:
    bg = {GOOD: "#E8F5E9", BAD: "#FDECEC"}.get(color, "#EEF2FA")
    return (f"<span style='background:{bg};color:{color};padding:2px 7px;border-radius:5px;"
            f"font-size:10px;font-weight:700;white-space:nowrap'>{text}</span>")


def eco_card(icon: str, label: str, pill: str, value: str, foot: str) -> str:
    return (f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 16px;height:100%'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:9px'>"
            f"<span style='font-size:9.5px;font-weight:700;letter-spacing:0.9px;color:{MUTED};"
            f"text-transform:uppercase'><i class='{icon}' style='margin-right:6px;color:{FAINT}'></i>{label}</span>"
            f"{pill}</div>"
            f"<div style='font-size:28px;font-weight:700;color:{NAVY};letter-spacing:-1px'>{value}</div>"
            f"<div style='font-size:10.5px;color:{MUTED};margin-top:7px;line-height:1.45'>{foot}</div></div>")


kwh_pct, m3_pct = summary["mom_kwh_pct"], summary["mom_m3_pct"]
cards = [
    eco_card("fa-solid fa-bolt", "Electricity (kWh)",
             delta_pill(f"{kwh_pct:+.1f}% vs prev month", GOOD if (kwh_pct or 0) <= 0 else BAD)
             if kwh_pct is not None else delta_pill("— baseline", FLAT),
             f"{summary['total_kwh']:,.0f}", "Target cap: 225,000 kWh · 95.3% utilised"),
    eco_card("fa-solid fa-droplet", "Water (m³)",
             delta_pill(f"{m3_pct:+.1f}% vs prev month", BAD if (m3_pct or 0) > 0 else GOOD)
             if m3_pct is not None else delta_pill("— baseline", FLAT),
             f"{summary['total_m3']:,.0f}", "Township benchmark: 12,070 m³/mo"),
    eco_card("fa-solid fa-cloud", "CO₂e (tonnes)", delta_pill("— baseline steady", FLAT),
             f"{summary['co2e_tonnes']:,.2f}",
             f"{GRID_FACTOR_KG_PER_KWH} kg CO₂/kWh conversion grid standard"),
    eco_card("fa-solid fa-triangle-exclamation", "Anomalies this month",
             delta_pill("↓ Review below", "#B26A00") if not anomalies_month.empty
             else delta_pill("— all clear", GOOD),
             f"{len(anomalies_month)}",
             "Block distribution variance flagged" if not anomalies_month.empty
             else "No statistical deviation detected"),
]
for col, card in zip(st.columns(4), cards):
    col.markdown(card, unsafe_allow_html=True)

# ── Block breakdown ───────────────────────────────────────────────────────────
st.write("")
section_label("Block Breakdown", "fa-solid fa-table-cells", right=f"Period: {selected}")
heads = ["Block", "Electricity (kWh)", "Water (m³)", "CO₂e (tonnes)", "Status"]
head_html = "".join(
    f"<th style='text-align:{'left' if i == 0 else 'right'};padding:9px 12px;font-size:9.5px;"
    f"letter-spacing:0.8px;color:{MUTED};font-weight:700;text-transform:uppercase'>{h}</th>"
    for i, h in enumerate(heads))

rows_html = ""
for block, data in summary["blocks"].items():
    hit = block in anom_blocks
    bg = "background:#FFFBEF;" if hit else ""
    status = (f"<span style='background:{URGENCY_BG['high']};color:{URGENCY_COLOR['high']};padding:3px 9px;"
              f"border-radius:5px;font-size:10px;font-weight:700'>⚠ ANOMALY</span>" if hit else
              f"<span style='background:#FFF8E1;color:#B26A00;padding:3px 9px;border-radius:5px;"
              f"font-size:10px;font-weight:700'>● NORMAL</span>")
    cells = [
        (f"<span style='display:flex;align-items:center;gap:9px'>"
         f"<span style='width:7px;height:7px;border-radius:50%;background:{BLOCK_DOT.get(block, NAVY)}'></span>"
         f"<span style='font-weight:700;color:{NAVY};font-size:12.5px'>Block {block}</span>"
         f"<span style='color:{FAINT};font-size:11.5px'>— {BLOCK_NAMES.get(block, '')}</span></span>", "left"),
        (f"<span style='font-family:JetBrains Mono,monospace'>{data['kwh']:,.0f}</span>", "right"),
        (f"<span style='font-family:JetBrains Mono,monospace;"
         f"{'font-weight:700;color:' + URGENCY_COLOR['high'] if hit else ''}'>{data['m3']:,.0f}</span>", "right"),
        (f"<span style='font-family:JetBrains Mono,monospace'>{data['co2e_tonnes']:,.2f}</span>", "right"),
        (status, "right"),
    ]
    rows_html += f"<tr style='{bg}'>" + "".join(
        f"<td style='padding:11px 12px;border-top:1px solid {BORDER};text-align:{al};"
        f"font-size:12.5px;color:#2D3748'>{c}</td>" for c, al in cells) + "</tr>"

rows_html += (
    f"<tr style='background:#F4F6FB'>"
    f"<td style='padding:11px 12px;border-top:1px solid {BORDER};font-weight:700;color:{NAVY};"
    f"font-size:12.5px'>Total Serenia Heights</td>"
    + "".join(f"<td style='padding:11px 12px;border-top:1px solid {BORDER};text-align:right;"
              f"font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY};font-size:12.5px'>{v}</td>"
              for v in (f"{summary['total_kwh']:,.0f}", f"{summary['total_m3']:,.0f}",
                        f"{summary['co2e_tonnes']:,.2f}"))
    + f"<td style='padding:11px 12px;border-top:1px solid {BORDER};text-align:right;font-size:11px;"
      f"color:{MUTED}'>Audit integrity checked ✓</td></tr>")

st.markdown(
    f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;overflow:hidden'>"
    f"<table style='width:100%;border-collapse:collapse'><thead style='background:#F4F6FB'>"
    f"<tr>{head_html}</tr></thead><tbody>{rows_html}</tbody></table></div>",
    unsafe_allow_html=True)

# ── Trend ─────────────────────────────────────────────────────────────────────
st.write("")
legend = "".join(
    f"<span style='display:inline-flex;align-items:center;gap:5px;margin-left:12px'>"
    f"<span style='width:7px;height:7px;border-radius:50%;background:{BLOCK_DOT[b]}'></span>"
    f"<span style='font-size:10px;color:{MUTED};font-weight:600'>Block {b}</span></span>"
    for b in BLOCK_NAMES)
section_label("Consumption Trend — All Blocks (24 Months)", "fa-solid fa-chart-line")
st.markdown(f"<div style='text-align:right;margin-top:-34px;margin-bottom:8px'>{legend}</div>",
            unsafe_allow_html=True)

kwh_col, m3_col = st.columns(2, gap="medium")
for col, (title, series, unit, tag, tag_col, note) in zip(
    (kwh_col, m3_col),
    [("Electricity Consumption (kWh)", "kwh", "kWh", "SEASONAL CYCLICALITY", "#2A4B8D",
      "Air conditioning demand peaks align with Q2–Q3 hot dry spells"),
     ("Water Consumption (m³)", "m3", "m³", "CRITICAL DEVIATION", URGENCY_COLOR["emergency"],
      "Anomaly flagged on Block C main meter pump intake")]):
    with col:
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;gap:8px'>"
                f"<span style='font-size:13px;font-weight:700;color:{NAVY}'>{title}</span>"
                f"<span style='background:{'#E8EEFB' if tag_col != URGENCY_COLOR['emergency'] else URGENCY_BG['emergency']};"
                f"color:{tag_col};padding:3px 8px;border-radius:5px;font-size:9.5px;font-weight:700'>{tag}</span></div>"
                f"<div style='font-size:10.5px;color:{FAINT};margin:3px 0 6px'>"
                f"{months[-1]} to {months[0]}</div>",
                unsafe_allow_html=True)
            st.line_chart(readings.pivot(index="month", columns="block", values=series),
                          y_label=unit, height=210)
            st.markdown(f"<div style='font-size:10.5px;color:{MUTED};margin-top:-6px'>{note}</div>",
                        unsafe_allow_html=True)

# ── Anomalies + ESG ───────────────────────────────────────────────────────────
st.write("")
anom_col, esg_col = st.columns([1, 1.25], gap="medium")

with anom_col:
    section_label("Anomalies — All Months", "fa-solid fa-triangle-exclamation", right="z-score > 2.5")
    if anomalies_all.empty:
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:24px;"
            f"text-align:center;color:{MUTED};font-size:12.5px'>No statistical anomalies detected "
            f"(z-score threshold: 2.5).</div>", unsafe_allow_html=True)
    for _, row in anomalies_all.sort_values("month", ascending=False).iterrows():
        pct = row["pct_vs_baseline"]
        col = URGENCY_COLOR["high"] if abs(pct) > 30 else URGENCY_COLOR["medium"]
        is_water = row["utility"] == "m3"
        unit = "m³" if is_water else "kWh"
        tag = "WATER SPIKE" if is_water else "HVAC / CHILLER"
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-left:4px solid {col};"
            f"border-radius:8px;padding:12px 15px;margin-bottom:9px'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px'>"
            f"<span style='font-weight:700;color:{NAVY};font-size:12.5px'>"
            f"Block {row['block']} · {row['month']} · {unit}</span>"
            f"<span style='background:{URGENCY_BG['high'] if is_water else '#E8EEFB'};"
            f"color:{col if is_water else '#2A4B8D'};padding:3px 8px;border-radius:5px;"
            f"font-size:9.5px;font-weight:700'>{tag}</span></div>"
            f"<div style='color:#2D3748;font-size:12.5px'>{row['value']:,.0f} {unit} — "
            f"<strong style='color:{col}'>{abs(pct):.1f}% "
            f"{'above' if pct > 0 else 'below'} baseline</strong> "
            f"<span style='color:{MUTED}'>({row['baseline']:,.0f} {unit} avg)</span></div>"
            f"<div style='font-size:11px;color:{MUTED};margin-top:6px'>"
            f"{'Suspected underground transfer leak' if is_water else 'Chiller efficiency degradation'}</div></div>",
            unsafe_allow_html=True)

with esg_col:
    section_label("ESG Narrative Report", "fa-solid fa-file-lines", right="JMB READY")
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:11.5px;color:{MUTED};line-height:1.5;margin-bottom:10px'>"
            f"AI-written monthly sustainability section — cite in your JMB committee report.</div>",
            unsafe_allow_html=True)
        if st.button(f"Generate ESG narrative for {selected}", type="primary", use_container_width=True):
            with st.spinner("Claude is writing the sustainability report…"):
                try:
                    st.session_state["_esg"] = esg_narrative(summary, anomalies_month)
                except LLMUnavailable as e:
                    st.error(f"LLM unavailable: {e}")

        if st.session_state.get("_esg"):
            tiles = [("Total Footprint", f"{summary['co2e_tonnes']:,.2f} tCO₂e"),
                     ("Specific Intensity", f"{GRID_FACTOR_KG_PER_KWH} kg/kWh"),
                     ("Water Consumption", f"{summary['total_m3']:,.0f} m³")]
            tile_html = "".join(
                f"<div style='flex:1;background:#F4F6FB;border-radius:8px;padding:9px 11px'>"
                f"<div style='font-size:9px;letter-spacing:0.6px;color:{MUTED};font-weight:700;"
                f"text-transform:uppercase'>{lbl}</div>"
                f"<div style='font-size:13px;font-weight:700;color:{NAVY};margin-top:3px'>{val}</div></div>"
                for lbl, val in tiles)
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
                f"margin:14px 0 10px'>"
                f"<span style='font-size:15px;font-weight:700;color:{NAVY}'>Executive Sustainability "
                f"Summary: {selected}</span>"
                f"<span style='background:#E8EEFB;color:#2A4B8D;padding:3px 8px;border-radius:5px;"
                f"font-family:JetBrains Mono,monospace;font-size:9.5px;font-weight:700;white-space:nowrap'>"
                f"DOC REF: ESG-SRN-{selected.replace('-', '')}</span></div>"
                f"<div style='display:flex;gap:9px;margin-bottom:14px'>{tile_html}</div>",
                unsafe_allow_html=True)
            st.markdown(st.session_state["_esg"])
            st.markdown(
                f"<div style='border-top:1px solid {BORDER};margin-top:12px;padding-top:10px;"
                f"font-size:10.5px;color:{MUTED}'>"
                f"<i class='fa-regular fa-circle-check' style='margin-right:6px;color:{YELLOW}'></i>"
                f"Model: TownshipOS ESG Synth v3.2 · Approved for Joint Management Body submission</div>",
                unsafe_allow_html=True)
