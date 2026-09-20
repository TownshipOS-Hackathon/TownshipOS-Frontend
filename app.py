import re

import streamlit as st

from core.org import AuthError, authenticate
from ui import BORDER, FAINT, MUTED, NAVY, YELLOW, db, inject_css

st.set_page_config(page_title="TownshipOS", layout="wide")
inject_css()

FM_NAV = [
    ("pages/fm_dashboard.py",      "Dashboard",               ":material/dashboard:"),
    ("pages/1_Triage.py",          "Triage",                  ":material/manage_search:"),
    ("pages/2_Assets.py",          "Assets (Predictive M&E)", ":material/precision_manufacturing:"),
    ("pages/fm_sustainability.py", "Sustainability",          ":material/eco:"),
    ("pages/fm_assistant.py",      "Assistant",               ":material/chat:"),
]
ADMIN_NAV = [
    ("pages/admin_overview.py",    "Portfolio Overview", ":material/analytics:"),
    ("pages/admin_portfolio.py",   "Towns & Buildings",  ":material/apartment:"),
    ("pages/admin_users.py",       "Staff Registry",     ":material/badge:"),
    ("pages/admin_contractors.py", "Contractor Directory", ":material/handyman:"),
]


def brand_block(size: int, sub: str) -> str:
    return (f"<div style='color:{YELLOW};font-size:9.5px;letter-spacing:1.8px;font-weight:700'>"
            f"SIME DARBY PROPERTY</div>"
            f"<div style='font-size:{size}px;font-weight:800;letter-spacing:-0.5px;margin-top:2px'>"
            f"<span style='color:#fff'>Township</span><span style='color:{YELLOW}'>OS</span></div>"
            f"<div style='color:{FAINT};font-size:9.5px;letter-spacing:1.4px;font-weight:600;"
            f"margin-top:3px'>{sub}</div>")


