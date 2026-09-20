"""Shared design system for TownshipOS. Ported from the Figma operational-cockpit design."""
import pandas as pd
import streamlit as st

from core.db import connect

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY = "#0F1C33"
NAVY_SOFT = "#16294A"
YELLOW = "#F5B700"
PAGE_BG = "#F7F8FC"
BORDER = "#E4E8F0"
TEXT = "#2D3748"
MUTED = "#6B7A99"
FAINT = "#8792AB"

URGENCY_COLOR = {"emergency": "#D32F2F", "high": "#EF6C00", "medium": "#F2B705", "low": "#2E7D32"}
URGENCY_BG = {"emergency": "#FDECEC", "high": "#FFF3E0", "medium": "#FFF8E1", "low": "#E8F5E9"}
PURPLE = "#6A1B9A"
PURPLE_BG = "#F3E5F5"
INFO_BG = "#E8EEFB"
INFO_FG = "#2A4B8D"


def inject_css() -> None:
    """Fonts, Font Awesome, and the project-wide stylesheet. Called once from app.py."""
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" '
        'crossorigin="anonymous" referrerpolicy="no-referrer" />'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&'
        'family=JetBrains+Mono:wght@400;500;600&'
        'family=Material+Symbols+Rounded:opsz,wght@20..48,400&display=block" rel="stylesheet">',
        unsafe_allow_html=True)

    st.markdown(f"""<style>
/* ── Base ─────────────────────────────────────────── */
html, body, .stApp {{ font-family: 'Inter', system-ui, sans-serif; }}
/* Streamlit's nav glyphs are an icon font — never let Inter win here. */
[data-testid="stIconMaterial"], span[class*="material-symbols"], .material-icons {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
}}
.stApp {{ background: {PAGE_BG}; }}
[data-testid="stHeader"] {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
footer {{ display: none !important; }}
.block-container {{ padding-top: 1.1rem !important; padding-bottom: 3rem !important; max-width: 1120px !important; }}
.stElementContainer:has(iframe[title*="streamlit_js_eval"]) {{
    height: 0 !important; min-height: 0 !important; margin: 0 !important;
    padding: 0 !important; overflow: hidden !important;
}}
h1, h2, h3, h4 {{ color: {NAVY} !important; font-weight: 700 !important; letter-spacing: -0.2px; }}
hr {{ border-color: {BORDER} !important; margin: 18px 0 !important; }}
code {{ font-family: 'JetBrains Mono', monospace !important; }}

/* ── Sidebar ──────────────────────────────────────── */
section[data-testid="stSidebar"] {{ background: {NAVY}; width: 240px !important; }}
section[data-testid="stSidebar"] > div {{ background: {NAVY}; }}
section[data-testid="stSidebar"] * {{ color: #9AA8C0; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.10) !important; margin: 10px 0 !important; }}
section[data-testid="stSidebar"] button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #C9D3E0 !important; border-radius: 8px !important;
    font-size: 13px !important; font-weight: 500 !important;
}}
section[data-testid="stSidebar"] button:hover {{ background: rgba(255,255,255,0.11) !important; }}
[data-testid="stSidebarHeader"], [data-testid="stSidebarNav"] {{ display: none !important; }}
[data-testid="stSidebarContent"] {{ display: flex; flex-direction: column; min-height: 100vh; }}
[data-testid="stSidebarUserContent"] {{ display: flex; flex-direction: column; flex: 1; padding: 0 !important; }}
[data-testid="stSidebarUserContent"] > div:first-child {{ display: flex; flex-direction: column; flex: 1; }}
.tos-brand {{ padding: 18px 16px 14px; }}
.tos-navgap {{ flex: 1; min-height: 20px; }}

/* Re-rendered nav (st.page_link), with the active row keyed from Python. */
[data-testid="stSidebar"] [data-testid="stPageLink"] {{ margin: 0 !important; }}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
    border-radius: 0 !important; padding: 10px 16px !important;
    gap: 12px !important; border-left: 3px solid transparent !important;
}}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{ background: rgba(255,255,255,0.05) !important; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] p {{
    color: #9AA8C0 !important; font-size: 13.5px !important; font-weight: 500 !important; margin: 0 !important;
}}
[class*="st-key-nav_on_"] a[data-testid="stPageLink-NavLink"] {{
    background: rgba(255,255,255,0.07) !important; border-left-color: {YELLOW} !important;
}}
[class*="st-key-nav_on_"] [data-testid="stPageLink"] p {{ color: #FFFFFF !important; font-weight: 600 !important; }}
[class*="st-key-nav_on_"] [data-testid="stIconMaterial"] {{ color: {YELLOW} !important; }}

/* Material glyphs need the icon font — Inter would print the literal glyph name. */
[data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded' !important;
    font-weight: 400 !important; font-style: normal !important;
    letter-spacing: normal !important; text-transform: none !important;
    color: #9AA8C0 !important; font-size: 18px !important;
}}

/* ── Buttons ──────────────────────────────────────── */
.stButton > button[kind="primary"], [data-testid="baseButton-primary"] {{
    background: {YELLOW} !important; color: {NAVY} !important; border: none !important;
    font-weight: 700 !important; border-radius: 8px !important; font-size: 14px !important;
    padding: 10px 18px !important; box-shadow: none !important;
}}
.stButton > button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {{ background: #DCA500 !important; }}
.stButton > button[kind="secondary"], [data-testid="baseButton-secondary"] {{
    border: 1px solid {BORDER} !important; border-radius: 8px !important;
    color: {NAVY} !important; background: white !important;
    font-size: 13.5px !important; font-weight: 500 !important; text-align: left !important;
}}
.stButton > button[kind="secondary"]:hover {{ border-color: {YELLOW} !important; background: #FFFCF2 !important; }}

/* ── Inputs ───────────────────────────────────────── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div {{
    border-radius: 8px !important; border-color: {BORDER} !important;
    background: white !important; font-size: 14px !important;
}}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
    border-color: {YELLOW} !important; box-shadow: 0 0 0 3px rgba(245,183,0,0.15) !important;
}}
[data-testid="stWidgetLabel"] p {{ font-size: 12.5px !important; font-weight: 600 !important; color: {MUTED} !important; }}

/* ── Containers ───────────────────────────────────── */
[data-testid="stExpander"] {{ border: 1px solid {BORDER} !important; border-radius: 10px !important; background: white; }}
[data-testid="stDataFrame"] {{ border: 1px solid {BORDER} !important; border-radius: 10px !important; }}
[data-testid="stMetric"] {{
    background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 14px 16px !important;
}}
[data-testid="stMetricValue"] {{ color: {NAVY} !important; font-weight: 700 !important; }}
[data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-size: 11px !important; }}
.stAlert {{ border-radius: 10px !important; }}

/* ── Reusable blocks ──────────────────────────────── */
.tos-card {{ background:#fff; border:1px solid {BORDER}; border-radius:10px; padding:16px 18px; }}
.tos-mono {{ font-family:'JetBrains Mono', monospace; }}
</style>""", unsafe_allow_html=True)


