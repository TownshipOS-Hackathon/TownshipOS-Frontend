import html

import streamlit as st

from ui import URGENCY_COLOR, badge, df, header, scored_assets

st.set_page_config(page_title="TownshipOS", page_icon="🏙️", layout="wide")
header("One AI brain for running a township", "Sime Darby Property University Hackathon · demo township: Serenia Heights")

tickets = df("SELECT * FROM tickets ORDER BY created_at DESC")
msgs = 80  # illustrative: messages received across WhatsApp/email/phone today
c1, c2, c3, c4 = st.columns(4)
c1.metric("Messages today", msgs)
c2.metric("Tickets created", len(tickets), f"{msgs - len(tickets)} deduplicated / informational")
urgent, human = int(tickets["urgency"].isin(["high", "emergency"]).sum()), int(tickets["needs_human"].sum())
c3.metric("Urgent (high + emergency)", urgent)
c4.metric("Need a human", human)

top = scored_assets()[0].iloc[0]
st.subheader("Morning brief")
st.markdown(
    "- **06:12** Leak photo from unit 12-3 triaged → AquaFix notified, resident replied in BM & EN\n"
    f"- **07:00** Overnight asset re-scoring flags **{top['name']}** at **{top['risk']:.0%}** 30-day failure risk\n"
    "- **07:00** Sustainability flags **Block C water +40 %** vs baseline — probable leak\n"
    f"- **09:30** You are here. {urgent} urgent tickets, {human} need a decision.")

st.subheader("Latest tickets")
for r in tickets.head(8).itertuples():
    st.markdown(f"{badge(r.urgency or 'untriaged', URGENCY_COLOR.get(r.urgency, '#607D8B'))} "
                f"**#{r.id}** {html.escape(r.raw_text)}  \n<small>{r.category} · {r.contractor} · SLA {r.sla_hours} h</small>",
                unsafe_allow_html=True)

st.subheader("Open issue map")
locs = df("SELECT latitude AS lat, longitude AS lon FROM tickets "
          "WHERE status IN ('open','assigned') AND latitude IS NOT NULL")
if locs.empty:
    st.caption("No geo-tagged tickets yet — residents can share location via the Report page.")
else:
    st.map(locs, latitude="lat", longitude="lon", zoom=16)
