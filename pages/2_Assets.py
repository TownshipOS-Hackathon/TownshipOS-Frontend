import html as html_lib

import streamlit as st

from core import maintenance as m
from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, YELLOW, db, df, header,
                scored_assets, section_label, topbar)

KIND_STYLE = {"breakdown": ("CORRECTIVE", "#D32F2F", "#FDECEC"),
              "scheduled": ("PREVENTIVE", "#2A4B8D", "#E8EEFB")}

topbar()
header("Predictive Maintenance", "30-day failure risk per asset, from 24 months of service logs",
       chips=[("ML CORE: ONLINE", "dot"), ("Model: GBM-Township-v2.4", "plain")])

scored, model, metrics = scored_assets()
logs = df("SELECT * FROM service_logs")
top = scored.iloc[0]


def risk_color(pct: float) -> str:
    return (URGENCY_COLOR["emergency"] if pct >= 70 else
            URGENCY_COLOR["high"] if pct >= 55 else
            URGENCY_COLOR["medium"] if pct >= 35 else "#546E7A")


def cell(inner: str, extra: str = "") -> str:
    return (f"<td style='padding:10px;border-top:1px solid {BORDER};vertical-align:middle;"
            f"font-size:12.5px;color:#2D3748;{extra}'>{inner}</td>")


def table(heads: list[str], rows: str) -> str:
    head = "".join(
        f"<th style='text-align:left;padding:9px 10px;font-size:9.5px;letter-spacing:0.8px;"
        f"color:{MUTED};font-weight:700;text-transform:uppercase;white-space:nowrap'>{h}</th>" for h in heads)
    return (f"<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse'>"
            f"<thead style='background:#F4F6FB'><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>")


# ── Critical asset banner ─────────────────────────────────────────────────────
with st.container(border=True):
    head, act = st.columns([2.4, 1])
    with head:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap'>"
            f"<span style='font-size:18px;font-weight:700;color:{NAVY}'>"
            f"<i class='fa-solid fa-triangle-exclamation' style='color:{YELLOW};margin-right:8px'></i>"
            f"{html_lib.escape(str(top['name']))} — {top['risk']:.0%} failure risk in 30 days</span>"
            f"<span style='background:{URGENCY_BG['emergency']};color:{URGENCY_COLOR['emergency']};"
            f"padding:3px 9px;border-radius:5px;font-size:10px;font-weight:700;letter-spacing:0.4px'>"
            f"CRITICAL THRESHOLD EXCEEDED</span></div>"
            f"<div style='font-size:12.5px;color:{MUTED};margin-top:6px'>Drivers: "
            f"{', '.join(d.replace('_', ' ') for d in top['top_drivers'])} &middot; Contractor: "
            f"<span style='color:{NAVY};font-weight:600'>{html_lib.escape(str(top['contractor']))}</span></div>",
            unsafe_allow_html=True)
    with act:
        made = st.button("Create pre-emptive work order", type="primary", use_container_width=True)

    if made:
        wid = m.create_work_order(db(), top["asset_id"], float(top["risk"]),
                                  "Predicted failure risk; drivers: " + ", ".join(top["top_drivers"]))
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;"
            f"background:#EEF2FA;border-radius:8px;padding:10px 14px;margin-top:10px'>"
            f"<span style='font-size:12.5px;color:#2D3748'>"
            f"<i class='fa-regular fa-circle-check' style='color:#2E7D32;margin-right:8px'></i>"
            f"Work order #{wid} created for {html_lib.escape(str(top['contractor']))} "
            f"(scheduled, not emergency)</span>"
            f"<span style='font-size:11px;color:{MUTED};white-space:nowrap'>Target SLA: 72 Hours</span></div>",
            unsafe_allow_html=True)

st.write("")
rank_col, shap_col = st.columns([2, 1], gap="medium")

