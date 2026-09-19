import streamlit as st

from core.llm import LLMUnavailable
from core.sustainability import detect_anomalies, esg_narrative, monthly_summary
from ui import NAVY, URGENCY_COLOR, df, header, section_label

header("Sustainability", "Water & energy consumption by block vs baseline · Peninsular grid 0.74 kg CO₂/kWh")

readings = df("SELECT block, month, kwh, m3 FROM utility_readings ORDER BY month")
if readings.empty:
    st.info("No utility data found — run the data generator first.")
    st.stop()

months = sorted(readings["month"].unique(), reverse=True)
selected = st.selectbox("Month", months)

summary = monthly_summary(readings, selected)
anomalies_all = detect_anomalies(readings)
anomalies_month = anomalies_all[anomalies_all["month"] == selected] if not anomalies_all.empty else anomalies_all

# ── Top metrics ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
mom_kwh = f"{summary['mom_kwh_pct']:+.1f}% vs prev month" if summary["mom_kwh_pct"] is not None else None
mom_m3  = f"{summary['mom_m3_pct']:+.1f}% vs prev month"  if summary["mom_m3_pct"]  is not None else None
c1.metric("Electricity (kWh)", f"{summary['total_kwh']:,.0f}", mom_kwh)
c2.metric("Water (m³)",        f"{summary['total_m3']:,.0f}",  mom_m3)
c3.metric("CO₂e (tonnes)",     f"{summary['co2e_tonnes']:.2f}")
c4.metric("Anomalies this month", len(anomalies_month),
          "⚠ review below" if not anomalies_month.empty else None)

st.write("")

# ── Block breakdown ───────────────────────────────────────────────────────────
section_label("Block Breakdown", "fa-solid fa-table-cells")
block_rows = []
for block, data in summary["blocks"].items():
    block_rows.append({
        "Block": block,
        "Electricity (kWh)": f"{data['kwh']:,.0f}",
        "Water (m³)": f"{data['m3']:,.0f}",
        "CO₂e (tonnes)": f"{data['co2e_tonnes']:.2f}",
    })
if block_rows:
    import pandas as pd
    st.dataframe(pd.DataFrame(block_rows), use_container_width=True, hide_index=True)

# ── Trend ─────────────────────────────────────────────────────────────────────
st.write("")
section_label("Consumption Trend — All Blocks", "fa-solid fa-chart-line")
left, right = st.columns(2)
left.line_chart(readings.pivot(index="month", columns="block", values="kwh"), y_label="kWh")
right.line_chart(readings.pivot(index="month", columns="block", values="m3"), y_label="m³")

# ── Anomalies ─────────────────────────────────────────────────────────────────
st.write("")
section_label("Anomalies — All Months", "fa-solid fa-triangle-exclamation")
if anomalies_all.empty:
    st.markdown(
        f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
        f"padding:20px;text-align:center;color:#6B7A99;font-size:14px'>"
        f"No statistical anomalies detected (z-score threshold: 2.5).</div>",
        unsafe_allow_html=True)
else:
    for _, row in anomalies_all.sort_values("month", ascending=False).iterrows():
        direction = "above" if row["pct_vs_baseline"] > 0 else "below"
        color = URGENCY_COLOR["high"] if abs(row["pct_vs_baseline"]) > 30 else URGENCY_COLOR["medium"]
        util_label = "kWh" if row["utility"] == "kwh" else "m³"
        st.markdown(
            f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
            f"padding:12px 16px;margin-bottom:8px;border-left:4px solid {color}'>"
            f"<div style='font-weight:600;color:{NAVY};font-size:14px;margin-bottom:4px'>"
            f"Block {row['block']} · {row['month']} · {util_label}</div>"
            f"<div style='color:#2D3748;font-size:14px'>"
            f"{row['value']:,.0f} {util_label} — "
            f"<strong>{abs(row['pct_vs_baseline']):.1f}% {direction} baseline</strong>"
            f" ({row['baseline']:,.0f} {util_label} avg)</div>"
            f"</div>",
            unsafe_allow_html=True)

# ── ESG narrative ─────────────────────────────────────────────────────────────
st.write("")
section_label("ESG Narrative Report", "fa-solid fa-file-lines")
st.caption("AI-written monthly sustainability section — cite in your JMB committee report.")
if st.button("Generate ESG narrative for " + selected, type="primary"):
    with st.spinner("Claude is writing the sustainability report…"):
        try:
            narrative = esg_narrative(summary, anomalies_month)
            st.markdown(narrative)
        except LLMUnavailable as e:
            st.error(f"LLM unavailable: {e}")
