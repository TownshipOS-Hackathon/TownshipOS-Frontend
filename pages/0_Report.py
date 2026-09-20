import hashlib
import html as html_lib
from pathlib import Path

import streamlit as st
from streamlit_js_eval import get_geolocation

from core.llm import LLMUnavailable
from core.triage import apply_triage, find_duplicate, insert_ticket, prepare_image, triage
from ui import (BORDER, FAINT, MUTED, NAVY, URGENCY_BG, URGENCY_COLOR, YELLOW, db, header,
                section_label, topbar)

unit = st.session_state.get("unit", "")
topbar(f"RESIDENT SERVICES · UNIT {unit}" if unit else "RESIDENT SERVICES")
header("Report an Issue", "Snap a photo · share your location · describe the problem",
       eyebrow_tag="RESIDENT PORTAL", chips=[("24/7 INTAKE", "dot")])

# Location is taken silently; only the denial path asks the resident for anything.
loc = get_geolocation()
lat = lon = None
location_note = ""
if loc and "coords" in loc:
    lat = loc["coords"].get("latitude")
    lon = loc["coords"].get("longitude")
    st.toast(f"Location captured — accuracy ±{loc['coords'].get('accuracy', 0):.0f} m")
else:
    location_note = st.text_input("Where is the problem?",
                                  placeholder="E.g. Near the lift lobby, Block C, level 3")

with st.container(border=True):
    section_label("Photo", "fa-solid fa-camera", right="OPTIONAL BUT HELPFUL")
    photo = st.file_uploader("Attach a photo", type=["jpg", "jpeg", "png", "webp"],
                             label_visibility="collapsed")
    if photo:
        st.image(photo, use_container_width=True)
        st.markdown(
            f"<div style='margin-top:-8px;font-family:JetBrains Mono,monospace;font-size:10.5px;"
            f"color:{FAINT}'><i class='fa-regular fa-image' style='margin-right:6px'></i>"
            f"{html_lib.escape(photo.name)} ({len(photo.getvalue()) / 1_048_576:.1f} MB)</div>",
            unsafe_allow_html=True)

    st.write("")
    section_label("Description", "fa-solid fa-pen-to-square", right="BM / EN / 中文")
    text = st.text_area(
        "Describe the problem", value="", height=118, label_visibility="collapsed",
        placeholder="E.g. Lubang besar di jalan masuk Block C / Lift stuck at level 5, making loud noise")
    go = st.button("Submit Report", type="primary", use_container_width=True)

st.markdown(
    f"<div style='display:flex;align-items:center;gap:9px;margin-top:12px;font-size:11px;color:{MUTED}'>"
    f"<span style='width:6px;height:6px;border-radius:50%;background:#2E7D32;display:inline-block'></span>"
    f"Reports are triaged by TownshipOS AI and routed to the on-call contractor automatically.</div>",
    unsafe_allow_html=True)

# ── Submission ────────────────────────────────────────────────────────────────
if go and not text.strip() and not photo:
    st.error("Please describe the problem or attach a photo.")
elif go:
    image_bytes = image_path = None
    if photo:
        image_bytes = photo.getvalue()
        try:
            prepare_image(image_bytes)
        except ValueError as e:
            st.error(str(e))
            st.stop()
        suffix = Path(photo.name).suffix.lower()
        suffix = suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
        image_path = f"data/uploads/{hashlib.sha256(image_bytes).hexdigest()[:16]}{suffix}"
        Path("data/uploads").mkdir(parents=True, exist_ok=True)
        Path(image_path).write_bytes(image_bytes)

    with st.spinner("Analysing your report…"):
        try:
            result = triage(text or "(photo only)", image_bytes, photo.type if photo else None)
        except LLMUnavailable as e:
            st.error(f"Service temporarily unavailable — please try again shortly. ({e})")
            st.stop()

    dup = find_duplicate(db(), result.category, lat, lon)
    st.write("")
    if dup:
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-left:4px solid "
            f"{URGENCY_COLOR['medium']};border-radius:10px;padding:16px 18px'>"
            f"<div style='font-weight:700;color:{NAVY};font-size:14px;margin-bottom:6px'>"
            f"<i class='fa-solid fa-circle-info' style='margin-right:9px;color:{YELLOW}'></i>"
            f"This issue has already been reported</div>"
            f"<div style='font-size:13px;color:#2D3748;line-height:1.6'>Ticket "
            f"<strong>#{dup['id']}</strong> · {dup['category']} · Status: <strong>{dup['status']}</strong><br>"
            f"{html_lib.escape(dup['contractor'] or 'The contractor')} has been notified. We will update "
            f"residents once it is resolved — thank you for looking out for the community.</div></div>",
            unsafe_allow_html=True)
    else:
        tid = insert_ticket(db(), text.strip() or "(photo only)", image_path, lat, lon,
                            location_note.strip() or None,
                            building_id=st.session_state.get("building_id"))
        apply_triage(db(), tid, result)
        col = URGENCY_COLOR.get(result.urgency, "#546E7A")
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-top:4px solid #2E7D32;"
            f"border-radius:10px;padding:16px 18px;margin-bottom:12px'>"
            f"<div style='font-weight:700;color:{NAVY};font-size:16px;margin-bottom:6px'>"
            f"<i class='fa-regular fa-circle-check' style='margin-right:9px;color:#2E7D32'></i>"
            f"Report submitted — Ticket #{tid}</div>"
            f"<div style='font-size:13px;color:#2D3748'>"
            f"<strong>{html_lib.escape(result.contractor)}</strong> has been notified "
            f"(SLA {result.sla_hours} h)</div></div>",
            unsafe_allow_html=True)

        tiles = [("Category", result.category.capitalize(), NAVY),
                 ("Urgency", result.urgency.capitalize(), col),
                 ("Target SLA", f"{result.sla_hours} h", NAVY)]
        for c, (lbl, val, vcol) in zip(st.columns(3), tiles):
            c.markdown(
                f"<div style='background:#fff;border:1px solid {BORDER};border-radius:10px;padding:13px 15px'>"
                f"<div style='font-size:9.5px;font-weight:700;letter-spacing:0.9px;color:{MUTED};"
                f"text-transform:uppercase'>{lbl}</div>"
                f"<div style='font-size:19px;font-weight:700;color:{vcol};margin-top:4px'>{val}</div></div>",
                unsafe_allow_html=True)

        st.write("")
        with st.expander("Our reply to you", expanded=True):
            for lang, body in [("Bahasa Malaysia", result.reply_bm), ("English", result.reply_en)]:
                st.markdown(
                    f"<div style='font-size:11.5px;font-weight:700;color:{MUTED};margin:4px 0 4px'>{lang}</div>"
                    f"<div style='background:#F4F6FB;border:1px solid {BORDER};border-radius:8px;"
                    f"padding:11px 13px;font-size:12.5px;color:#2D3748;line-height:1.6;margin-bottom:8px'>"
                    f"{html_lib.escape(body or '')}</div>", unsafe_allow_html=True)
