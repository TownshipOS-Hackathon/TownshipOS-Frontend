"""Group-admin contractor directory. Triage routes from this table, so edits change dispatch."""
import html as html_lib
import sqlite3

import streamlit as st

from core import org
from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, YELLOW, data_table, db, df,
                header, metric_card, section_label, topbar)

TRADES = ["lift", "plumbing", "electrical", "structural", "security", "landscaping",
          "cleanliness", "other"]
STATUSES = ["active", "probation", "suspended"]
STATUS_STYLE = {"active": ("#2E7D32", "#E8F5E9"), "probation": ("#B26A00", "#FFF8E1"),
                "suspended": ("#D32F2F", "#FDECEC")}

topbar("GROUP PORTFOLIO · CONTRACTOR DIRECTORY")
header("Contractor Directory", "Suppliers, trades, SLA terms and escalation contacts",
       eyebrow_tag="GROUP ADMIN", chips=[("DISPATCH SOURCE", "dot")])

conn = db()
cons = df("SELECT * FROM contractors ORDER BY trade, name")
load = df("SELECT contractor, COUNT(*) AS jobs FROM tickets "
          "WHERE status IN ('open','assigned') GROUP BY contractor").set_index("contractor")

active = cons[cons["status"] == "active"]
cards = [
    metric_card("Contractors", str(len(cons)), "on panel", "— Master agreements on file",
                "fa-solid fa-helmet-safety"),
    metric_card("Active", str(len(active)), "dispatchable",
                f"— {len(cons) - len(active)} suspended or on probation",
                "fa-regular fa-circle-check", "#2E7D32"),
    metric_card("Trades covered", str(cons["trade"].nunique()), f"of {len(TRADES)}",
                "— Gaps fall back to the PMO desk", "fa-solid fa-screwdriver-wrench"),
    metric_card("Avg. panel rating", f"{cons['rating'].mean():.1f}" if len(cons) else "—", "/ 5.0",
                "— Rolling 12-month performance", "fa-solid fa-star", YELLOW),
]
for col, card in zip(st.columns(4), cards):
    col.markdown(card, unsafe_allow_html=True)

# ── Directory ─────────────────────────────────────────────────────────────────
st.write("")
section_label("Panel Directory", "fa-solid fa-address-book",
              right="Triage dispatches to the top-rated active contractor per trade")
rows = []
for c in cons.itertuples():
    fg, bg = STATUS_STYLE.get(c.status, (MUTED, "#EEF2FA"))
    jobs = int(load["jobs"].get(c.name, 0))
    stars = "★" * int(round(c.rating)) + "☆" * (5 - int(round(c.rating)))
    rows.append([
        f"<span style='font-weight:700;color:{NAVY}'>{html_lib.escape(c.name)}</span>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:{FAINT}'>"
        f"{html_lib.escape(c.contract_ref or '—')}</div>",
        f"<span style='background:#EEF2FA;color:{NAVY};padding:3px 8px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{html_lib.escape(c.trade.upper())}</span>",
        f"<span style='font-size:12px'>{html_lib.escape(c.contact_person or '—')}</span>"
        f"<div style='font-size:11px;color:{FAINT}'>{html_lib.escape(c.email or '')}</div>",
        f"<span style='font-family:JetBrains Mono,monospace;font-size:11.5px'>"
        f"{html_lib.escape(c.phone or '—')}</span>",
        f"<span style='font-weight:700;color:{NAVY}'>{c.sla_hours} h</span>",
        f"<span style='color:{YELLOW};font-size:12px'>{stars}</span>"
        f"<div style='font-size:10.5px;color:{FAINT}'>{c.rating:.1f}</div>",
        (f"<span style='color:{URGENCY_COLOR['high']};font-weight:700'>{jobs}</span>" if jobs
         else f"<span style='color:{FAINT}'>0</span>"),
        f"<span style='background:{bg};color:{fg};padding:3px 9px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{html_lib.escape(c.status.upper())}</span>",
        f"<span style='font-size:10.5px;color:{FAINT}'>{html_lib.escape((c.last_update or '')[:10])}</span>",
    ])
