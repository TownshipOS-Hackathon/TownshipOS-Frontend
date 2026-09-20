import html as html_lib

import pandas as pd
import pydeck as pdk
import streamlit as st

from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, YELLOW, df, header,
                metric_card, scope_picker, scope_sql, scored_assets, section_label, topbar,
                urgency_pill)

DOTS = ["#1A2332", "#3F51B5", YELLOW, "#6A1B9A", "#00897B", "#C2185B", "#5D4037", "#455A64"]

home = df("SELECT name, district FROM projects WHERE id = ?",
          (st.session_state.get("project_id"),))
topbar(f"{home['name'].iloc[0].upper()} · {home['district'].iloc[0].upper()}" if not home.empty
       else "TOWNSHIP OPERATIONS")
header("One AI brain for running a township",
       "Sime Darby Property University Hackathon · AI-assisted township operations",
       eyebrow_tag="LIVE OPERATIONS",
       chips=[("SYNC: OPERATIONAL", "dot"), ("100% Telemetry", "plain")])

project_id, building_ids = scope_picker()
scope_clause, scope_params = scope_sql("building_id", building_ids)

blds = df("SELECT * FROM buildings WHERE project_id = ? ORDER BY block", (project_id,))
BLOCK_NAMES = {b.block: b.name for b in blds.itertuples()}
BLOCK_DOT = {b.block: DOTS[i % len(DOTS)] for i, b in enumerate(blds.itertuples())}
BID_BLOCK = {b.id: b.block for b in blds.itertuples()}

tickets = df(f"SELECT * FROM tickets WHERE {scope_clause} ORDER BY created_at DESC", scope_params)
msgs = 80
urgent = int(tickets["urgency"].isin(["high", "emergency"]).sum())
human = int(tickets["needs_human"].sum())

# ── Cockpit metrics ───────────────────────────────────────────────────────────
cards = [
    metric_card("Messages today", str(msgs), "inbound", "— Baseline steady", "fa-regular fa-comment"),
    metric_card("Tickets created", str(len(tickets)), "active",
                f"<span style='color:{YELLOW}'>▼</span> +{msgs - len(tickets)} deduplicated / informational",
                "fa-regular fa-clipboard"),
    metric_card("Urgent (high + emergency)", str(urgent), "tickets", "— SLA breach countdown active",
                "fa-solid fa-triangle-exclamation", URGENCY_COLOR["emergency"]),
    metric_card("Need a human", str(human), "escalations", "— Township FM sign-off req.",
                "fa-regular fa-face-frown", "#6A1B9A"),
]
for col, card in zip(st.columns(4), cards):
    col.markdown(card, unsafe_allow_html=True)

st.write("")
left, right = st.columns([1.65, 1], gap="medium")

