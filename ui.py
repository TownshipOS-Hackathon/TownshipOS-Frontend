"""Small shared bits for the Streamlit pages."""
import pandas as pd
import streamlit as st

from core.db import connect

NAVY = "#0B1F3A"
YELLOW = "#F2B705"
URGENCY_COLOR = {"emergency": "#C62828", "high": "#EF6C00", "medium": "#F2B705", "low": "#2E7D32"}


def header(title: str, subtitle: str = ""):
    st.markdown(
        f"<div style='background:{NAVY};padding:18px 24px;border-radius:12px;margin-bottom:16px'>"
        f"<div style='color:{YELLOW};font-size:12px;letter-spacing:2px'>TOWNSHIPOS</div>"
        f"<div style='color:white;font-size:26px;font-weight:700'>{title}</div>"
        f"<div style='color:#C9D3E0;font-size:14px'>{subtitle}</div></div>", unsafe_allow_html=True)


def badge(text: str, color: str) -> str:
    return (f"<span style='background:{color};color:white;padding:2px 10px;border-radius:999px;"
            f"font-size:12px;font-weight:600'>{text}</span>")


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
    scored = m.score(model, m.build_features(logs, assets, as_of=END)).merge(assets, left_on="asset_id", right_on="id")
    return scored, model, metrics
