import hashlib
import json
from pathlib import Path

import streamlit as st

from core.llm import LLMUnavailable
from core.triage import apply_triage, insert_ticket, prepare_image, triage
from core.voice import TranscriptionUnavailable, transcribe
from ui import URGENCY_COLOR, badge, db, df, header

header("Complaint Triage", "Photo + message in → category, urgency, contractor, SLA and a bilingual reply out")

samples = [json.loads(l) for l in Path("data/complaints.jsonl").read_text(encoding="utf-8").splitlines()][:30]
left, right = st.columns([1, 1])
with left:
    st.caption("Simulated WhatsApp intake")
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
            prepare_image(image_bytes)  # validate BEFORE anything touches disk or the DB
            suffix = Path(photo.name).suffix.lower()
            suffix = suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
            image_path = f"data/uploads/{hashlib.sha256(image_bytes).hexdigest()[:16]}{suffix}"  # never the client's name
            Path("data/uploads").mkdir(parents=True, exist_ok=True)
            Path(image_path).write_bytes(image_bytes)
        tid = insert_ticket(db(), text.strip() or "(photo only)", image_path)  # saved before the model runs
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
        st.markdown(f"### Ticket #{tid} {badge(r.urgency, URGENCY_COLOR[r.urgency])} "
                    f"{badge(r.category, '#0B1F3A')} " + (badge("needs human", "#6A1B9A") if r.needs_human else ""),
                    unsafe_allow_html=True)
        if r.error:
            st.warning(f"Auto-triage fell back to manual review: {r.error}")
        a, b, c = st.columns(3)
        a.metric("Contractor", r.contractor)
        b.metric("SLA", f"{r.sla_hours} h")
        c.metric("Confidence", f"{r.confidence:.0%}")
        st.write(f"**Summary:** {r.summary_en}")
        st.write(f"**Location:** {r.location or '—'} · **Language:** {r.language}")
        st.text_area("Drafted reply (BM)", r.reply_bm, height=80)
        st.text_area("Drafted reply (EN)", r.reply_en, height=80)
        st.success("Ticket created and contractor notification queued (simulated).")

st.divider()
st.subheader("Ticket queue")
status = st.multiselect("Status", ["untriaged", "open", "assigned", "closed"], default=["untriaged", "open"])
if status:
    q = df("SELECT id, created_at, urgency, category, contractor, sla_hours, needs_human, status, raw_text FROM tickets "
           f"WHERE status IN ({','.join('?' * len(status))}) ORDER BY created_at DESC", tuple(status))
else:
    q = df("SELECT * FROM tickets WHERE 0")
st.dataframe(q, use_container_width=True, hide_index=True)
