"""Small shared bits for the Streamlit pages."""
import pandas as pd
import streamlit as st

from core.db import connect

NAVY = "#0B1F3A"
YELLOW = "#F2B705"
URGENCY_COLOR = {"emergency": "#C62828", "high": "#EF6C00", "medium": "#F2B705", "low": "#2E7D32"}


def inject_css() -> None:
    """Inject project-wide CSS + Font Awesome. Called once from app.py before pg.run()."""
    # Font Awesome 6 from cdnjs
    st.markdown(
        '<link rel="stylesheet" '
        'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" '
        'integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==" '
        'crossorigin="anonymous" referrerpolicy="no-referrer" />',
        unsafe_allow_html=True)
    st.markdown("""<style>
/* ── Base ───────────────────────────────────────── */
.stApp { background: #F4F7FB; }
.stElementContainer:has(iframe[title*="streamlit_js_eval"]) { height: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
[data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
h2, h3 { color: #0B1F3A !important; font-weight: 600 !important; }
hr { border-color: #E4EBF5 !important; margin: 20px 0 !important; }

/* ── Sidebar (dark navy — brand identity) ─────── */
section[data-testid="stSidebar"] {
    background: #0B1F3A;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * { color: #C9D3E0 !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }
section[data-testid="stSidebar"] button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #E8ECF4 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] button:hover { background: rgba(255,255,255,0.12) !important; }
[data-testid="stSidebarNavLink"] { border-radius: 8px !important; margin: 1px 0 !important; }
[data-testid="stSidebarNavLink"]:hover { background: rgba(242,183,5,0.10) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(242,183,5,0.18) !important;
    border-left: 3px solid #F2B705 !important;
}
[data-testid="stSidebarNavLink"] span { color: #E8ECF4 !important; }

/* ── Metric cards ─────────────────────────────── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E4EBF5;
    border-radius: 10px;
    padding: 18px 20px !important;
    box-shadow: 0 1px 3px rgba(11,31,58,0.05);
}
[data-testid="stMetricValue"] { color: #0B1F3A !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #6B7A99 !important; font-size: 12px !important; }

/* ── Primary button (yellow CTA) ──────────────── */
[data-testid="baseButton-primary"] {
    background: #F2B705 !important;
    color: #0B1F3A !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="baseButton-primary"]:hover { background: #D9A504 !important; }
[data-testid="baseButton-secondary"] {
    border: 1.5px solid #CDD6E0 !important;
    border-radius: 8px !important;
    color: #0B1F3A !important;
}

/* ── Inputs ────────────────────────────────────── */
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #F2B705 !important;
    box-shadow: 0 0 0 2px rgba(242,183,5,0.18) !important;
}

/* ── Expander ──────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E4EBF5 !important;
    border-radius: 10px !important;
}
</style>""", unsafe_allow_html=True)


def header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"<div style='background:{NAVY};padding:18px 24px;border-radius:12px;margin-bottom:16px'>"
        f"<div style='color:{YELLOW};font-size:12px;letter-spacing:2px;font-weight:600'>TOWNSHIPOS</div>"
        f"<div style='color:white;font-size:26px;font-weight:700;letter-spacing:-0.3px'>{title}</div>"
        f"<div style='color:#8A9DB5;font-size:13px;margin-top:2px'>{subtitle}</div></div>",
        unsafe_allow_html=True)


def badge(text: str, color: str) -> str:
    # dark text on yellow to meet WCAG contrast
    text_color = "#0B1F3A" if color in (YELLOW, "#F2B705") else "white"
    return (f"<span style='background:{color};color:{text_color};padding:2px 10px;border-radius:999px;"
            f"font-size:12px;font-weight:600'>{text}</span>")


def section_label(text: str, icon: str = "") -> None:
    """Small uppercase label. icon = Font Awesome class string e.g. 'fa-solid fa-ticket'."""
    icon_html = f'<i class="{icon}" style="margin-right:7px;opacity:0.65"></i>' if icon else ""
    st.markdown(
        f"<div style='font-size:11px;font-weight:600;letter-spacing:1.5px;color:#6B7A99;"
        f"text-transform:uppercase;margin-bottom:6px'>{icon_html}{text}</div>",
        unsafe_allow_html=True)


@st.cache_resource
def db():
    return connect("townshipos.db")


def df(sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, db(), params=params)


@st.cache_resource
def scored_assets():
    """(scored DataFrame joined with assets, model, metrics-or-None). Trains once per process if no model file."""
    from core import maintenance as m
    from data.generate import END
    assets, logs = df("SELECT * FROM assets"), df("SELECT * FROM service_logs")
    model, metrics = m.load_or_train(logs, assets)
    scored = (m.score(model, m.build_features(logs, assets, as_of=END))
              .merge(assets, left_on="asset_id", right_on="id"))
    return scored, model, metrics
