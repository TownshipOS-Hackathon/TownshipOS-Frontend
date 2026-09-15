# TownshipOS — Design Spec

**Date:** 2026-09-16
**Event:** Sime Darby Property University Hackathon ("Ideas Into Impact")
**Status:** Approved in brainstorming (Parts 1 and 2); ready for implementation planning

## 1. Constraints from kickoff

| Question | Answer | Consequence |
|---|---|---|
| Deadline | Over one month | Build all four pages, real photos, eval set, rehearsed demo |
| Format | Live demo + deck | App must be demo-safe: cached responses, no network dependency on stage |
| Team | 2–3 people, one coder | `core/` modules are pure Python so the coder works alone; teammates own deck, photos, labelling |
| Prototype | Required | End-to-end working Streamlit app, not mock screens |

## 2. Product (decided, not re-opened)

**TownshipOS** — "one AI brain for running a township." Internal ops platform for Sime Darby Property's property/facility management teams. Intake, classification, routing and first reply are automated; humans handle exceptions and decisions.

Four features:

| # | Feature | AI | Demo moment |
|---|---|---|---|
| 1 | Complaint Triage (hero) | Claude Opus 5 vision + structured output | Photo + "Lif rosak tingkat 5, bunyi pelik" → Lift / High / OTIS (SLA 4h) + BM & EN reply → ticket |
| 2 | Predictive Maintenance | scikit-learn classifier on service logs | "Lift L3, Block B — 78% failure risk in 30 days" → pre-emptive work order |
| 3 | Sustainability Intel | rolling z-score anomaly detection + Claude ESG narrative | "Block C water +40% vs baseline — probable leak" + monthly ESG report with CO₂e |
| + | Ask TownshipOS | Claude with SOP/SLA docs as cited `document` blocks | "Penalty if OTIS misses the 4h SLA?" → answer citing the clause |

## 3. Architecture

```
townshipos/
  app.py                    # Streamlit entry; sidebar nav to 4 pages
  pages/                    # 1_Triage.py 2_Assets.py 3_Sustainability.py 4_Ask.py
  core/
    db.py                   # sqlite3 connect + schema
    llm.py                  # shared Anthropic client, JSON response cache, refusal check
    triage.py
    assistant.py
    maintenance.py
    sustainability.py
  data/
    generate.py             # writes all synthetic data into townshipos.db
    photos/                 # ~10 real campus photos
    docs/                   # 5 SOP/SLA text files for the assistant
  eval/
    triage_set.jsonl        # 40 labelled complaints
    run_triage_eval.py
  tests/                    # one test_*.py per core module + generators
  cache/                    # JSON cache of LLM responses (committed for demo safety)
  models/maintenance.pkl    # trained classifier (regenerated if missing)
  docs/superpowers/specs/
```

- **Streamlit** only. No backend, no React. Theme navy + yellow via `.streamlit/config.toml`.
- **SQLite** via stdlib `sqlite3`, single file `townshipos.db`.
- **Claude Opus 5** (`claude-opus-5`) via the official `anthropic` Python SDK. Adaptive thinking (default), `output_config.effort` set per call, no prefill, no sampling params.
- **scikit-learn + pandas** for maintenance model and anomaly detection. Pillow (already a Streamlit dependency) for image downscaling.
- Python 3.14 via `uv`; deps in `pyproject.toml`.

### 3.1 Data model (SQLite)

```sql
tickets(id, created_at, raw_text, image_path, language, category, urgency,
        location, summary_en, contractor, sla_hours, reply_bm, reply_en,
        needs_human, confidence, status)          -- status: untriaged|open|assigned|closed
assets(id, name, type, block, installed_at, contractor, sla_hours)
service_logs(id, asset_id, date, kind, runtime_hours, vibration_score, notes)  -- kind: scheduled|breakdown
utility_readings(id, block, month, kwh, m3)
work_orders(id, asset_id, created_at, risk, reason, status)
```

### 3.2 Shared LLM plumbing (`core/llm.py`)

