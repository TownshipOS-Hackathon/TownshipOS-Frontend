import html as html_lib

import streamlit as st

from ui import NAVY, URGENCY_COLOR, badge, df, header, scored_assets, section_label

header("One AI brain for running a township",
       "Sime Darby Property University Hackathon · demo township: Serenia Heights")

tickets = df("SELECT * FROM tickets ORDER BY created_at DESC")
msgs = 80
c1, c2, c3, c4 = st.columns(4)
c1.metric("Messages today", msgs)
c2.metric("Tickets created", len(tickets), f"{msgs - len(tickets)} deduplicated / informational")
urgent = int(tickets["urgency"].isin(["high", "emergency"]).sum())
human = int(tickets["needs_human"].sum())
c3.metric("Urgent (high + emergency)", urgent)
c4.metric("Need a human", human)

st.write("")

# ── Morning brief ─────────────────────────────────────────────────────────────
top = scored_assets()[0].iloc[0]
top_name = html_lib.escape(str(top["name"]))
st.markdown(
    f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;padding:16px 20px;margin-bottom:20px'>"
    f"<div style='font-size:11px;font-weight:600;letter-spacing:1.5px;color:#6B7A99;"
    f"text-transform:uppercase;margin-bottom:12px'>Morning Brief</div>"
    f"<ul style='margin:0;padding-left:18px;color:#2D3748;font-size:14px;line-height:1.9'>"
    f"<li><strong>06:12</strong> Leak photo from unit 12-3 triaged &rarr; AquaFix notified, resident replied in BM &amp; EN</li>"
    f"<li><strong>07:00</strong> Overnight asset re-scoring flags <strong>{top_name}</strong>"
    f" at <strong>{top['risk']:.0%}</strong> 30-day failure risk</li>"
    f"<li><strong>07:00</strong> Sustainability flags <strong>Block C water +40 %</strong> vs baseline &mdash; probable leak</li>"
    f"<li><strong>09:30</strong> You are here. {urgent} urgent tickets, {human} need a decision.</li>"
    f"</ul></div>",
    unsafe_allow_html=True)

# ── Latest tickets ────────────────────────────────────────────────────────────
section_label("Latest Tickets", "fa-solid fa-ticket")
for r in tickets.head(8).itertuples():
    urg = r.urgency or "untriaged"
    col = URGENCY_COLOR.get(r.urgency, "#607D8B")
    text = html_lib.escape((r.raw_text or "")[:110])
    st.markdown(
        f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
        f"padding:12px 16px;margin-bottom:8px;border-left:4px solid {col}'>"
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>"
        f"{badge(urg, col)}"
        f"<span style='font-weight:600;color:{NAVY};font-size:14px'>#{r.id}</span>"
        f"</div>"
        f"<div style='color:#2D3748;font-size:14px;line-height:1.5;margin-bottom:4px'>{text}</div>"
        f"<div style='color:#6B7A99;font-size:12px'>"
        f"{r.category or '—'} &middot; {r.contractor or '—'} &middot; SLA {r.sla_hours or '—'} h"
        f"</div></div>",
        unsafe_allow_html=True)

# ── Open issue map ────────────────────────────────────────────────────────────
st.write("")
section_label("Open Issue Map", "fa-solid fa-map-location-dot")
locs = df("SELECT latitude AS lat, longitude AS lon FROM tickets "
          "WHERE status IN ('open','assigned') AND latitude IS NOT NULL")
if locs.empty:
    st.markdown(
        f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
        f"padding:32px;text-align:center;color:#6B7A99;font-size:14px'>"
        f"No geo-tagged tickets yet &mdash; residents can share location via the Report page.</div>",
        unsafe_allow_html=True)
else:
    st.map(locs, latitude="lat", longitude="lon", zoom=16)