# ── Risk ranking ──────────────────────────────────────────────────────────────
with rank_col:
    section_label("Risk Ranking", "fa-solid fa-ranking-star", right="Sorted by 30-Day Risk Probability")
    rows = ""
    for a in scored.head(6).itertuples():
        pct = a.risk * 100
        col = risk_color(pct)
        bar = (f"<div style='display:flex;align-items:center;gap:9px'>"
               f"<div style='flex:1;min-width:52px;height:7px;background:#EEF2FA;border-radius:4px;"
               f"overflow:hidden'><div style='width:{pct:.0f}%;height:100%;background:{col};"
               f"border-radius:4px'></div></div>"
               f"<span style='color:{col};font-weight:700;font-size:12px'>{pct:.0f}%</span></div>")
        rows += "<tr>" + "".join([
            cell(f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>"
                 f"{html_lib.escape(str(a.asset_id))}</span>"),
            cell(f"<span style='font-size:12px'>{html_lib.escape(str(a.name))}</span>"),
            cell(f"<span style='color:{MUTED};font-size:12px'>{html_lib.escape(str(a.block))}</span>"),
            cell(f"<span style='background:#EEF2FA;color:{NAVY};padding:3px 8px;border-radius:5px;"
                 f"font-size:10px;font-weight:700;letter-spacing:0.3px'>{str(a.type).upper()}</span>"),
            cell(bar, "min-width:130px"),
            cell(f"<span style='color:{MUTED};font-size:11.5px'>"
                 f"{', '.join(d.replace('_', ' ') for d in a.top_drivers)}</span>"),
        ]) + "</tr>"
    st.markdown(table(["Asset_ID", "Name", "Block", "Type", "Risk %", "Top_Drivers"], rows),
                unsafe_allow_html=True)

# ── Feature importances ───────────────────────────────────────────────────────
with shap_col:
    section_label("What the Model Learned", "fa-solid fa-circle-nodes", right="Feature Weights")
    imps = sorted(zip(m.FEATURES, model[-1].feature_importances_), key=lambda x: -x[1])
    peak = max(v for _, v in imps) or 1
    body = ""
    for name, val in imps:
        body += (
            f"<div style='margin-bottom:11px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:11.5px;color:#2D3748'>{name}</span>"
            f"<span style='font-weight:700;font-size:12px;color:{NAVY}'>{val:.2f}</span></div>"
            f"<div style='height:6px;background:#EEF2FA;border-radius:3px;overflow:hidden'>"
            f"<div style='width:{val / peak * 100:.0f}%;height:100%;background:{NAVY};border-radius:3px'></div>"
            f"</div></div>")
    auc = f"Cross-validated AUC {metrics['auc']:.2f} · {metrics['n_rows']} training rows" if metrics \
        else "Loaded from cached model artefact"
    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 16px'>"
        f"<div style='display:flex;justify-content:space-between;font-size:9.5px;letter-spacing:0.7px;"
        f"color:{MUTED};font-weight:700;text-transform:uppercase;margin-bottom:12px'>"
        f"<span>Feature Predictor</span><span>Importance Weight</span></div>{body}"
        f"<div style='border-top:1px solid {BORDER};padding-top:10px;font-size:11px;color:{MUTED}'>"
        f"<i class='fa-regular fa-circle-check' style='margin-right:7px'></i>{auc}</div></div>",
        unsafe_allow_html=True)