- `get_client()` returns a module-level `anthropic.Anthropic()`; every core function accepts `client=None` so tests inject a fake.
- `cached(key_parts, fn)`: SHA-256 of the inputs → `cache/<hash>.json`. Hit returns the stored dict; miss calls `fn`, stores, returns. This is the demo safety net: rehearse once, then the stage demo is offline-safe.
- `check_refusal(response)`: if `stop_reason == "refusal"`, return `stop_details.explanation` (or a generic string); else `None`. Called before any content is read.
- All Claude calls go through `client.beta.messages.*` with `betas=["server-side-fallback-2026-07-01"]` and `fallbacks="default"` so category-routed server-side fallbacks handle refusals automatically. A `refusal` that survives the fallback chain routes to a human.

## 4. Module interfaces

### 4.1 `core/triage.py`

```python
Category = Literal["lift","plumbing","electrical","structural","security",
                   "landscaping","cleanliness","other"]
Urgency  = Literal["low","medium","high","emergency"]

class TriageLLM(BaseModel):            # what Claude returns via messages.parse
    category: Category
    urgency: Urgency
    location: str | None
    language: Literal["ms","en","zh","mixed"]
    summary_en: str
    reply_bm: str
    reply_en: str
    confidence: float                  # 0–1

class TriageResult(TriageLLM):         # TriageLLM + deterministic routing
    contractor: str
    sla_hours: int
    needs_human: bool
    error: str | None = None

ROUTING: dict[Category, tuple[str, int]]   # e.g. "lift": ("OTIS Malaysia", 4)

def route(category, urgency, confidence) -> tuple[str, int, bool]   # contractor, sla_hours, needs_human
def triage(text: str, image_bytes: bytes | None = None,
           media_type: str | None = None, *, client=None) -> TriageResult
def create_ticket(conn, result: TriageResult, raw_text: str, image_path: str | None) -> int
```

- The LLM classifies only. Contractor, SLA and `needs_human` come from `ROUTING` plus rules (`urgency == "emergency"` or `confidence < 0.6` → `needs_human`). Deterministic, testable, free.
- `triage` calls `client.beta.messages.parse(model="claude-opus-5", max_tokens=2048, output_format=TriageLLM, output_config={"effort":"medium"}, betas=[...], fallbacks="default", system=TRIAGE_SYSTEM, messages=[image block?, text block])`.
- Image handling at the boundary: accept JPEG/PNG/WebP ≤ 5 MB, downscale longest side to 1568 px with Pillow, base64 encode.

### 4.2 `core/assistant.py`

```python
@dataclass
class Citation: doc_title: str; cited_text: str
@dataclass
class Answer:  text: str; citations: list[Citation]; refused: bool

def load_docs(dir: str = "data/docs") -> list[dict]
    # one {"type":"document","source":{"type":"text",...},"title":...,
    #      "citations":{"enabled":True}} per file; cache_control on the last block
def ask(question: str, docs: list[dict], *, client=None) -> Answer
```

- Docs go in the first user turn's content, followed by the question text block. Streaming via `client.beta.messages.stream(...)` and `get_final_message()`. `effort: "high"`.
- Citations parsed from `text` blocks carrying a `citations` array (`cited_text`, `document_title`). Zero citations → UI shows "uncited — verify".
- No vector DB: five short docs fit trivially in context; `cache_control` makes repeat questions cheap.

### 4.3 `core/maintenance.py`

```python
FEATURES = ["age_months","days_since_service","breakdowns_last_12m",
            "avg_runtime_hours","vibration_score"]

def build_features(logs: DataFrame, assets: DataFrame, as_of: date) -> DataFrame
    # one row per asset: FEATURES + label failed_within_30d (for training windows)
def train(features: DataFrame) -> tuple[Pipeline, dict]     # metrics: auc, importances
def score(model, features: DataFrame) -> DataFrame           # asset_id, risk, top_drivers (2 features)
def create_work_order(conn, asset_id: str, risk: float, reason: str) -> int
```

