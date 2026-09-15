"""Shared Claude plumbing: client, on-disk response cache, refusal check."""
import hashlib
import json
import os
from pathlib import Path

import anthropic

MODEL = "claude-opus-5"
BETAS = ["server-side-fallback-2026-07-01"]   # enables fallbacks="default" (category-routed refusal fallback)
CACHE_DIR = Path(os.environ.get("TOWNSHIPOS_CACHE", "cache"))
_client = None


class LLMUnavailable(RuntimeError):
    """Raised after the SDK's own retries are exhausted. Callers fall back to cache or show an error."""


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=60.0, max_retries=2)
    return _client


def cache_key(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, (bytes, bytearray)):
            h.update(b"<bytes>" + hashlib.sha256(p).digest())
        else:
            h.update(json.dumps(p, sort_keys=True, ensure_ascii=False, default=str).encode())
        h.update(b"\x1f")
    return h.hexdigest()[:24]


def cached(key: str, fn):
    """Return the JSON-able dict stored under key, or call fn(), store it, return it."""
    p = CACHE_DIR / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    value = fn()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    return value


def refusal_reason(response):
    """Explanation string if the response is a refusal, else None. Call before reading content."""
    if getattr(response, "stop_reason", None) != "refusal":
        return None
    details = getattr(response, "stop_details", None)
    return getattr(details, "explanation", None) or "Request declined by the safety system"


# AnthropicError covers connection/status/auth; the SDK raises a bare TypeError when no credentials resolve.
API_ERRORS = (anthropic.AnthropicError, TypeError)


def unavailable(e: Exception) -> LLMUnavailable:
    """Wrap an SDK failure in LLMUnavailable with a message a demo audience can read."""
    if "authentication method" in str(e):
        return LLMUnavailable("No Anthropic API key found. Set ANTHROPIC_API_KEY (cached demo responses still work).")
    return LLMUnavailable(f"{type(e).__name__}: {e}")
