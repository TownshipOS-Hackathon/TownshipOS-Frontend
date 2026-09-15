# Kickoff prompt — TownshipOS (Sime Darby Property University Hackathon)

Paste everything below into a new Claude Code session opened in `C:\Users\user\townshipos`.

---

I am a Malaysian university student joining the **Sime Darby Property University Hackathon** (theme: "Ideas Into Impact"; pillars: Innovation, Collaboration, Sustainability, Future Ready; benefits: mentorship, connections, rewards). Sime Darby Property builds and runs integrated townships (City of Elmina, Bandar Bukit Raja, Serenia City, Ara Damansara, etc.). The poster features Elmina Lakeside Mall.

In a previous session we already brainstormed and **decided** the project. Do not re-open these decisions — continue from them.

## Decisions already made

- **Project:** **TownshipOS** (working name) — "one AI brain for running a township."
- **Primary user:** property / facility management teams at Sime Darby (not residents, not homebuyers).
- **Shape:** an AI-integrated multi-feature platform (like an internal ops platform), scoped to Sime Darby's world.
- **Team skills:** AI/ML, Python. No strong frontend skills — keep frontend effort minimal.
- **Approach chosen ("combo"):** the platform frame (A) + photo-based complaint/defect triage as the hero demo (B) + a small sustainability panel (C).

## Pitch (agreed)

Sime Darby's facility teams juggle thousands of units, hundreds of assets, and a daily flood of resident complaints across WhatsApp, email, and phone. TownshipOS turns that chaos into triaged tickets, predicted failures, and sustainability insights — before a manager reads a single message. Intake, classification, routing and first reply are automated; humans handle exceptions and decisions.

Why Sime Darby cares: SLA compliance and response time; fewer emergency breakdowns (emergency call-outs cost multiples of scheduled maintenance); leak/energy detection = utility savings + credible ESG numbers; brand and resale value sell the next phase; one AI brain scales across 20+ townships with no extra headcount.

Domain facts to use in the pitch: post-handover townships are run by property management teams often together with the JMB/MC under the **Strata Management Act 2013 (Act 757)**; new units carry a **24-month Defect Liability Period**; assets (lifts, pumps, gensets, chillers, gates, CCTV, landscaping) each have a contractor, an SLA and a service schedule; residents write in BM, English and Chinese; Sime Darby Property has public ESG / net-zero commitments and sustainability reporting is usually done by hand from utility bills.

## Features (agreed)

| # | Feature | AI under the hood | Demo moment |
|---|---|---|---|
| 1 | **Complaint Triage** (hero) | Claude vision + structured output | Resident sends photo + "Lif rosak tingkat 5, bunyi pelik" → card: Lift / High urgency / assign OTIS (SLA 4h) + drafted reply in BM & English → ticket created |
| 2 | **Predictive Maintenance** | scikit-learn classifier on asset service logs (real ML) | "Lift L3, Block B — 78% failure risk in 30 days" → one click creates a pre-emptive work order |
| 3 | **Sustainability Intel** | rolling z-score anomaly detection + Claude writes the ESG summary | "Block C water +40% vs baseline — probable leak" + auto-generated monthly ESG report with CO₂e |
| + | **Ask TownshipOS** | Claude with SLA/SOP docs passed as cited `document` blocks — no vector DB | "Penalty if OTIS misses the 4h SLA?" → answer citing the exact clause |

Day-in-the-life scenario for the pitch: 06:12 leak photo + "Bocor dari atas, unit 12-3" → triaged, contractor notified, reply drafted before the manager wakes up; 07:00 overnight asset re-scoring flags Lift L3; 07:00 sustainability flags Block C water; 09:30 manager sees 80 messages became 23 tickets, 3 urgent, 5 need a human, and asks the assistant an SLA question answered with a citation.

## Stack (agreed — lazy on purpose)

- **Streamlit** app with 4 pages (Triage, Assets, Sustainability, Ask). No separate backend, no React. Theme: navy + yellow to match Sime Darby.
- **`core/`** package: `triage.py`, `maintenance.py`, `sustainability.py`, `assistant.py` — each independently testable, pure Python functions.
- **SQLite** (stdlib `sqlite3`) for tickets, assets, service logs, utility readings. One file, zero setup.
- **Claude Opus 5** (`claude-opus-5`) via the official `anthropic` Python SDK for triage (vision), the assistant, and the ESG narrative. Use `client.messages.parse()` with Pydantic models so triage returns typed JSON. Load SOP/SLA docs as `document` content blocks with `citations: {enabled: true}` and `cache_control` on them (1M context makes RAG infra unnecessary). **Before writing any Anthropic SDK code, invoke the `claude-api` skill** and follow it (adaptive thinking, no prefill, `output_config`, current model IDs).
- **scikit-learn + pandas** for the maintenance model and anomaly detection.
- Budget: whole demo ≈ USD 10–20 of API credit. (Haiku 4.5 for bulk text-only classification is an optional cost cut — only if I ask.)

## Data plan (agreed — all synthetic, generated by script)

- ~200 synthetic complaints (BM/EN/Chinese mix) + ~10 real photos I will take on campus (cracked wall, leaking pipe, broken light, blocked drain) for the vision demo.
- Asset registry (~60 assets across 4 blocks: lifts, pumps, gensets, chillers, gates) + 24 months of service logs. Maintenance model features: `age_months`, `days_since_service`, `breakdowns_last_12m`, `avg_runtime_hours`, `vibration_score`; label: `failed_within_30d`. Report top features as the explanation.
- Utility readings: monthly kWh and m³ per block for 24 months with seasonality and injected anomalies. Detect with rolling z-score (explainable, one-liner). CO₂e using the Malaysia grid emission factor ≈ 0.58 kgCO₂/kWh (verify the latest Energy Commission figure).
- 4–5 short documents for the assistant: Lift Maintenance SLA, Plumbing SLA, Renovation Guidelines, Emergency SOP, extracts from the Strata Management Act 2013 (public).

## Demo script (3 minutes)

1. Photo + Manglish complaint → triage card → ticket + drafted bilingual reply.
2. Assets page → Lift L3 risk 78% → create pre-emptive work order.
3. Sustainability page → Block C water anomaly → generated ESG monthly summary.
4. Ask → SLA penalty question → cited answer.

## Explicitly cut (do not build)

Real WhatsApp webhook (simulate intake in the UI; add FastAPI + Twilio only if time remains), auth/roles, real IoT sensors, mobile app, multi-tenant, payments.

## Working style

Ponytail mode: shortest working diff, stdlib and native first, no speculative abstractions, one runnable check per non-trivial module. Skills and rules from my global config apply (brainstorming → spec → writing-plans → TDD).

## What to do first in this session

1. Ask me these, then proceed: hackathon deadline; submission format (pitch deck only, video, or live demo?); team size; whether a working prototype is required or a pitch is enough.
2. Continue the brainstorming **Part 2** that was pending: per-module interfaces (inputs/outputs of each `core/` function), error handling (LLM output validation, refusal stop reason, retry), testing/eval plan (fixtures for each module, a small triage eval set with precision/recall), and the final pitch mapping to the four pillars. Get my approval per section.
3. Write the spec to `docs/superpowers/specs/YYYY-MM-DD-townshipos-design.md`, `git init` this folder, commit.
4. Invoke the `writing-plans` skill, then implement with TDD in this order: data generators → `core/triage.py` → `core/assistant.py` → `core/maintenance.py` → `core/sustainability.py` → Streamlit pages → pitch deck outline.