- Model: `GradientBoostingClassifier` in a `Pipeline` with `StandardScaler`. Seeded. Saved with `pickle` to `models/maintenance.pkl`; retrained on startup if missing.
- Training set is built by sliding `as_of` monthly over the 24-month history so each asset contributes ~20 rows.
- `top_drivers`: the two features with the highest positive z-score for that asset. Global `feature_importances_` shown once on the page as "what the model learned".

### 4.4 `core/sustainability.py`

```python
GRID_FACTOR_KG_PER_KWH = 0.74   # Energy Commission Malaysia, Peninsular GEF 2024

def detect_anomalies(readings: DataFrame, window: int = 12, z: float = 2.5) -> DataFrame
    # per block×utility rolling mean/std over prior `window` months; rows where |z| ≥ threshold
    # columns: block, utility, month, value, baseline, z, pct_vs_baseline
def co2e(kwh: float, factor: float = GRID_FACTOR_KG_PER_KWH) -> float
def monthly_summary(readings: DataFrame, month: str) -> dict     # totals per block, township, co2e, MoM %
def esg_narrative(summary: dict, anomalies: DataFrame, *, client=None) -> str   # markdown
```

- Blocks with fewer than `window + 1` months are skipped.
- Narrative call: `effort: "medium"`, streaming, cached like the rest.

### 4.5 `core/db.py`

```python
def connect(path: str = "townshipos.db") -> sqlite3.Connection   # row_factory = sqlite3.Row
def init_schema(conn) -> None                                     # CREATE TABLE IF NOT EXISTS ×5
```

## 5. Error handling

| Failure | Handling |
|---|---|
| Any triage attempt | Raw complaint inserted as `untriaged` **before** the API call; a failed triage never loses a message |
| Pydantic `ValidationError` or `stop_reason == "max_tokens"` | Retry once; second failure → `TriageResult(category="other", urgency="medium", needs_human=True, confidence=0, error=...)` |
| `stop_reason == "refusal"` after server-side fallback | `needs_human=True`, `error` = refusal explanation; assistant returns `Answer(refused=True)` |
| `RateLimitError`, 5xx, `APIConnectionError` | SDK retries twice; then raise `LLMUnavailable`; page falls back to cache if present, else shows error and leaves ticket `untriaged` |
| Bad input | Text stripped, ≤ 2000 chars; image ≤ 5 MB, JPEG/PNG/WebP only; empty text **and** no image → rejected with a message |
| Missing `models/maintenance.pkl` | Seeded retrain from DB at startup |
| Short utility history | Block skipped by detector, noted in UI |
| Uncited assistant answer | Rendered with an "uncited — verify" badge |

Timeouts: 60 s for triage; assistant and ESG narrative stream. All errors are logged with `response._request_id` when available.

## 6. Testing and eval

**Unit tests** (pytest, fully offline, `FakeClient` returning canned responses):

| File | Covers |
|---|---|
| `tests/test_triage.py` | `route()` table; enum rejection; refusal path; validation-failure fallback; ticket round-trip in SQLite |
| `tests/test_assistant.py` | `load_docs` block shape (citations on, `cache_control` only on last); citation parsing; refusal path |
| `tests/test_maintenance.py` | exact feature values on a 3-asset log; seeded train AUC ≥ 0.75; scores ∈ [0,1], sorted desc |
| `tests/test_sustainability.py` | injected +40 % spike flagged; normal months not; `co2e` arithmetic; narrative builder with fake client |
| `tests/test_generate.py` | row counts; language mix ≈ 50/35/15; failure label rate 10–20 % |

**Triage eval** (`eval/`): 40 hand-labelled complaints (gold category + urgency), 10 with campus photos. `run_triage_eval.py` calls the real API once (~USD 1), caches results, prints per-category precision/recall/F1, urgency accuracy, and **emergency recall**.
Targets: category macro-F1 ≥ 0.85; emergency recall = 1.0 (a missed emergency is the worst failure).

**Smoke check:** `streamlit run app.py` starts and each page renders with the seeded DB. Run manually before each rehearsal.

## 7. Synthetic data plan (`data/generate.py`, seeded)

