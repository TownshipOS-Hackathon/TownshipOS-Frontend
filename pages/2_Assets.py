import pandas as pd
import streamlit as st

from core import maintenance as m
from ui import db, df, header, scored_assets

header("Predictive Maintenance", "30-day failure risk per asset, from 24 months of service logs")

scored, model, metrics = scored_assets()
logs = df("SELECT * FROM service_logs")

top = scored.iloc[0]
st.markdown(f"### ⚠️ {top['name']} — **{top['risk']:.0%}** failure risk in 30 days")
st.caption("Drivers: " + ", ".join(d.replace("_", " ") for d in top["top_drivers"]) + f" · Contractor: {top['contractor']}")
if st.button("Create pre-emptive work order", type="primary"):
    wid = m.create_work_order(db(), top["asset_id"], float(top["risk"]),
                              "Predicted failure risk; drivers: " + ", ".join(top["top_drivers"]))
    st.success(f"Work order #{wid} created for {top['contractor']} (scheduled, not emergency).")

c1, c2 = st.columns([2, 1])
with c1:
    st.subheader("Risk ranking")
    show = scored[["asset_id", "name", "block", "type", "risk", "top_drivers", "contractor"]].copy()
    show["risk"] = (show["risk"] * 100).round(0)
    st.dataframe(show, use_container_width=True, hide_index=True,
                 column_config={"risk": st.column_config.ProgressColumn("risk %", min_value=0, max_value=100)})
with c2:
    st.subheader("What the model learned")
    imp = pd.Series(dict(zip(m.FEATURES, model[-1].feature_importances_))).sort_values()
    st.bar_chart(imp)
    if metrics:
        st.caption(f"Cross-validated AUC {metrics['auc']:.2f} · {metrics['n_rows']} training rows")

pick = st.selectbox("Service history", scored["asset_id"])
st.dataframe(logs[logs["asset_id"] == pick].sort_values("date", ascending=False), use_container_width=True, hide_index=True)
st.subheader("Open work orders")
st.dataframe(df("SELECT * FROM work_orders ORDER BY created_at DESC"), use_container_width=True, hide_index=True)
