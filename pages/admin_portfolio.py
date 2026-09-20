"""Group-admin CRUD for townships and the buildings inside them."""
import html as html_lib
import sqlite3

import streamlit as st

from core import org
from ui import BORDER, FAINT, MUTED, NAVY, data_table, db, df, header, section_label, topbar, txt

BUILDING_TYPES = ["Residential Tower", "Serviced Apartment", "Townhouse Cluster",
                  "Commercial Block", "Clubhouse", "Infrastructure"]

topbar("GROUP PORTFOLIO · TOWNS & BUILDINGS")
header("Towns & Buildings", "Register townships and the blocks that sit inside them",
       eyebrow_tag="GROUP ADMIN", chips=[("PORTFOLIO REGISTRY", "dot")])

conn = db()
projects = df("SELECT * FROM projects ORDER BY name")
counts = df("SELECT project_id, COUNT(*) AS n, COALESCE(SUM(units),0) AS units "
            "FROM buildings GROUP BY project_id").set_index("project_id")

# ── Townships ─────────────────────────────────────────────────────────────────
section_label("Registered Townships", "fa-solid fa-city", right=f"{len(projects)} active")
rows = []
for p in projects.itertuples():
    n = int(counts["n"].get(p.id, 0))
    u = int(counts["units"].get(p.id, 0))
    rows.append([
        f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>{p.id}</span>",
        f"<span style='font-weight:700;color:{NAVY}'>{txt(p.name)}</span>",
        f"<span style='font-size:12px'>{txt(p.district, '')} {txt(p.state, '')}</span>",
        f"<span style='font-size:12px'>{txt(p.manager)}</span>",
        str(n), f"{u:,}",
        f"<span style='background:#E8F5E9;color:#2E7D32;padding:3px 9px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{txt(p.status, 'ACTIVE').upper()}</span>",
    ])
st.markdown(data_table(["Code", "Township", "Location", "FM Manager", "Blocks", "Units", "Status"],
                       rows, ["left", "left", "left", "left", "right", "right", "right"]),
            unsafe_allow_html=True)

with st.expander("Register a new township"):
    with st.form("new_project", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        pid = c1.text_input("Township code", placeholder="e.g. CTY", max_chars=6)
        name = c2.text_input("Township name", placeholder="e.g. City of Elmina")
        manager = c3.text_input("FM manager", placeholder="Full name")
        c4, c5 = st.columns(2)
        state = c4.text_input("State", value="Selangor")
        district = c5.text_input("District", placeholder="e.g. Shah Alam")
        if st.form_submit_button("Register township", type="primary", use_container_width=True):
            if not (pid.strip() and name.strip() and state.strip()):
                st.error("Township code, name and state are required.")
            else:
                try:
                    org.add_project(conn, pid, name, state, district, manager)
                    st.success(f"Township {pid.strip().upper()} registered.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"Township code {pid.strip().upper()} already exists.")

# ── Buildings ─────────────────────────────────────────────────────────────────
st.write("")
if projects.empty:
    st.info("Register a township first, then add its buildings.")
    st.stop()

names = {p.name: p.id for p in projects.itertuples()}
pick_col, _ = st.columns([1.2, 3])
chosen = pick_col.selectbox("Township", list(names))
pid = names[chosen]

blds = df("SELECT * FROM buildings WHERE project_id = ? ORDER BY block", (pid,))
section_label("Buildings", "fa-solid fa-building",
              right=f"{len(blds)} block{'s' if len(blds) != 1 else ''} in {html_lib.escape(chosen)}")
if blds.empty:
    st.markdown(
        f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:22px;"
        f"text-align:center;color:{MUTED};font-size:13px'>No buildings registered for this township "
        f"yet — add the first block below.</div>", unsafe_allow_html=True)
else:
    rows = [[
        f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>{b.id}</span>",
        f"<span style='font-weight:700;color:{NAVY}'>Block {b.block}</span>",
        f"<span style='font-size:12px'>{html_lib.escape(b.name)}</span>",
        f"<span style='background:#EEF2FA;color:{NAVY};padding:3px 8px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{html_lib.escape(b.type.upper())}</span>",
        f"{b.units:,}", str(b.floors),
        (f"<span style='font-family:JetBrains Mono,monospace;font-size:11px;color:{FAINT}'>"
         f"{b.latitude:.4f}, {b.longitude:.4f}</span>" if b.latitude else
         f"<span style='color:{FAINT}'>—</span>"),
    ] for b in blds.itertuples()]
    st.markdown(data_table(["Building ID", "Block", "Name", "Type", "Units", "Floors", "Coordinates"],
                           rows, ["left", "left", "left", "left", "right", "right", "right"]),
                unsafe_allow_html=True)

with st.expander(f"Add a building to {chosen}"):
    with st.form("new_building", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 2])
        block = c1.text_input("Block letter", max_chars=2, placeholder="E")
        bname = c2.text_input("Building name", placeholder="e.g. Elmina Grove")
        btype = c3.selectbox("Type", BUILDING_TYPES)
        c4, c5, c6, c7 = st.columns(4)
        units = c4.number_input("Units", min_value=0, max_value=2000, value=120, step=4)
        floors = c5.number_input("Floors", min_value=0, max_value=100, value=15)
        lat = c6.number_input("Latitude", value=3.0000, format="%.4f")
        lon = c7.number_input("Longitude", value=101.5000, format="%.4f")
        if st.form_submit_button("Add building", type="primary", use_container_width=True):
            if not (block.strip() and bname.strip()):
                st.error("Block letter and building name are required.")
            else:
                try:
                    org.add_building(conn, pid, block, bname, btype, int(units), int(floors), lat, lon)
                    st.success(f"Block {block.strip().upper()} added to {chosen}.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"Block {block.strip().upper()} already exists in this township.")

st.markdown(
    f"<div style='margin-top:14px;font-size:11px;color:{MUTED}'>"
    f"<i class='fa-solid fa-circle-info' style='margin-right:7px'></i>"
    f"A resident's unit code resolves by block letter, so each block letter should be unique "
    f"across the portfolio.</div>", unsafe_allow_html=True)