- **Complaints:** ~200, BM/EN/Chinese ≈ 50/35/15 with Manglish mixing; templated per category with urgency cues. ~10 real campus photos (cracked wall, leaking pipe, broken light, blocked drain).
- **Assets:** ~60 across 4 blocks — lifts, pumps, gensets, chillers, gates — each with contractor and SLA.
- **Service logs:** 24 months; scheduled services plus breakdowns whose probability rises with age, days since service and vibration, so the label is learnable but not trivial. Target base rate 10–20 %.
- **Utility readings:** 24 months × 4 blocks × (kWh, m³) with seasonality; injected anomalies: Block C water +40 % in the latest month (leak), Block A kWh +25 % three months back (chiller fault).
- **Docs:** Lift Maintenance SLA, Plumbing SLA, Renovation Guidelines, Emergency SOP, Strata Management Act 2013 (Act 757) extracts. Plain text, 1–2 pages each, with numbered clauses so citations look precise.

## 8. Streamlit pages

| Page | Contents |
|---|---|
| Triage | Text box + photo upload ("simulate WhatsApp"); Triage button → result card (category, urgency badge, contractor, SLA, drafted BM/EN replies); Create ticket; ticket table with status filter; header metrics "80 messages → 23 tickets, 3 urgent, 5 need a human" |
| Assets | Risk-ranked table; expand asset → drivers + service history; Create pre-emptive work order; feature-importance bar chart |
| Sustainability | Block × month kWh and m³ charts; anomaly callouts; Generate ESG monthly report → markdown with CO₂e |
| Ask | Chat input; answer with citation chips; expandable "sources" showing cited text |

## 9. Demo script (3 minutes)

1. Photo + Manglish complaint → triage card → ticket + bilingual reply.
2. Assets → Lift L3 78 % → pre-emptive work order.
3. Sustainability → Block C water anomaly → generated ESG summary.
4. Ask → SLA penalty question → cited answer.

Day-in-the-life framing: 06:12 leak photo triaged before the manager wakes; 07:00 overnight re-scoring flags Lift L3; 07:00 water anomaly flagged; 09:30 manager reviews 23 tickets and asks one SLA question.

## 10. Pitch → four pillars

- **Innovation:** photo + Manglish in, typed ticket out; cited SOP answers with no vector DB thanks to 1M context; a real trained failure-risk model, not rules.
- **Collaboration:** one shared queue across the PM team, the JMB/MC and contractors; bilingual first reply drafted automatically; SLA clock visible to all; humans handle exceptions only.
- **Sustainability:** leaks and energy faults caught within a month, not at the annual audit; monthly ESG report with CO₂e (Energy Commission grid factor 0.74 kgCO₂e/kWh) feeding Sime Darby Property's net-zero reporting; predictive maintenance extends asset life.
- **Future Ready:** one brain scales to 20+ townships with no extra headcount; Defect Liability Period tracking; multilingual by default; WhatsApp and IoT feeds plug in later.

All figures in the pitch (80 → 23, call-out cost multiples) are stated as illustrative from synthetic data, never as Sime Darby facts.

## 11. Budget

Opus 5 at USD 5 / 25 per M tokens. Triage with image ≈ 2.5k in / 0.5k out ≈ USD 0.025; 200 complaints ≈ USD 5. Assistant docs (~15k tokens) are cached, so questions cost cents. ESG narrative ≈ USD 0.05 each. Eval run ≈ USD 1. Total comfortably inside USD 10–20.

## 12. Explicitly cut

Real WhatsApp webhook (simulate intake in UI; FastAPI + Twilio only if time remains), auth/roles, real IoT sensors, mobile app, multi-tenant, payments, vector database, separate backend, Haiku cost-cut path (only on request).

## 13. Build order (for the implementation plan)

1. Project scaffold, `pyproject.toml`, `core/db.py`, `data/generate.py` + tests
2. `core/llm.py` + `core/triage.py` + tests
3. `core/assistant.py` + docs + tests
4. `core/maintenance.py` + tests
5. `core/sustainability.py` + tests
6. Streamlit pages, theme, cache warm-up
7. Eval set + eval script
8. Pitch deck outline
