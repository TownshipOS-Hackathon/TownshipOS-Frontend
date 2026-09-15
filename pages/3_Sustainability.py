import streamlit as st

from core import sustainability as s
from core.llm import LLMUnavailable
from ui import df, header

st.set_page_config(page_title="Sustainability · TownshipOS", layout="wide")
header("Sustainability Intel", "Leak and energy anomalies by block, plus an auto-drafted ESG monthly section")

readings = df("SELECT block, month, kwh, m3 FROM utility_readings ORDER BY month")
month = st.selectbox("Month", sorted(readings["month"].unique(), reverse=True))
anoms = s.detect_anomalies(readings)
summary = s.monthly_summary(readings, month)

c1, c2, c3 = st.columns(3)
c1.metric("Electricity", f"{summary['total_kwh']:,.0f} kWh",
          f"{summary['mom_kwh_pct']} % MoM" if summary["mom_kwh_pct"] is not None else None, delta_color="inverse")
c2.metric("Water", f"{summary['total_m3']:,.0f} m³",
          f"{summary['mom_m3_pct']} % MoM" if summary["mom_m3_pct"] is not None else None, delta_color="inverse")
c3.metric("Scope 2 emissions", f"{summary['co2e_tonnes']:,.1f} tCO₂e",
          help=f"Grid factor {s.GRID_FACTOR_KG_PER_KWH} kgCO₂e/kWh (Energy Commission, Peninsular Malaysia)")

for a in anoms.sort_values("month", ascending=False).itertuples():
    kind = "probable leak" if a.utility == "m3" else "probable equipment fault"
    st.error(f"**Block {a.block} {s.UTILITIES[a.utility]} {a.pct_vs_baseline:+.0f} % vs 12-month baseline** "
             f"in {a.month} — {kind} (z = {a.z})")

l, r = st.columns(2)
l.line_chart(readings.pivot(index="month", columns="block", values="kwh"), y_label="kWh")
r.line_chart(readings.pivot(index="month", columns="block", values="m3"), y_label="m³")

if st.button("Generate ESG monthly section", type="primary"):
    try:
        with st.spinner("Drafting…"):
            st.markdown(s.esg_narrative(summary, anoms[anoms["month"] <= month]))
    except LLMUnavailable as e:
        st.error(f"Report service unavailable: {e}")