st.markdown(data_table(
    ["Contractor", "Trade", "Contact Person", "Phone", "SLA", "Rating", "Open Jobs", "Status", "Updated"],
    rows, ["left", "left", "left", "left", "right", "right", "right", "right", "right"]),
    unsafe_allow_html=True)

# ── Trade coverage ────────────────────────────────────────────────────────────
missing = [t for t in TRADES if t not in set(active["trade"])]
if missing:
    st.markdown(
        f"<div style='background:{URGENCY_BG['medium']};border:1px solid {BORDER};border-left:4px solid "
        f"{URGENCY_COLOR['medium']};border-radius:8px;padding:11px 15px;margin-top:12px;font-size:12.5px;"
        f"color:#2D3748'><i class='fa-solid fa-triangle-exclamation' style='margin-right:9px;"
        f"color:{URGENCY_COLOR['medium']}'></i>No active contractor for: "
        f"<strong>{html_lib.escape(', '.join(missing))}</strong>. Tickets in these categories fall back "
        f"to the Property Management Office.</div>", unsafe_allow_html=True)

# ── Add ───────────────────────────────────────────────────────────────────────
with st.expander("Add a contractor to the panel"):
    with st.form("new_contractor", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        name = c1.text_input("Company name", placeholder="e.g. Perdana Lift Services Sdn Bhd")
        trade = c2.selectbox("Trade", TRADES)
        sla = c3.number_input("SLA (hours)", min_value=1, max_value=168, value=24)
        c4, c5, c6 = st.columns(3)
        person = c4.text_input("Contact person", placeholder="Full name")
        phone = c5.text_input("Phone", placeholder="+60 3-…")
        email = c6.text_input("Email", placeholder="ops@contractor.com.my")
        c7, c8 = st.columns([1, 2])
        rating = c7.number_input("Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
        ref = c8.text_input("Contract reference", placeholder="SDP/TRD/2026-001")
        notes = st.text_area("Notes", placeholder="Scope, exclusions, escalation path…", height=70)
        if st.form_submit_button("Add contractor", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Company name is required.")
            else:
                try:
                    org.add_contractor(conn, name, trade, person, phone, email,
                                       int(sla), float(rating), ref, notes)
                    st.success(f"{name.strip()} added to the panel.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"{name.strip()} is already on the panel.")

# ── Update ────────────────────────────────────────────────────────────────────
with st.expander("Update a contractor"):
    if cons.empty:
        st.info("No contractors on the panel yet.")
    else:
        labels = {f"{c.name} ({c.trade})": c for c in cons.itertuples()}
        picked = labels[st.selectbox("Contractor", list(labels), label_visibility="collapsed")]
        with st.form("edit_contractor"):
            c1, c2, c3 = st.columns(3)
            person = c1.text_input("Contact person", value=picked.contact_person or "")
            phone = c2.text_input("Phone", value=picked.phone or "")
            email = c3.text_input("Email", value=picked.email or "")
            c4, c5, c6 = st.columns(3)
            sla = c4.number_input("SLA (hours)", min_value=1, max_value=168, value=int(picked.sla_hours))
            rating = c5.number_input("Rating", min_value=0.0, max_value=5.0,
                                     value=float(picked.rating), step=0.1)
            status = c6.selectbox("Status", STATUSES, index=STATUSES.index(picked.status)
                                  if picked.status in STATUSES else 0)
            notes = st.text_area("Latest update / notes", value=picked.notes or "", height=70)
            if st.form_submit_button("Save changes", type="primary", use_container_width=True):
                org.update_contractor(conn, int(picked.id), contact_person=person, phone=phone,
                                      email=email, sla_hours=int(sla), rating=float(rating),
                                      status=status, notes=notes)
                st.success(f"{picked.name} updated.")
                st.rerun()

st.markdown(
    f"<div style='margin-top:14px;font-size:11px;color:{MUTED}'>"
    f"<i class='fa-solid fa-circle-info' style='margin-right:7px'></i>"
    f"Suspending a contractor removes them from triage dispatch; the next highest-rated active "
    f"contractor in that trade takes over.</div>", unsafe_allow_html=True)
