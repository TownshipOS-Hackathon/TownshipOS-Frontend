import hashlib
import json
from pathlib import Path

import streamlit as st

from core.llm import LLMUnavailable
from core.triage import apply_triage, insert_ticket, prepare_image, triage
from core.voice import TranscriptionUnavailable, transcribe
from ui import NAVY, URGENCY_COLOR, badge, db, df, header, section_label

header("Complaint Triage",
       "Photo + message in → category, urgency, contractor, SLA and a bilingual reply out")

samples = [json.loads(l) for l in Path("data/complaints.jsonl").read_text(encoding="utf-8").splitlines()][:30]
left, right = st.columns([1, 1])

with left:
    section_label("Simulated WhatsApp Intake", "fa-brands fa-whatsapp")
    pick = st.selectbox("Load a sample message", ["(type your own)"] + [s["text"] for s in samples])
    voice = st.file_uploader("Voice note (optional)", type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"])
    transcript = ""
    if voice:
        with st.spinner("Transcribing via Whisper…"):
            try:
                transcript = transcribe(voice.getvalue(), voice.name)
                st.caption(f"Transcribed: {transcript}")
            except (TranscriptionUnavailable, Exception) as e:
                st.warning(f"Voice transcription unavailable: {e}")
    default_text = "" if pick.startswith("(") else pick
    if not default_text:
        default_text = transcript
    text = st.text_area("Resident message", value=default_text, height=120,
                        placeholder="Lif rosak tingkat 5, bunyi pelik")
    photo = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png", "webp"])
    if photo:
        st.image(photo, width=320)
    go = st.button("Triage", type="primary", use_container_width=True)

if go and not text.strip() and not photo:
    st.error("Provide a message or a photo")
elif go:
    image_bytes = photo.getvalue() if photo else None
    image_path = None
    tid = None
    try:
        if image_bytes is not None:
            prepare_image(image_bytes)
            suffix = Path(photo.name).suffix.lower()
            suffix = suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
            image_path = f"data/uploads/{hashlib.sha256(image_bytes).hexdigest()[:16]}{suffix}"
            Path("data/uploads").mkdir(parents=True, exist_ok=True)
            Path(image_path).write_bytes(image_bytes)
        tid = insert_ticket(db(), text.strip() or "(photo only)", image_path)
        with st.spinner("Claude is reading the complaint…"):
            result = triage(text, image_bytes, photo.type if photo else None)
        apply_triage(db(), tid, result)
        st.session_state["last"] = (tid, result)
    except ValueError as e:
        st.error(str(e))
    except LLMUnavailable as e:
        st.error(f"Triage service unavailable; ticket #{tid} saved as untriaged. ({e})")

if "last" in st.session_state:
    tid, r = st.session_state["last"]
    with right:
        urg_color = URGENCY_COLOR[r.urgency]
        # Result card header
        st.markdown(
            f"<div style='background:white;border:1px solid #E4EBF5;border-radius:10px;"
            f"padding:16px 18px;margin-bottom:12px;border-top:4px solid {urg_color}'>"
            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap'>"
            f"<span style='font-weight:700;color:{NAVY};font-size:18px'>Ticket #{tid}</span>"
            f"{badge(r.urgency, urg_color)}"
            f"{badge(r.category, NAVY)}"
            f"{'&nbsp;' + badge('needs human', '#6A1B9A') if r.needs_human else ''}"
            f"</div>"
            f"<div style='color:#4A5568;font-size:14px;line-height:1.5'>{r.summary_en}</div>"
            f"<div style='color:#6B7A99;font-size:12px;margin-top:6px'>"
            f"Location: {r.location or '—'} &middot; Language: {r.language}"
            f"</div></div>",
            unsafe_allow_html=True)

        if r.error:
            st.warning(f"Auto-triage fell back to manual review: {r.error}")

        a, b, c = st.columns(3)
        a.metric("Contractor", r.contractor)
        b.metric("SLA", f"{r.sla_hours} h")
        c.metric("Confidence", f"{r.confidence:.0%}")

        section_label("Drafted Reply", "fa-solid fa-reply")
        st.text_area("Bahasa Malaysia", r.reply_bm, height=80)
        st.text_area("English", r.reply_en, height=80)
        st.success("Ticket created and contractor notification queued (simulated).")

# ── Ticket queue ──────────────────────────────────────────────────────────────
st.divider()
section_label("Ticket Queue", "fa-solid fa-list-check")
status = st.multiselect("Status", ["untriaged", "open", "assigned", "closed"],
                        default=["untriaged", "open"])
if status:
    q = df("SELECT id, created_at, urgency, category, contractor, sla_hours, needs_human, status, raw_text "
           f"FROM tickets WHERE status IN ({','.join('?' * len(status))}) ORDER BY created_at DESC",
           tuple(status))
else:
    q = df("SELECT * FROM tickets WHERE 0")
st.dataframe(q, use_container_width=True, hide_index=True)