# ── Chrome ────────────────────────────────────────────────────────────────────
def topbar(district: str = "SERENIA HEIGHTS CENTRAL DISTRICT") -> None:
    """Fixed-feel cockpit bar: centred title, search affordance, action icons."""
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;gap:16px;"
        f"padding:0 4px 14px;border-bottom:1px solid {BORDER};margin-bottom:18px'>"
        f"<div style='flex:1'></div>"
        f"<div style='text-align:center;line-height:1.3'>"
        f"<div style='font-size:14px;font-weight:600;color:{NAVY}'>Township Operational Cockpit</div>"
        f"<div style='font-size:10px;letter-spacing:1px;color:{FAINT};font-weight:500'>{district}</div>"
        f"</div>"
        f"<div style='flex:1;display:flex;align-items:center;justify-content:flex-end;gap:14px'>"
        f"<div style='display:flex;align-items:center;gap:8px;background:#fff;border:1px solid {BORDER};"
        f"border-radius:8px;padding:7px 12px;min-width:240px'>"
        f"<i class='fa-solid fa-magnifying-glass' style='font-size:11px;color:{FAINT}'></i>"
        f"<span style='font-size:12.5px;color:{FAINT}'>Search units, tickets, telemetry…</span></div>"
        f"<i class='fa-regular fa-bell' style='color:{MUTED};font-size:15px'></i>"
        f"<i class='fa-solid fa-sliders' style='color:{MUTED};font-size:15px'></i>"
        f"<div style='width:28px;height:28px;border-radius:50%;background:{NAVY};display:flex;"
        f"align-items:center;justify-content:center'>"
        f"<i class='fa-solid fa-user' style='color:#fff;font-size:12px'></i></div>"
        f"</div></div>",
        unsafe_allow_html=True)