# ── Morning brief + tickets ───────────────────────────────────────────────────
with left:
    in_scope = scored_assets()[0]
    in_scope = in_scope[in_scope["building_id"].isin(building_ids)]
    top = in_scope.iloc[0] if not in_scope.empty else None
    risk_pill = ("" if top is None else
                 f"<span style='background:{URGENCY_BG['emergency']};color:{URGENCY_COLOR['emergency']};"
                 f"padding:2px 7px;border-radius:4px;font-size:11.5px;font-weight:600'>"
                 f"{top['risk']:.0%} 30-day failure risk</span>")

    def brief_row(time: str, body: str, highlight: bool = False) -> str:
        bg = "background:#EEF2FA;border-radius:6px;" if highlight else ""
        return (f"<div style='display:flex;gap:14px;padding:7px 10px;{bg}'>"
                f"<span style='font-family:JetBrains Mono,monospace;font-size:12px;font-weight:600;"
                f"color:{NAVY};flex-shrink:0'>{time}</span>"
                f"<span style='font-size:13px;color:#2D3748;line-height:1.55'>{body}</span></div>")

    # Anomaly line reflects this township's own readings, not a hardcoded block.
    anom = df(f"SELECT block, month, m3 FROM utility_readings WHERE {scope_clause} "
              "ORDER BY month DESC LIMIT 200", scope_params)
    spike = ""
    if not anom.empty:
        latest_month = anom["month"].max()
        cur = anom[anom["month"] == latest_month]
        base = anom[anom["month"] < latest_month].groupby("block")["m3"].mean()
        worst, worst_pct = None, 0.0
        for r in cur.itertuples():
            b = base.get(r.block)
            if b and (pct := 100 * (r.m3 - b) / b) > worst_pct:
                worst, worst_pct = r.block, pct
        spike = (f"Sustainability flags <strong>Block {worst} water +{worst_pct:.0f} %</strong> vs "
                 f"baseline &mdash; probable hidden leak detected." if worst and worst_pct > 15
                 else "Sustainability reports all blocks within baseline tolerance this month.")

    rows = brief_row("06:12", "Leak photo from unit 12-3 triaged &rarr; <strong>AquaFix</strong> notified, "
                              "resident replied in BM &amp; EN")
    if top is not None:
        rows += brief_row("07:00", f"Overnight asset re-scoring flags "
                                   f"<strong>{html_lib.escape(str(top['name']))}</strong> at {risk_pill}")
    rows += (brief_row("07:00", spike)
             + brief_row("09:30", f"You are here. <strong>{urgent} urgent tickets</strong>, "
                                  f"{human} need a decision.", highlight=True))
    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 12px 12px;"
        f"margin-bottom:18px'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;padding:0 8px 8px'>"
        f"<span style='font-size:11px;font-weight:700;letter-spacing:1.2px;color:{MUTED}'>"
        f"<i class='fa-regular fa-sun' style='margin-right:8px;color:{YELLOW}'></i>MORNING BRIEF</span>"
        f"<span style='background:#EEF2FA;color:{MUTED};border-radius:5px;padding:3px 8px;"
        f"font-size:9.5px;font-weight:700;letter-spacing:0.5px'>AUTOMATED DIGEST · TOWNSHIP CORE</span>"
        f"</div>{rows}</div>",
        unsafe_allow_html=True)

    section_label("Latest Tickets", "fa-solid fa-ticket", right=f"{min(len(tickets), 8)} Live")
    for r in tickets.head(8).itertuples():
        urg = (r.urgency or "untriaged").lower()
        col = URGENCY_COLOR.get(urg, "#546E7A")
        sla = f"SLA {r.sla_hours} h" if r.sla_hours else "SLA Pending Review"
        sla_html = (f"<span style='color:{col};font-size:11.5px;font-weight:600'>"
                    f"{'● ' if urg == 'emergency' else ''}{sla}</span>")
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-left:4px solid {col};"
            f"border-radius:8px;padding:11px 14px;margin-bottom:8px'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px'>"
            f"<span style='display:flex;align-items:center;gap:9px'>{urgency_pill(urg)}"
            f"<span style='font-weight:700;color:{NAVY};font-size:13.5px'>#{r.id}</span></span>{sla_html}</div>"
            f"<div style='color:#2D3748;font-size:13px;line-height:1.5;margin-bottom:6px'>"
            f"{html_lib.escape((r.raw_text or '')[:110])}</div>"
            f"<div style='font-size:11.5px;color:{MUTED};display:flex;gap:8px;flex-wrap:wrap'>"
            f"<span style='color:{col};font-weight:600'>{r.category or '—'}</span><span>·</span>"
            f"<span>{r.contractor or '—'}</span><span>·</span>"
            f"<span style='color:{col};font-weight:600'>{sla}</span></div></div>",
            unsafe_allow_html=True)