# ── Service history ───────────────────────────────────────────────────────────
st.write("")
section_label("Asset Service History", "fa-solid fa-clock-rotate-left", right="Audit Logs & Corrective Cycles")
with st.container(border=True):
    pick_col, ingest_col = st.columns([2, 1])
    labels = {f"{a.asset_id} ({a.name})": a.asset_id for a in scored.itertuples()}
    chosen = pick_col.selectbox("Service history for:", list(labels))
    ingest_col.markdown(
        f"<div style='text-align:right;padding-top:28px;font-size:11px;color:{MUTED}'>"
        f"<span style='width:6px;height:6px;border-radius:50%;background:{YELLOW};display:inline-block;"
        f"margin-right:7px'></span>Last telemetry ingest: 14 mins ago</div>", unsafe_allow_html=True)

    hist = logs[logs["asset_id"] == labels[chosen]].sort_values("date", ascending=False).head(6)
    rows = ""
    for h in hist.itertuples():
        label, fg, bg = KIND_STYLE.get(h.kind, ("ROUTINE", MUTED, "#EEF2FA"))
        vib_col = URGENCY_COLOR["emergency"] if h.vibration_score >= 0.9 else "#2D3748"
        rows += "<tr>" + "".join([
            cell(f"<span style='font-family:JetBrains Mono,monospace;font-size:12px'>{h.date}</span>"),
            cell(f"<span style='background:{bg};color:{fg};padding:3px 8px;border-radius:5px;"
                 f"font-size:10px;font-weight:700'>{label}</span>"),
            cell(f"{h.runtime_hours:,.0f} h", "text-align:right"),
            cell(f"<span style='color:{vib_col};font-weight:600'>{h.vibration_score:.2f} mm/s</span>",
                 "text-align:right"),
            cell(f"<span style='color:{MUTED};font-size:12px'>{html_lib.escape(h.notes or '—')}</span>"),
        ]) + "</tr>"
    st.markdown(table(["Date", "Kind", "Runtime Hours", "Vibration Score", "Technician / Notes"], rows),
                unsafe_allow_html=True)

    st.write("")
    wo = df("SELECT w.id, w.asset_id, w.reason, w.created_at, w.risk, w.status, a.contractor "
            "FROM work_orders w LEFT JOIN assets a ON a.id = w.asset_id ORDER BY w.created_at DESC LIMIT 6")
    section_label("Open Work Orders", "fa-regular fa-rectangle-list",
                  right=f"{len(wo)} active dispatch{'es' if len(wo) != 1 else ''}")
    if wo.empty:
        st.markdown(f"<div style='padding:16px;text-align:center;color:{MUTED};font-size:12.5px'>"
                    f"No work orders yet — raise one from the critical asset above.</div>",
                    unsafe_allow_html=True)
    else:
        rows = ""
        for w in wo.itertuples():
            pr_fg, pr_bg = ((URGENCY_COLOR["emergency"], URGENCY_BG["emergency"]) if w.risk >= 0.7
                            else (URGENCY_COLOR["medium"], URGENCY_BG["medium"]))
            rows += "<tr>" + "".join([
                cell(f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>"
                     f"WO-{w.id:04d}</span>"),
                cell(f"<span style='font-size:12px'>{html_lib.escape(str(w.asset_id))}</span>"),
                cell(f"<span style='color:{MUTED};font-size:11.5px'>"
                     f"{html_lib.escape((w.reason or '')[:46])}</span>"),
                cell(f"<span style='font-family:JetBrains Mono,monospace;font-size:11.5px'>"
                     f"{(w.created_at or '')[:10]}</span>"),
                cell(f"<span style='background:{pr_bg};color:{pr_fg};padding:3px 8px;border-radius:5px;"
                     f"font-size:10px;font-weight:700'>{'HIGH' if w.risk >= 0.7 else 'MEDIUM'}</span>"),
                cell(f"<span style='background:#E8EEFB;color:#2A4B8D;padding:3px 8px;border-radius:5px;"
                     f"font-size:10px;font-weight:700'>{(w.status or 'open').upper()}</span>"),
                cell(f"<span style='font-size:11.5px'>{html_lib.escape(w.contractor or '—')}</span>"),
            ]) + "</tr>"
        st.markdown(table(["WO ID", "Asset", "Type", "Scheduled Date", "Priority", "Status",
                           "Assigned Contractor"], rows), unsafe_allow_html=True)
