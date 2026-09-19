import re

import streamlit as st

from ui import NAVY, YELLOW, inject_css

st.set_page_config(page_title="TownshipOS", layout="wide")
inject_css()

# ── Demo credentials ──────────────────────────────────────────────────────────
# Resident units: unit_code -> 4-digit PIN
UNITS = {
    "A1512": "1223",
    "A1201": "4567",
    "B0801": "8901",
    "B1105": "2345",
    "C0302": "6789",
    "C0501": "3344",
    "D0901": "5566",
}
# FM staff badge IDs (7-digit numbers)
FM_BADGES = {"1234567", "7654321", "1111111", "2222222"}


def parse_code(raw: str):
    """Split e.g. 'A15121223' into ('A1512', '1223'). Returns (None,None) on bad format."""
    s = raw.strip().upper()
    m = re.match(r"^([A-Z]\d{3,5})(\d{4})$", s)
    return (m.group(1), m.group(2)) if m else (None, None)


role = st.session_state.get("role")

# ── Login ─────────────────────────────────────────────────────────────────────
if not role:
    st.markdown("""<style>
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>""", unsafe_allow_html=True)

    # Centered hero
    st.markdown(
        f"<div style='background:{NAVY};padding:36px 48px;border-radius:16px;"
        f"margin-bottom:32px;text-align:center'>"
        f"<div style='color:{YELLOW};font-size:12px;letter-spacing:3px;font-weight:600;"
        f"margin-bottom:10px'>SIME DARBY PROPERTY</div>"
        f"<div style='color:white;font-size:44px;font-weight:800;letter-spacing:-0.5px;"
        f"margin-bottom:8px'>TownshipOS</div>"
        f"<div style='color:#8A9DB5;font-size:15px'>AI-powered facility management · Serenia Heights demo</div>"
        f"</div>",
        unsafe_allow_html=True)

    # Login card — centered column
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        code_input = st.text_input(
            "access_code",
            placeholder="Enter your access code",
            label_visibility="collapsed",
            key="login_code",
        )
        if st.button("Enter", type="primary", use_container_width=True):
            raw = code_input.strip()
            if re.match(r"^\d{7}$", raw):
                st.session_state.role = "fm"
                st.rerun()
            else:
                unit, pin = parse_code(raw)
                if unit is None:
                    st.error("Residents: unit + 4-digit PIN e.g. A15121223 · Staff: 7-digit badge ID")
                else:
                    st.session_state.role = "resident"
                    st.session_state.unit = unit
                    st.rerun()

        st.markdown(
            f"<div style='margin-top:14px;padding:10px 14px;background:#F4F7FB;"
            f"border-radius:8px;font-size:12px;color:#6B7A99;line-height:1.8'>"
            f"Resident demo: <code>A15121223</code> · <code>A12014567</code><br>"
            f"Staff demo: <code>1234567</code> · <code>7654321</code></div>",
            unsafe_allow_html=True)

# ── Resident portal ───────────────────────────────────────────────────────────
elif role == "resident":
    unit = st.session_state.get("unit", "")
    with st.sidebar:
        st.markdown(
            f"<div style='padding:12px 8px 10px'>"
            f"<div style='color:{YELLOW};font-size:10px;letter-spacing:2px;font-weight:600'>SIME DARBY PROPERTY</div>"
            f"<div style='color:white;font-size:16px;font-weight:700;margin-top:3px'>TownshipOS</div>"
            f"<div style='color:#6B7A99;font-size:11px;margin-top:2px'>Unit {unit}</div>"
            f"</div>",
            unsafe_allow_html=True)
        st.divider()
        if st.button("← Sign out", use_container_width=True):
            for k in ("role", "unit"):
                st.session_state.pop(k, None)
            st.rerun()

    pg = st.navigation(
        [st.Page("pages/0_Report.py", title="Report an Issue", icon=":material/edit_note:")],
        position="hidden",
    )
    pg.run()

# ── FM Staff portal ───────────────────────────────────────────────────────────
else:
    with st.sidebar:
        st.markdown(
            f"<div style='padding:12px 8px 10px'>"
            f"<div style='color:{YELLOW};font-size:10px;letter-spacing:2px;font-weight:600'>SIME DARBY PROPERTY</div>"
            f"<div style='color:white;font-size:16px;font-weight:700;margin-top:3px'>TownshipOS</div>"
            f"<div style='color:#6B7A99;font-size:11px;margin-top:2px'>Facility Manager</div>"
            f"</div>",
            unsafe_allow_html=True)
        st.divider()
        if st.button("← Sign out", use_container_width=True):
            st.session_state.pop("role", None)
            st.rerun()

    pg = st.navigation([
        st.Page("pages/fm_dashboard.py",      title="Dashboard",     icon=":material/dashboard:"),
        st.Page("pages/1_Triage.py",          title="Triage",        icon=":material/manage_search:"),
        st.Page("pages/fm_sustainability.py", title="Sustainability", icon=":material/eco:"),
        st.Page("pages/fm_assistant.py",      title="Assistant",     icon=":material/chat:"),
    ])
    pg.run()