def header(title: str, subtitle: str = "", eyebrow_tag: str = "", chips: list[tuple[str, str]] | None = None) -> None:
    """Navy page banner. chips = [(label, 'dot'|'plain'), …] rendered on the right."""
    tag = (f"<span style='color:{FAINT};font-weight:500'> &middot; {eyebrow_tag}</span>") if eyebrow_tag else ""
    chip_html = ""
    if chips:
        parts = []
        for label, kind in chips:
            dot = (f"<span style='width:6px;height:6px;border-radius:50%;background:{YELLOW};"
                   f"display:inline-block;margin-right:7px'></span>") if kind == "dot" else ""
            parts.append(
                f"<span style='background:rgba(255,255,255,0.09);border:1px solid rgba(255,255,255,0.14);"
                f"border-radius:7px;padding:6px 12px;font-size:11px;font-weight:600;color:#E8ECF4;"
                f"letter-spacing:0.3px;white-space:nowrap'>{dot}{label}</span>")
        chip_html = ("<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;"
                     "justify-content:flex-end'>" + "".join(parts) + "</div>")
    st.markdown(
        f"<div style='background:{NAVY};border-radius:12px;padding:20px 24px;margin-bottom:20px;"
        f"display:flex;align-items:center;justify-content:space-between;gap:20px'>"
        f"<div><div style='color:{YELLOW};font-size:10px;letter-spacing:2px;font-weight:700'>TOWNSHIPOS{tag}</div>"
        f"<div style='color:#fff;font-size:25px;font-weight:700;letter-spacing:-0.4px;margin:5px 0 3px'>{title}</div>"
        f"<div style='color:#8A9DB5;font-size:12.5px'>{subtitle}</div></div>"
        f"{chip_html}</div>",
        unsafe_allow_html=True)


def section_label(text: str, icon: str = "", right: str = "") -> None:
    """Uppercase micro-label. icon = Font Awesome classes. right = muted text on the far side."""
    icon_html = f'<i class="{icon}" style="margin-right:8px;opacity:0.55"></i>' if icon else ""
    right_html = (f"<span style='font-size:10.5px;font-weight:500;letter-spacing:0.6px;"
                  f"color:{FAINT};text-transform:none'>{right}</span>") if right else ""
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin:0 0 9px'>"
        f"<span style='font-size:11px;font-weight:700;letter-spacing:1.2px;color:{MUTED};"
        f"text-transform:uppercase'>{icon_html}{text}</span>{right_html}</div>",
        unsafe_allow_html=True)


# ── Atoms ─────────────────────────────────────────────────────────────────────
def pill(text: str, fg: str, bg: str, mono: bool = False) -> str:
    font = "'JetBrains Mono', monospace" if mono else "inherit"
    return (f"<span style='background:{bg};color:{fg};padding:3px 9px;border-radius:5px;"
            f"font-size:10.5px;font-weight:700;letter-spacing:0.4px;font-family:{font};"
            f"white-space:nowrap'>{text.upper()}</span>")


def urgency_pill(urgency: str) -> str:
    u = (urgency or "untriaged").lower()
    return pill(u, URGENCY_COLOR.get(u, "#546E7A"), URGENCY_BG.get(u, "#ECEFF1"))


def badge(text: str, color: str) -> str:
    """Legacy rounded badge kept for call sites that want a solid pill."""
    fg = NAVY if color in (YELLOW, "#F2B705") else "white"
    return (f"<span style='background:{color};color:{fg};padding:2px 10px;border-radius:999px;"
            f"font-size:11.5px;font-weight:600'>{text}</span>")


def metric_card(label: str, value: str, unit: str = "", footnote: str = "",
                icon: str = "", value_color: str = NAVY) -> str:
    """Cockpit metric tile: label + icon, coloured value, rule, footnote."""
    icon_html = f"<i class='{icon}' style='color:{FAINT};font-size:13px'></i>" if icon else ""
    unit_html = (f"<span style='font-size:12.5px;font-weight:500;color:{MUTED};"
                 f"margin-left:6px'>{unit}</span>") if unit else ""
    foot = (f"<div style='border-top:1px solid {BORDER};margin-top:11px;padding-top:9px;"
            f"font-size:11px;color:{MUTED}'>{footnote}</div>") if footnote else ""
    return (f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:14px 16px;height:100%'>"
            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:8px'>"
            f"<span style='font-size:10px;font-weight:700;letter-spacing:1px;color:{MUTED};"
            f"text-transform:uppercase;line-height:1.4'>{label}</span>{icon_html}</div>"
            f"<div style='margin-top:8px'><span style='font-size:29px;font-weight:700;"
            f"color:{value_color};letter-spacing:-1px'>{value}</span>{unit_html}</div>{foot}</div>")


