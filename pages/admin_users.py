"""Group-admin staff registry. Sign-in checks this table, so a row here is an access grant."""
import html as html_lib
import sqlite3

import streamlit as st

from core import org
from ui import (BORDER, FAINT, MUTED, NAVY, data_table, db, df, header, metric_card,
                section_label, topbar, txt)

ROLE_STYLE = {"admin": ("#6A1B9A", "#F3E5F5", "GROUP ADMIN"),
              "fm": ("#2A4B8D", "#E8EEFB", "FACILITY MANAGER")}

topbar("GROUP PORTFOLIO · STAFF REGISTRY")
header("Staff Registry", "Register staff numbers and scope them to a township",
       eyebrow_tag="GROUP ADMIN", chips=[("ACCESS CONTROL", "dot")])

conn = db()
users = df("SELECT u.*, p.name AS project_name FROM users u "
           "LEFT JOIN projects p ON p.id = u.project_id ORDER BY u.role, u.name")
projects = df("SELECT id, name FROM projects ORDER BY name")

active = users[users["active"] == 1]
cards = [
    metric_card("Registered staff", str(len(users)), "accounts", "— Portfolio wide",
                "fa-solid fa-id-badge"),
    metric_card("Active", str(len(active)), "can sign in",
                f"— {len(users) - len(active)} deactivated", "fa-solid fa-user-check", "#2E7D32"),
    metric_card("Group admins", str(int((users["role"] == "admin").sum())), "unrestricted",
                "— See every township", "fa-solid fa-user-shield", "#6A1B9A"),
    metric_card("Facility managers", str(int((users["role"] == "fm").sum())), "site-scoped",
                "— Pinned to one township", "fa-solid fa-user-gear"),
]
for col, card in zip(st.columns(4), cards):
    col.markdown(card, unsafe_allow_html=True)

# ── Registry ──────────────────────────────────────────────────────────────────
st.write("")
section_label("Registered Staff", "fa-solid fa-users", right="Sign-in is enforced against this list")
rows = []
for u in users.itertuples():
    fg, bg, label = ROLE_STYLE.get(u.role, (MUTED, "#EEF2FA", u.role.upper()))
    scope = txt(u.project_name, "All townships")
    status = (f"<span style='background:#E8F5E9;color:#2E7D32;padding:3px 9px;border-radius:5px;"
              f"font-size:10px;font-weight:700'>ACTIVE</span>" if u.active else
              f"<span style='background:#ECEFF1;color:#546E7A;padding:3px 9px;border-radius:5px;"
              f"font-size:10px;font-weight:700'>DISABLED</span>")
    rows.append([
        f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>{u.staff_no}</span>",
        f"<span style='font-weight:600;color:{NAVY}'>{txt(u.name)}</span>",
        f"<span style='background:{bg};color:{fg};padding:3px 9px;border-radius:5px;"
        f"font-size:10px;font-weight:700'>{label}</span>",
        f"<span style='font-size:12px'>{scope}</span>",
        f"<span style='font-family:JetBrains Mono,monospace;font-size:11px;color:{MUTED}'>"
        f"{txt(u.phone)}</span>",
        f"<span style='font-size:11.5px;color:{MUTED}'>{txt(u.email)}</span>",
        status,
    ])
st.markdown(data_table(["Staff No.", "Name", "Role", "Township Scope", "Phone", "Email", "Status"],
                       rows, ["left", "left", "left", "left", "left", "left", "right"]),
            unsafe_allow_html=True)

# ── Register ──────────────────────────────────────────────────────────────────
with st.expander("Register a staff member"):
    with st.form("new_user", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        staff_no = c1.text_input("Staff number", max_chars=7, placeholder="7 digits")
        name = c2.text_input("Full name", placeholder="e.g. Aminah binti Yusof")
        role = c3.selectbox("Role", ["fm", "admin"],
                            format_func=lambda r: ROLE_STYLE[r][2].title())
        c4, c5, c6 = st.columns(3)
        scope_names = {"All townships (group admin)": None} | {p.name: p.id for p in projects.itertuples()}
        scope = c4.selectbox("Township scope", list(scope_names))
        phone = c5.text_input("Phone", placeholder="+60 3-…")
        email = c6.text_input("Email", placeholder="name@simedarbyproperty.com")
        if st.form_submit_button("Register staff member", type="primary", use_container_width=True):
            pid = scope_names[scope]
            if role == "fm" and pid is None:
                st.error("A facility manager must be scoped to one township.")
            elif not name.strip():
                st.error("Full name is required.")
            else:
                try:
                    org.add_user(conn, staff_no, name, role, pid, phone, email)
                    st.success(f"Staff number {staff_no.strip()} registered — they can sign in now.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except sqlite3.IntegrityError:
                    st.error(f"Staff number {staff_no.strip()} is already registered.")

# ── Enable / disable ──────────────────────────────────────────────────────────
with st.expander("Enable or disable access"):
    if users.empty:
        st.info("No staff registered yet.")
    else:
        labels = {f"{u.staff_no} — {u.name} ({'active' if u.active else 'disabled'})": (u.staff_no, u.active)
                  for u in users.itertuples()}
        c1, c2 = st.columns([2, 1])
        picked = c1.selectbox("Staff member", list(labels), label_visibility="collapsed")
        staff_no, is_active = labels[picked]
        me = st.session_state.get("staff_no")
        if staff_no == me:
            c2.markdown(f"<div style='padding-top:6px;font-size:11.5px;color:{MUTED}'>"
                        f"This is your own account.</div>", unsafe_allow_html=True)
        elif c2.button("Disable access" if is_active else "Re-enable access",
                       use_container_width=True):
            org.set_user_active(conn, staff_no, not is_active)
            st.rerun()

st.markdown(
    f"<div style='margin-top:14px;font-size:11px;color:{MUTED}'>"
    f"<i class='fa-solid fa-circle-info' style='margin-right:7px'></i>"
    f"Sign-in rejects any staff number absent from this registry, so add the account before "
    f"handing out the number.</div>", unsafe_allow_html=True)
