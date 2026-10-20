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
    return (f"<div style='color:{YELLOW};font-size:9px;letter-spacing:2px;font-weight:700;"
            f"font-family:Inter,sans-serif;text-transform:uppercase'>SIME DARBY PROPERTY</div>"
            f"<div style='font-size:{size}px;font-weight:900;letter-spacing:-0.4px;margin-top:3px;"
            f"font-family:Nunito,sans-serif'>"
            f"<span style='color:#fff'>Township</span><span style='color:{YELLOW}'>OS</span></div>"
            f"<div style='color:rgba(255,255,255,0.35);font-size:9px;letter-spacing:1.6px;font-weight:600;"
            f"font-family:Inter,sans-serif;margin-top:4px;text-transform:uppercase'>{sub}</div>")


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
                f"<div style='padding:0 16px 12px;font-size:10.5px;color:rgba(255,255,255,0.3);line-height:1.6'>"
                f"Signed in as<br><span style='color:#C9D3E0;font-weight:600;font-size:12px'>{who}</span></div>",
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
    .block-container { max-width: 500px !important; padding-top: 0 !important; }
    .stApp { background: #ffffff !important; }
    </style>""", unsafe_allow_html=True)

    # ── Full-page centred layout ──────────────────────────────────────────────
    st.markdown(f"""
    <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;
                justify-content:center;padding:48px 0 64px">

      <!-- Hero logotype -->
      <div style="text-align:center;margin-bottom:40px">
        <div style="font-size:10px;letter-spacing:3px;font-weight:700;color:{MUTED};
                    font-family:Inter,sans-serif;text-transform:uppercase;margin-bottom:14px">
          SIME DARBY PROPERTY
        </div>
        <div style="font-size:52px;font-weight:900;letter-spacing:-2px;line-height:1;
                    font-family:Nunito,sans-serif;margin-bottom:10px">
          <span style="color:#000">Township</span><span style="color:{YELLOW}">OS</span>
        </div>
        <div style="font-size:14px;color:{MUTED};font-weight:400;line-height:1.5;
                    font-family:Inter,sans-serif">
          AI-powered facility management &middot; multi-township portfolio
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    # ── Login card ────────────────────────────────────────────────────────────
    typed = st.session_state.get("login_code", "").strip()
    code_input = st.text_input("access_code", placeholder="Enter your access code",
                               label_visibility="collapsed", key="login_code")

    if typed:
        if re.match(r"^\d{7}$", typed):
            text, fg, bg = "Staff number detected", "#000", "#fafafa"
            dot_color = NAVY
        elif re.match(r"^[A-Z]\d{3,4}\d{4}$", typed.upper()):
            text, fg, bg = "Resident code detected", "#000", "#fafafa"
            dot_color = "#2E7D32"
        else:
            text, fg, bg = "Unrecognised format", "#000", "#fafafa"
            dot_color = "#EF6C00"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:7px;margin:-4px 0 10px;"
            f"padding:7px 14px;background:{bg};border:1px solid #e5e5e5;border-radius:9999px;"
            f"font-size:12.5px;font-weight:500;color:{fg}'>"
            f"<span style='width:6px;height:6px;border-radius:50%;background:{dot_color};"
            f"display:inline-block;flex-shrink:0'></span>{text}</div>",
            unsafe_allow_html=True)

    if err := st.session_state.pop("_login_error", ""):
        st.markdown(
            f"<div style='color:#D32F2F;font-size:12.5px;font-weight:500;margin-bottom:10px;"
            f"padding:8px 14px;background:#fafafa;border:1px solid #e5e5e5;border-radius:9999px'>"
            f"<i class='fa-solid fa-circle-exclamation' style='margin-right:7px'></i>{err}</div>",
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

    # ── Demo credentials — terminal-card style ────────────────────────────────
    rows = [("Admin",    "1000001", "1000002"),
            ("Staff",    "1234567", "7654321"),
            ("Resident", "A15121223", "E12014567")]
    items = "".join(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:9px 0;{'border-bottom:1px solid #e5e5e5' if i < 2 else ''}'>"
        f"<span style='font-size:12px;color:{MUTED};font-weight:500'>{role} demo</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:12px;color:#111;"
        f"display:flex;gap:12px'>"
        f"<span>{a}</span><span style='color:#d4d4d4'>&middot;</span><span>{b}</span>"
        f"</span></div>"
        for i, (role, a, b) in enumerate(rows))
    st.markdown(
        f"<div style='margin-top:14px;background:#fafafa;border:1px solid #e5e5e5;"
        f"border-radius:12px;padding:4px 16px 0'>"
        f"<!-- traffic lights -->"
        f"<div style='display:flex;gap:5px;padding:10px 0 8px'>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:#ff5f56;display:inline-block'></span>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:#ffbd2e;display:inline-block'></span>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:#27c93f;display:inline-block'></span>"
        f"</div>"
        f"{items}</div>",
        unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='text-align:center;margin-top:28px;line-height:1.8'>"
        f"<div style='font-size:11.5px;color:{FAINT}'>"
        f"© 2026 Sime Darby Property Berhad &middot; TownshipOS Platform</div>"
        f"<div style='font-size:11px;color:#d4d4d4'>"
        f"Protected under Sime Darby Property Cybersecurity Governance</div></div>",
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