def txt(value, default: str = "—") -> str:
    """Escaped cell text. pandas turns SQL NULLs into NaN, which is truthy — so `x or default`
    is not enough and every table cell goes through here."""
    import html as _html

    import pandas as _pd
    if value is None or (isinstance(value, float) and _pd.isna(value)):
        return default
    s = str(value).strip()
    return _html.escape(s) if s else default


def card_open(pad: str = "16px 18px", extra: str = "") -> str:
    return f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:{pad};{extra}'>"


def data_table(heads: list[str], rows: list[list[str]], align: list[str] | None = None,
               footer: list[str] | None = None) -> str:
    """Dense cockpit table. Cells are raw HTML, so callers escape their own text."""
    align = align or ["left"] * len(heads)
    head = "".join(
        f"<th style='text-align:{a};padding:9px 12px;font-size:9.5px;letter-spacing:0.8px;"
        f"color:{MUTED};font-weight:700;text-transform:uppercase;white-space:nowrap'>{h}</th>"
        for h, a in zip(heads, align))
    body = "".join(
        "<tr>" + "".join(
            f"<td style='padding:10px 12px;border-top:1px solid {BORDER};text-align:{a};"
            f"font-size:12.5px;color:#2D3748;vertical-align:middle'>{c}</td>"
            for c, a in zip(row, align)) + "</tr>"
        for row in rows)
    if footer:
        body += "<tr style='background:#F4F6FB'>" + "".join(
            f"<td style='padding:11px 12px;border-top:1px solid {BORDER};text-align:{a};"
            f"font-size:12.5px;font-weight:700;color:{NAVY}'>{c}</td>"
            for c, a in zip(footer, align)) + "</tr>"
    return (f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;overflow:auto'>"
            f"<table style='width:100%;border-collapse:collapse'>"
            f"<thead style='background:#F4F6FB'><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_resource
def db():
    return connect("townshipos.db")


def scope_picker() -> tuple[str | None, list[str]]:
    """Township + building selectors. Returns (project_id, building_ids to filter on).

    FM staff are pinned to the township on their staff record; group admins roam.
    """
    projects = db().execute("SELECT id, name FROM projects ORDER BY name").fetchall()
    if not projects:
        return None, []
    pinned = st.session_state.get("project_id")
    is_admin = st.session_state.get("role") == "admin"

    pcol, bcol, _ = st.columns([1.1, 1.1, 2])
    if is_admin or pinned is None:
        names = {p["name"]: p["id"] for p in projects}
        chosen = pcol.selectbox("Township", list(names), key="_scope_project_pick")
        pid = names[chosen]
    else:
        pid = pinned
        name = next((p["name"] for p in projects if p["id"] == pid), pid)
        pcol.markdown(
            f"<div style='padding-top:4px'><div style='font-size:10px;letter-spacing:0.9px;"
            f"color:{MUTED};font-weight:700;text-transform:uppercase'>Township</div>"
            f"<div style='font-size:14px;font-weight:700;color:{NAVY};margin-top:4px'>{name}</div></div>",
            unsafe_allow_html=True)

    rows = db().execute("SELECT id, block, name FROM buildings WHERE project_id = ? ORDER BY block",
                        (pid,)).fetchall()
    opts = {"All buildings": None} | {f"Block {r['block']} — {r['name']}": r["id"] for r in rows}
    picked = bcol.selectbox("Building", list(opts), key=f"_scope_building_{pid}")
    bid = opts[picked]
    return pid, [bid] if bid else [r["id"] for r in rows]


def scope_sql(column: str, building_ids: list[str]) -> tuple[str, tuple]:
    """('building_id IN (?,?)', params) — safe because only the count is interpolated."""
    if not building_ids:
        return "1=0", ()
    return f"{column} IN ({','.join('?' * len(building_ids))})", tuple(building_ids)


def df(sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, db(), params=params)


@st.cache_resource
def scored_assets():
    """(scored joined with assets, model, metrics-or-None). Trains once per process if no model file."""
    from core import maintenance as m
    from data.generate import END
    assets, logs = df("SELECT * FROM assets"), df("SELECT * FROM service_logs")
    model, metrics = m.load_or_train(logs, assets)
    scored = (m.score(model, m.build_features(logs, assets, as_of=END))
              .merge(assets, left_on="asset_id", right_on="id"))
    return scored, model, metrics