def sidebar_nav(nav: list[tuple[str, str, str]], subtitle: str):
    """Branding above the links, sign-out pinned to the bottom. st.page_link keeps the session."""
    pages = [st.Page(path, title=title, icon=icon) for path, title, icon in nav]
    pg = st.navigation(pages, position="hidden")
    with st.sidebar:
        st.markdown(f"<div class='tos-brand'>{brand_block(19, subtitle)}</div>", unsafe_allow_html=True)
        for page in pages:
            state = "on" if page.url_path == pg.url_path else "off"
            with st.container(key=f"nav_{state}_{page.url_path}"):
                st.page_link(page, label=page.title, icon=page.icon)
        st.markdown("<div class='tos-navgap'></div>", unsafe_allow_html=True)
        who = st.session_state.get("name", "")
        if who:
            st.markdown(
                f"<div style='padding:0 16px 10px;font-size:10.5px;color:{FAINT};line-height:1.5'>"
                f"Signed in as<br><span style='color:#C9D3E0;font-weight:600'>{who}</span></div>",
                unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            for k in ("role", "name", "staff_no", "project_id", "building_id", "unit", "scope_project"):
                st.session_state.pop(k, None)
            st.rerun()
    return pg


role = st.session_state.get("role")

# ── Login ─────────────────────────────────────────────────────────────────────
if not role:
    st.markdown("""<style>
    section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .block-container { max-width: 620px !important; padding-top: 3rem !important; }
    </style>""", unsafe_allow_html=True)

    st.markdown(
        f"<div style='background:{NAVY};border-radius:12px;padding:30px 40px 34px;text-align:center;"
        f"margin-bottom:22px'>"
        f"<div style='color:{YELLOW};font-size:10.5px;letter-spacing:2.6px;font-weight:700'>"
        f"SIME DARBY PROPERTY</div>"
        f"<div style='font-size:42px;font-weight:800;letter-spacing:-1.2px;margin:8px 0 6px'>"
        f"<span style='color:#fff'>Township</span><span style='color:{YELLOW}'>OS</span></div>"
        f"<div style='color:#8A9DB5;font-size:13.5px'>AI-powered facility management "
        f"&middot; multi-township portfolio</div></div>",
        unsafe_allow_html=True)

    with st.container(border=True):
        typed = st.session_state.get("login_code", "").strip()
        code_input = st.text_input("access_code", placeholder="Enter your access code",
                                   label_visibility="collapsed", key="login_code")

        if typed:
            if re.match(r"^\d{7}$", typed):
                text, fg, bg = "Staff Number Detected", "#2A4B8D", "#E8EEFB"
            elif re.match(r"^[A-Z]\d{3,4}\d{4}$", typed.upper()):
                text, fg, bg = "Resident Detected", "#2E7D32", "#E8F5E9"
            else:
                text, fg, bg = "Unrecognised Format", "#B26A00", "#FFF8E1"
            st.markdown(
                f"<div style='display:flex;justify-content:flex-end;margin:-8px 0 8px'>"
                f"<span style='background:{bg};color:{fg};border-radius:6px;padding:4px 10px;"
                f"font-size:11px;font-weight:600'>"
                f"<span style='width:6px;height:6px;border-radius:50%;background:{fg};display:inline-block;"
                f"margin-right:6px'></span>{text}</span></div>",
                unsafe_allow_html=True)

        if err := st.session_state.pop("_login_error", ""):
            st.markdown(
                f"<div style='color:#D32F2F;font-size:12px;font-weight:500;margin-bottom:8px'>"
                f"<i class='fa-solid fa-circle-exclamation' style='margin-right:6px'></i>{err}</div>",
                unsafe_allow_html=True)

        if st.button("Enter  →", type="primary", use_container_width=True):
            try:
                session = authenticate(db(), code_input)
            except AuthError as e:
                st.session_state._login_error = str(e)
                st.rerun()
            st.session_state.update(session)
            st.session_state.scope_project = session["project_id"]
            st.rerun()

        rows = [("Admin demo:", "1000001 &nbsp;·&nbsp; 1000002"),
                ("Staff demo:", "1234567 &nbsp;·&nbsp; 7654321"),
                ("Resident demo:", "A15121223 &nbsp;·&nbsp; E1201 4567".replace(" 4567", "4567"))]
        body = "".join(
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:8px 12px;{'border-bottom:1px solid ' + BORDER if i < 2 else ''}'>"
            f"<span style='font-size:12px;color:{MUTED};font-weight:500'>{lbl}</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:11.5px;color:{NAVY};"
            f"font-weight:500'>{val}</span></div>"
            for i, (lbl, val) in enumerate(rows))
        st.markdown(
            f"<div style='background:#F4F6FB;border:1px solid {BORDER};border-radius:8px;"
            f"margin-top:12px'>{body}</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"margin-top:14px;padding-top:12px;border-top:1px solid {BORDER}'>"
            f"<span style='font-size:11px;color:{MUTED}'>"
            f"<span style='width:6px;height:6px;border-radius:50%;background:#2E7D32;"
            f"display:inline-block;margin-right:7px'></span>"
            f"Portfolio Operations Auth Gateway</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-size:11px;color:{FAINT}'>v2.4-MY</span>"
            f"</div>",
            unsafe_allow_html=True)

    st.markdown(
        f"<div style='text-align:center;margin-top:20px;line-height:1.7'>"
        f"<div style='font-size:11.5px;color:{MUTED}'>© 2026 Sime Darby Property Berhad "
        f"&middot; TownshipOS Platform</div>"
        f"<div style='font-size:11px;color:{FAINT}'>Protected under Sime Darby Property "
        f"Cybersecurity Governance</div></div>",
        unsafe_allow_html=True)

# ── Resident portal ───────────────────────────────────────────────────────────
elif role == "resident":
    with st.sidebar:
        st.markdown(f"<div class='tos-brand'>{brand_block(19, st.session_state.get('unit', 'RESIDENT'))}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='tos-navgap'></div>", unsafe_allow_html=True)
        if st.button("←  Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    pg = st.navigation(
        [st.Page("pages/0_Report.py", title="Report an Issue", icon=":material/edit_note:")],
        position="hidden",
    )
    pg.run()

# ── Group admin portal ────────────────────────────────────────────────────────
elif role == "admin":
    sidebar_nav(ADMIN_NAV, "GROUP ADMIN").run()

# ── FM Staff portal ───────────────────────────────────────────────────────────
else:
    sidebar_nav(FM_NAV, "FACILITY MANAGER").run()
