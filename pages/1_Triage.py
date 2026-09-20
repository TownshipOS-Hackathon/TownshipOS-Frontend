import hashlib
import html as html_lib
import json
from pathlib import Path

import streamlit as st

from core.llm import LLMUnavailable
from core.triage import apply_triage, insert_ticket, prepare_image, triage
from core.voice import TranscriptionUnavailable, transcribe
from ui import (BORDER, FAINT, MUTED, NAVY, PURPLE, PURPLE_BG, URGENCY_COLOR, db, df, header,
                metric_card, scope_picker, scope_sql, section_label, topbar, urgency_pill)

STATUS_STYLE = {"open": ("#B26A00", "#FFF8E1"), "assigned": ("#2A4B8D", "#E8EEFB"),
                "closed": ("#546E7A", "#ECEFF1"), "untriaged": ("#6B7A99", "#EEF2FA")}

topbar()
header("Complaint Triage",
       "Photo + message in → category, urgency, contractor, SLA and a bilingual reply out",
       chips=[("AI PIPELINE ONLINE", "dot")])

project_id, building_ids = scope_picker()
intake_building = building_ids[0] if len(building_ids) == 1 else None

samples = [json.loads(l) for l in Path("data/complaints.jsonl").read_text(encoding="utf-8").splitlines()][:30]
left, right = st.columns(2, gap="medium")

# ── Intake ────────────────────────────────────────────────────────────────────
with left:
    with st.container(border=True):
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
        text = st.text_area("Resident Message Body", value=default_text or transcript, height=110,
                            placeholder="Lif rosak tingkat 5, bunyi pelik")
        photo = st.file_uploader("Resident Photo Attachment", type=["jpg", "jpeg", "png", "webp"])
        if photo:
            st.image(photo, use_container_width=True)
            size_mb = len(photo.getvalue()) / 1_048_576
            st.markdown(
                f"<div style='margin-top:-8px;font-family:JetBrains Mono,monospace;font-size:10.5px;"
                f"color:{FAINT}'><i class='fa-regular fa-image' style='margin-right:6px'></i>"
                f"{html_lib.escape(photo.name)} ({size_mb:.1f} MB)</div>", unsafe_allow_html=True)
        go = st.button("Triage with TownshipOS AI", type="primary", use_container_width=True)

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
        tid = insert_ticket(db(), text.strip() or "(photo only)", image_path,
                            building_id=intake_building)
        with st.spinner("Claude is reading the complaint…"):
            result = triage(text, image_bytes, photo.type if photo else None)
        apply_triage(db(), tid, result)
        st.session_state["last"] = (tid, result)
    except ValueError as e:
        st.error(str(e))
    except LLMUnavailable as e:
        st.error(f"Triage service unavailable; ticket #{tid} saved as untriaged. ({e})")

# ── Result ────────────────────────────────────────────────────────────────────
if "last" in st.session_state:
    tid, r = st.session_state["last"]
    col = URGENCY_COLOR.get(r.urgency, "#546E7A")
    with right:
        cat_pill = (f"<span style='background:{NAVY};color:#fff;padding:3px 9px;border-radius:5px;"
                    f"font-size:10.5px;font-weight:700;letter-spacing:0.4px'>{(r.category or '').upper()}</span>")
        human_pill = (f"<span style='background:{PURPLE_BG};color:{PURPLE};padding:3px 9px;border-radius:5px;"
                      f"font-size:10.5px;font-weight:700;letter-spacing:0.4px'>NEEDS HUMAN</span>"
                      if r.needs_human else "")
        st.markdown(
            f"<div style='background:#fff;border:1px solid {BORDER};border-top:4px solid {col};"
            f"border-radius:10px;padding:16px 18px;margin-bottom:12px'>"
            f"<div style='display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:9px'>"
            f"<span style='font-weight:700;color:{NAVY};font-size:19px'>Ticket #{tid}</span>"
            f"{urgency_pill(r.urgency)}{cat_pill}{human_pill}</div>"
            f"<div style='color:#2D3748;font-size:13.5px;line-height:1.55'>{html_lib.escape(r.summary_en or '')}</div>"
            f"<div style='color:{MUTED};font-size:11.5px;margin-top:7px'>"
            f"Location: {html_lib.escape(r.location or '—')} &middot; Language: {r.language} "
            f"&middot; Confidence: {r.confidence:.0%}</div></div>",
            unsafe_allow_html=True)

        if r.error:
            st.warning(f"Auto-triage fell back to manual review: {r.error}")

        tiles = [
            metric_card("Contractor", r.contractor, "", "Primary SLA Partner", "fa-regular fa-address-card"),
            metric_card("SLA Target", f"{r.sla_hours} h", "", "High Urgency Clock",
                        "fa-regular fa-clock", col),
            metric_card("Model Confidence", f"{r.confidence:.0%}", "", "Township LLM v4.2",
                        "fa-regular fa-circle-check"),
        ]
        for c, tile in zip(st.columns(3), tiles):
            c.markdown(tile, unsafe_allow_html=True)

        st.write("")
        with st.container(border=True):
            section_label("Drafted Reply", "fa-solid fa-reply", right="DUAL OUTPUT")
            for lang, body in [("Bahasa Malaysia", r.reply_bm), ("English", r.reply_en)]:
                st.markdown(
                    f"<div style='font-size:11.5px;font-weight:600;color:{MUTED};margin:6px 0 4px'>{lang}</div>"
                    f"<div style='background:#F4F6FB;border:1px solid {BORDER};border-radius:8px;"
                    f"padding:11px 13px;font-size:12.5px;color:#2D3748;line-height:1.6'>"
                    f"{html_lib.escape(body or '')}</div>", unsafe_allow_html=True)

        wa, note = st.columns([1, 1.6])
        if wa.button("Send reply via WhatsApp", use_container_width=True, key="_wa_send"):
            st.session_state["_wa_sent"] = tid
        note.markdown(
            f"<div style='display:flex;gap:9px;align-items:flex-start;padding-top:8px'>"
            f"<i class='fa-regular fa-circle-check' style='color:#2E7D32;margin-top:2px'></i>"
            f"<span style='font-size:12px;color:{MUTED};line-height:1.5'>Ticket created and contractor "
            f"notification queued for {html_lib.escape(r.contractor or 'contractor')}.</span></div>",
            unsafe_allow_html=True)

        if st.session_state.get("_wa_sent") == tid:
            st.markdown(
                f"<div style='background:#E8F5E9;border:1px solid #C8E6C9;border-left:4px solid #2E7D32;"
                f"border-radius:8px;padding:11px 15px;margin-top:10px;font-size:12.5px;color:#2D3748'>"
                f"<i class='fa-brands fa-whatsapp' style='color:#25D366;margin-right:9px;font-size:15px'></i>"
                f"Bilingual reply delivered to the resident and dispatch note pushed to "
                f"<strong>{html_lib.escape(r.contractor or 'contractor')}</strong> duty engineer. "
                f"<span style='color:{FAINT}'>(simulated — no message actually sent)</span></div>",
                unsafe_allow_html=True)

