import hashlib
from pathlib import Path

import streamlit as st
from streamlit_js_eval import get_geolocation

from core.llm import LLMUnavailable
from core.triage import apply_triage, find_duplicate, insert_ticket, prepare_image, triage
from core.voice import TranscriptionUnavailable, transcribe
from ui import URGENCY_COLOR, badge, db, header

header("Report an Issue", "Snap a photo · share your location · describe the problem")

# --- Location capture (runs on load; browser asks permission once) ---
loc = get_geolocation()
lat = lon = None
if loc and "coords" in loc:
    lat = loc["coords"].get("latitude")
    lon = loc["coords"].get("longitude")
    acc = loc["coords"].get("accuracy", 0)
    st.success(f"Location captured — accuracy ±{acc:.0f} m")
else:
    st.info("Allow location access in your browser so we can pinpoint the exact spot.")

# --- Form ---
photo = st.file_uploader("Photo (optional but very helpful)", type=["jpg", "jpeg", "png", "webp"])
if photo:
    st.image(photo, use_container_width=True)

voice = st.file_uploader("Voice note (optional)", type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"])
transcript = ""
if voice:
    with st.spinner("Transcribing voice note via Whisper…"):
        try:
            transcript = transcribe(voice.getvalue(), voice.name)
            st.caption(f"Transcribed: {transcript}")
        except TranscriptionUnavailable as e:
            st.warning(str(e))
        except Exception as e:
            st.warning(f"Could not transcribe audio: {e}")

text = st.text_area(
    "Describe the problem",
    value=transcript,
    height=120,
    placeholder="E.g. Lubang besar di jalan masuk Block C / Lift stuck at level 5, making loud noise",
)

location_note = st.text_input(
    "Exact spot (optional)",
    placeholder="E.g. Near the letterbox at Block A entrance, third pillar from left",
)

go = st.button("Submit Report", type="primary", use_container_width=True)

if go and not text.strip() and not photo:
    st.error("Please describe the problem or attach a photo.")
elif go:
    image_bytes = None
    image_path = None

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
    if dup:
        st.warning(
            f"**This issue has already been reported.**\n\n"
            f"Ticket **#{dup['id']}** · {dup['category']} · Status: **{dup['status']}**\n\n"
            f"{dup['contractor'] or 'The contractor'} has been notified. "
            f"We will update residents once it is resolved. Thank you for looking out for the community!"
        )
    else:
        tid = insert_ticket(db(), text.strip() or "(photo only)", image_path, lat, lon,
                            location_note.strip() or None)
        apply_triage(db(), tid, result)
        st.success(
            f"Report submitted — **Ticket #{tid}**\n\n"
            f"**{result.contractor}** has been notified (SLA {result.sla_hours} h)"
        )
        col1, col2 = st.columns(2)
        col1.metric("Category", result.category.capitalize())
        col2.metric("Urgency", result.urgency.capitalize())

        with st.expander("Our reply to you"):
            st.markdown(f"**Bahasa Malaysia**\n\n{result.reply_bm}")
            st.markdown(f"**English**\n\n{result.reply_en}")
