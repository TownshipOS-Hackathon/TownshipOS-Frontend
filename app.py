import streamlit as st

st.set_page_config(page_title="TownshipOS", page_icon="🏙️", layout="wide")

NAVY = "#0B1F3A"
YELLOW = "#F2B705"

role = st.session_state.get("role")

# ── Landing ──────────────────────────────────────────────────────────────────
if not role:
    st.markdown(
        f"<div style='background:{NAVY};padding:32px 40px;border-radius:16px;margin-bottom:32px;text-align:center'>"
        f"<div style='color:{YELLOW};font-size:13px;letter-spacing:3px;margin-bottom:8px'>SIME DARBY PROPERTY</div>"
        f"<div style='color:white;font-size:42px;font-weight:800;margin-bottom:6px'>🏙️ TownshipOS</div>"
        f"<div style='color:#C9D3E0;font-size:16px'>AI-powered facility management · Serenia Heights demo</div>"
        f"</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(
            f"<div style='background:#F0F4FF;border:2px solid #D0DCFF;border-radius:12px;padding:28px 24px'>"
            f"<div style='font-size:36px;margin-bottom:8px'>🏠</div>"
            f"<div style='font-size:20px;font-weight:700;color:{NAVY}'>I'm a Resident</div>"
            f"<div style='color:#555;margin-top:6px'>Report a maintenance issue in your block. "
            f"Takes under 2 minutes — photo and location optional.</div>"
            f"</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Enter as Resident", use_container_width=True, type="primary"):
            st.session_state.role = "resident"
            st.rerun()

    with col2:
        st.markdown(
            f"<div style='background:#FFF8E8;border:2px solid #FFE0A0;border-radius:12px;padding:28px 24px'>"
            f"<div style='font-size:36px;margin-bottom:8px'>🛠️</div>"
            f"<div style='font-size:20px;font-weight:700;color:{NAVY}'>FM Staff</div>"
            f"<div style='color:#555;margin-top:6px'>Full operations dashboard — triage queue, asset risk, "
            f"sustainability, and the AI assistant.</div>"
            f"</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Enter as FM Staff", use_container_width=True):
            st.session_state.role = "fm"
            st.rerun()

# ── Resident portal ───────────────────────────────────────────────────────────
elif role == "resident":
    with st.sidebar:
        st.caption("TownshipOS · Resident Portal")
        st.divider()
        if st.button("← Back to home", use_container_width=True):
            del st.session_state["role"]
            st.rerun()

    pg = st.navigation(
        [st.Page("pages/0_Report.py", title="Report an Issue", icon="📋")],
        position="hidden",
    )
    pg.run()

# ── FM Staff portal ───────────────────────────────────────────────────────────
else:
    with st.sidebar:
        st.caption("TownshipOS · FM Staff")
        st.divider()
        if st.button("← Exit to home", use_container_width=True):
            del st.session_state["role"]
            st.rerun()

    pg = st.navigation([
        st.Page("pages/fm_dashboard.py", title="Dashboard", icon="🏙️"),
        st.Page("pages/1_Triage.py",     title="Triage",    icon="🔍"),
    ])
    pg.run()
