"""Complaint triage: Claude classifies (vision + structured output); Python routes."""
import base64
import io
from datetime import datetime
from typing import Literal

import pydantic
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from core.llm import API_ERRORS, BETAS, MODEL, LLMUnavailable, cache_key, cached, get_client, refusal_reason

Category = Literal["lift", "plumbing", "electrical", "structural", "security", "landscaping", "cleanliness", "other"]
Urgency = Literal["low", "medium", "high", "emergency"]

MAX_TEXT = 2000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_SIDE = 1568
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MIN_CONFIDENCE = 0.6

# category -> (contractor, SLA hours). Deterministic, no LLM.
ROUTING: dict[str, tuple[str, int]] = {
    "lift": ("OTIS Malaysia", 4),
    "plumbing": ("AquaFix Plumbing Sdn Bhd", 8),
    "electrical": ("Voltra Electrical Sdn Bhd", 8),
    "structural": ("BuildCare Engineering Sdn Bhd", 48),
    "security": ("SecureGuard Services", 2),
    "landscaping": ("GreenScape Landscaping", 72),
    "cleanliness": ("CleanPro Facilities", 24),
    "other": ("Property Management Office", 24),
}


class TriageLLM(BaseModel):
    """Exactly what Claude returns. Kept flat and enum-heavy so parse() validates hard."""
    category: Category
    urgency: Urgency
    location: str | None = Field(description="Block / floor / unit if mentioned or visible, else null")
    language: Literal["ms", "en", "zh", "mixed"]
    summary_en: str = Field(description="One sentence in English for the ticket")
    reply_bm: str = Field(description="Short polite acknowledgement to the resident in Bahasa Malaysia")
    reply_en: str = Field(description="Same acknowledgement in English")
    confidence: float = Field(ge=0, le=1)


class TriageResult(TriageLLM):
    contractor: str
    sla_hours: int
    needs_human: bool
    error: str | None = None


SYSTEM = """You triage resident complaints for a Malaysian township property-management team.
Residents write in Bahasa Malaysia, English, Chinese or a mix (Manglish). A photo may be attached; use it.

Categories: lift, plumbing (leaks, pipes, drains, water supply), electrical (lights, power, DB boxes),
structural (cracks, ceilings, falling plaster), security (gates, doors, CCTV, intruders),
landscaping (trees, grass, gardens), cleanliness (rubbish, pests, smells), other.

Urgency:
- emergency: immediate danger to life or major property damage (person trapped in lift, fire, sparks/burning smell,
  burst pipe flooding, falling ceiling, gas smell, live wires). When in doubt between high and emergency, choose emergency.
- high: service loss or safety risk affecting many residents (lift out of service, gate stuck open, active leak into a unit).
- medium: fault that degrades service but is not urgent.
- low: cosmetic, requests, routine.

Replies: 1-2 sentences, warm and professional, acknowledge the issue, say the team is arranging the right contractor.
Never promise a specific time. Do not mention AI. reply_bm in Bahasa Malaysia, reply_en in English.
confidence is your confidence in category AND urgency together."""


def route(category: str, urgency: str, confidence: float) -> tuple[str, int, bool]:
    contractor, sla = ROUTING[category]
    if urgency == "emergency":
        return contractor, min(sla, 1), True
    return contractor, sla, confidence < MIN_CONFIDENCE


def prepare_image(data: bytes, media_type: str | None = None) -> tuple[str, str]:
    """Validate, downscale, re-encode as JPEG. Returns (base64, media_type)."""
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image larger than 5 MB")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError("File is not a readable image") from e
    if img.format not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported image format {img.format}; use JPEG, PNG or WebP")
    img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return base64.b64encode(out.getvalue()).decode(), "image/jpeg"


def _fallback(error: str) -> TriageResult:
    contractor, sla, _ = route("other", "medium", 0.0)
    return TriageResult(
        category="other", urgency="medium", location=None, language="mixed",
        summary_en="Could not auto-triage; needs manual review",
        reply_bm="Terima kasih, aduan anda telah diterima dan sedang disemak oleh pasukan kami.",
        reply_en="Thank you, your complaint has been received and is being reviewed by our team.",
        confidence=0.0, contractor=contractor, sla_hours=sla, needs_human=True, error=error)


def _finalize(llm: TriageLLM) -> TriageResult:
    contractor, sla, needs_human = route(llm.category, llm.urgency, llm.confidence)
    return TriageResult(**llm.model_dump(), contractor=contractor, sla_hours=sla, needs_human=needs_human)


def _call(text: str, image_bytes: bytes | None, media_type: str | None, client) -> dict:
    content = []
    if image_bytes is not None:
        b64, mt = prepare_image(image_bytes, media_type)
        content.append({"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}})
    content.append({"type": "text", "text": text or "(no text, photo only)"})
    last_error = "unknown"
    for _ in range(2):  # one retry on incomplete/invalid output
        try:
            r = client.beta.messages.parse(
                model=MODEL, max_tokens=2048, system=SYSTEM,
                messages=[{"role": "user", "content": content}],
                output_format=TriageLLM, output_config={"effort": "medium"},
                betas=BETAS, fallbacks="default")
        except API_ERRORS as e:
            raise LLMUnavailable(str(e)) from e
        except pydantic.ValidationError as e:
            last_error = f"invalid output: {e.error_count()} errors"
            continue
        reason = refusal_reason(r)
        if reason:
            return _fallback(reason).model_dump()
        if r.stop_reason == "max_tokens" or r.parsed_output is None:
            last_error = f"incomplete output (stop_reason={r.stop_reason})"
            continue
        return _finalize(r.parsed_output).model_dump()
    return _fallback(last_error).model_dump()


def triage(text: str, image_bytes: bytes | None = None, media_type: str | None = None, *, client=None) -> TriageResult:
    text = (text or "").strip()[:MAX_TEXT]
    if not text and image_bytes is None:
        raise ValueError("Provide a message or a photo")
    if image_bytes is not None:
        prepare_image(image_bytes, media_type)  # fail fast on bad input before touching the cache
    key = cache_key("triage", text, image_bytes)
    data = cached(key, lambda: _call(text, image_bytes, media_type, client or get_client()))
    return TriageResult(**data)


def insert_ticket(conn, raw_text: str, image_path: str | None) -> int:
    """Insert the raw complaint BEFORE calling the model, so nothing is ever lost."""
    cur = conn.execute("INSERT INTO tickets(created_at, raw_text, image_path) VALUES(?,?,?)",
                       (datetime.now().isoformat(timespec="minutes"), raw_text, image_path))
    conn.commit()
    return cur.lastrowid


def apply_triage(conn, ticket_id: int, r: TriageResult) -> None:
    conn.execute(
        "UPDATE tickets SET language=?, category=?, urgency=?, location=?, summary_en=?, contractor=?, "
        "sla_hours=?, reply_bm=?, reply_en=?, needs_human=?, confidence=?, status='open' WHERE id=?",
        (r.language, r.category, r.urgency, r.location, r.summary_en, r.contractor, r.sla_hours,
         r.reply_bm, r.reply_en, int(r.needs_human), r.confidence, ticket_id))
    conn.commit()