# ── Queue ─────────────────────────────────────────────────────────────────────
st.write("")
with st.container(border=True):
    section_label("Ticket Queue", "fa-solid fa-list-check")
    status = st.multiselect("Status", ["untriaged", "open", "assigned", "closed"],
                            default=["untriaged", "open"], label_visibility="collapsed")
    scope_clause, scope_params = scope_sql("building_id", building_ids)
    q = (df("SELECT id, created_at, urgency, category, contractor, sla_hours, needs_human, status, raw_text "
            f"FROM tickets WHERE {scope_clause} AND status IN ({','.join('?' * len(status))}) "
            "ORDER BY created_at DESC LIMIT 12",
            (*scope_params, *status)) if status else df("SELECT * FROM tickets WHERE 0"))

    if q.empty:
        st.markdown(f"<div style='padding:18px;text-align:center;color:{MUTED};font-size:13px'>"
                    f"No tickets match this filter.</div>", unsafe_allow_html=True)
    else:
        heads = ["ID", "Created At", "Urgency", "Category", "Contractor", "SLA (h)", "Needs Human", "Status", "Raw Text"]
        head_html = "".join(
            f"<th style='text-align:left;padding:9px 10px;font-size:9.5px;letter-spacing:0.8px;"
            f"color:{MUTED};font-weight:700;text-transform:uppercase;white-space:nowrap'>{h}</th>" for h in heads)
        body_html = ""
        for t in q.itertuples():
            s = (t.status or "untriaged").lower()
            s_fg, s_bg = STATUS_STYLE.get(s, STATUS_STYLE["untriaged"])
            ucol = URGENCY_COLOR.get((t.urgency or "").lower(), "#546E7A")
            cells = [
                f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{NAVY}'>#{t.id}</span>",
                f"<span style='color:{MUTED};font-size:11.5px'>{(t.created_at or '')[:16].replace('T', ' ')}</span>",
                urgency_pill(t.urgency),
                html_lib.escape(t.category or "—"),
                f"<span style='font-size:11.5px'>{html_lib.escape(t.contractor or '—')}</span>",
                f"<span style='color:{ucol};font-weight:700'>{t.sla_hours or '—'}</span>",
                (f"<i class='fa-solid fa-user-check' style='color:{PURPLE}'></i>" if t.needs_human
                 else f"<span style='color:{FAINT}'>—</span>"),
                (f"<span style='background:{s_bg};color:{s_fg};padding:3px 8px;border-radius:5px;"
                 f"font-size:10px;font-weight:700'>{s.upper()}</span>"),
                (f"<span style='color:{MUTED};font-size:11.5px'>"
                 f"{html_lib.escape((t.raw_text or '')[:52])}…</span>"),
            ]
            body_html += ("<tr>" + "".join(
                f"<td style='padding:10px;border-top:1px solid {BORDER};vertical-align:middle;"
                f"font-size:12.5px;color:#2D3748'>{c}</td>" for c in cells) + "</tr>")
        st.markdown(
            f"<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse'>"
            f"<thead style='background:#F4F6FB'><tr>{head_html}</tr></thead>"
            f"<tbody>{body_html}</tbody></table></div>",
            unsafe_allow_html=True)