# ── Map + per-block rollup ────────────────────────────────────────────────────
with right:
    section_label("Open Issue Map", "fa-solid fa-map-location-dot", right="LIVE GEOSPATIAL VIEW")
    locs = df("SELECT id, urgency, latitude AS lat, longitude AS lon FROM tickets "
              f"WHERE {scope_clause} AND status IN ('open','assigned') AND latitude IS NOT NULL",
              scope_params)

    legend = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:5px;margin-right:12px'>"
        f"<span style='width:7px;height:7px;border-radius:50%;background:{URGENCY_COLOR[u]}'></span>"
        f"<span style='font-size:10.5px;color:{MUTED};font-weight:600'>{lbl}</span></span>"
        for u, lbl in [("emergency", "Emerg"), ("high", "High"), ("medium", "Med"), ("low", "Low")])
    st.markdown(f"<div style='padding:2px 0 8px'>{legend}</div>", unsafe_allow_html=True)

    if locs.empty:
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:32px;"
            f"text-align:center;color:{MUTED};font-size:13px'>No geo-tagged tickets yet — residents can "
            f"share location via the Report page.</div>",
            unsafe_allow_html=True)
    else:
        def rgb(u):
            h = URGENCY_COLOR.get((u or "").lower(), "#546E7A").lstrip("#")
            return [int(h[i:i + 2], 16) for i in (0, 2, 4)]

        locs = locs.assign(color=locs["urgency"].map(rgb), label=locs["id"].map(lambda i: f"#{i}"))
        st.pydeck_chart(pdk.Deck(
            map_style="light",
            initial_view_state=pdk.ViewState(latitude=float(locs["lat"].mean()),
                                             longitude=float(locs["lon"].mean()), zoom=15.4, pitch=0),
            layers=[
                pdk.Layer("ScatterplotLayer", locs, get_position="[lon, lat]", get_fill_color="color",
                          get_radius=22, radius_min_pixels=11, stroked=True,
                          get_line_color=[255, 255, 255], line_width_min_pixels=2),
                pdk.Layer("TextLayer", locs, get_position="[lon, lat]", get_text="label",
                          get_color=[255, 255, 255], get_size=10, get_alignment_baseline="'center'"),
            ],
            tooltip={"text": "Ticket {label} · {urgency}"},
        ), height=290)
    st.markdown(
        f"<div style='font-size:10.5px;color:{FAINT};margin:-4px 0 18px'>"
        f"Target zone: Serenia Precinct 1 &amp; 2</div>", unsafe_allow_html=True)

    open_t = df(f"SELECT urgency, building_id FROM tickets WHERE {scope_clause} "
                "AND status IN ('open','assigned')", scope_params)
    counts = {b: {"open": 0, "emerg": 0} for b in BLOCK_NAMES}
    for t in open_t.itertuples():
        b = BID_BLOCK.get(t.building_id)
        if b is None:
            continue
        counts[b]["open"] += 1
        counts[b]["emerg"] += int(t.urgency == "emergency")

    rows = ""
    for b, c in counts.items():
        emerg = c["emerg"]
        chip_fg, chip_bg = ((URGENCY_COLOR["emergency"], URGENCY_BG["emergency"]) if emerg
                            else (MUTED, "#EEF2FA"))
        label = f"{c['open']} open" + (f" ({emerg} Emerg)" if emerg else "")
        rows += (
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:8px;"
            f"padding:9px 14px;border-bottom:1px solid {BORDER}'>"
            f"<span style='display:flex;align-items:center;gap:8px;min-width:0'>"
            f"<span style='width:7px;height:7px;border-radius:50%;background:{BLOCK_DOT[b]};flex-shrink:0'></span>"
            f"<span style='font-size:12.5px;font-weight:700;color:{NAVY}'>Block {b}</span>"
            f"<span style='font-size:11px;color:{FAINT};white-space:nowrap'>{BLOCK_NAMES[b]}</span></span>"
            f"<span style='background:{chip_bg};color:{chip_fg};border-radius:5px;padding:3px 9px;"
            f"font-size:11px;font-weight:700;white-space:nowrap'>{label}</span></div>")

    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;overflow:hidden'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;padding:11px 14px;"
        f"border-bottom:1px solid {BORDER}'>"
        f"<span style='font-size:10.5px;font-weight:700;letter-spacing:1px;color:{MUTED}'>"
        f"OPEN TICKETS BY BLOCK</span>"
        f"<span style='font-size:10px;color:{FAINT};font-weight:600'>{len(counts)} Sectors Active</span></div>"
        f"{rows}"
        f"<div style='display:flex;align-items:center;justify-content:space-between;padding:10px 14px'>"
        f"<span style='font-size:11.5px;color:{MUTED}'>Common Area Facilities</span>"
        f"<span style='font-size:11.5px;color:{NAVY};font-weight:600'>Clubhouse &amp; Gates</span></div></div>",
        unsafe_allow_html=True)
