# TownshipOS — Frontend

> AI-powered township operations platform built for the Sime Darby Property Hackathon.  
> Streamlit application with two portals: **Resident** and **Facility Manager**.

---

## What It Does

TownshipOS turns the daily grind of managing a residential township into a near-automated workflow. Residents snap a photo and describe a problem; the system triages it, routes it to the right contractor, and replies in both Bahasa Malaysia and English — all in under 30 seconds.

| Portal | Who uses it | What they can do |
|--------|-------------|------------------|
| Resident | Unit owners / tenants | Report issues with photo + location, track ticket status |
| Facility Manager | On-site FM staff | AI triage console, live dashboard, sustainability monitor, SOP assistant |

---

## Pages

### Resident Portal

**Report an Issue** (`pages/0_Report.py`)
- Captures device location silently (toast notification on grant, address input on denial)
- Photo upload with AI vision analysis
- Bilingual AI reply (BM + EN) returned instantly after submission
- Duplicate detection — flags if the same issue is already open nearby

### FM Portal

**Complaint Triage** (`pages/1_Triage.py`)
- Simulated WhatsApp intake with sample resident messages
- Voice note transcription via Whisper
- Claude classifies complaint → assigns category, urgency, contractor, SLA
- Drafted bilingual reply ready to send
- Live ticket queue with status filter

**Dashboard** (`pages/fm_dashboard.py`)
- Open ticket count, emergency count, average resolution time
- Latest tickets table
- Interactive map of open issues by GPS coordinate

**Sustainability** (`pages/fm_sustainability.py`)
- Monthly electricity (kWh) and water (m³) consumption by block
- Z-score anomaly detection — flags blocks spiking vs. their own baseline
- One-click AI-written ESG narrative for the JMB committee report

**Knowledge Assistant** (`pages/fm_assistant.py`)
- Full-text RAG over SOP, SLA, Renovation Guidelines, and Strata Management Act documents
- Ask in Bahasa Malaysia or English
- Cites the source document for every answer

---

## Login System

Single input field — the system auto-detects the role:

| Format | Role | Example |
|--------|------|---------|
| 7-digit number | FM Staff | `1234567` |
| Letter + unit digits + 4-digit PIN | Resident | `A15121223` |

Demo mode: any validly formatted code is accepted — no lookup table. Residents see their unit code in the sidebar; FM staff see "Facility Manager".

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| UI framework | Streamlit 1.40+ |
| AI / LLM | Claude via OpenRouter (`anthropic/claude-opus-4-5` default) |
| Speech-to-text | Whisper via OpenRouter |
| Database | SQLite (local file `townshipos.db`) |
| ML model | scikit-learn Gradient Boosting (predictive maintenance) |
| Data | pandas, synthetic generator in `data/generate.py` |
| Icons | Font Awesome 6.7.2 (CDN) |

---

## Project Structure

```
townshipos/
├── app.py                  # Entry point — login router, navigation
├── ui.py                   # Shared CSS, helpers, section_label()
├── pages/
│   ├── 0_Report.py         # Resident: report an issue
│   ├── 1_Triage.py         # FM: complaint triage console
│   ├── fm_dashboard.py     # FM: live operations dashboard
│   ├── fm_sustainability.py# FM: water & energy monitoring
│   └── fm_assistant.py     # FM: SOP / SLA knowledge assistant
├── core/                   # Business logic (see TownshipOS-Backend)
│   ├── llm.py
│   ├── triage.py
│   ├── sustainability.py
│   ├── assistant.py
│   ├── maintenance.py
│   ├── db.py
│   └── voice.py
├── data/
│   ├── generate.py         # Synthetic data generator
│   ├── complaints.jsonl    # Sample complaint messages
│   └── docs/               # Knowledge base (.txt files for RAG)
└── pyproject.toml
```

---

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- An [OpenRouter](https://openrouter.ai) API key

### 1. Clone and install

```bash
git clone https://github.com/TownshipOS-Hackathon/TownshipOS-Frontend.git
cd TownshipOS-Frontend
uv sync
# or: pip install -e .
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-...your-key-here...

# Optional — override the default model
# OPENROUTER_MODEL=anthropic/claude-sonnet-4-5
```

### 3. Generate sample data

```bash
python data/generate.py
```

This creates `townshipos.db` with synthetic assets, service logs, utility readings, and resident complaints.

### 4. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

**Demo credentials:**
- FM Staff: any 7-digit number e.g. `1234567`
- Resident: letter + unit digits + 4-digit PIN e.g. `A15121223`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | API key from openrouter.ai |
| `OPENROUTER_MODEL` | No | `anthropic/claude-opus-4-5` | LLM model ID to use |

> The app includes a JSON response cache (`data/.llm_cache/`). Many demo flows work without a key if the cache is pre-warmed.

---

## Related

- **[TownshipOS-Backend](https://github.com/TownshipOS-Hackathon/TownshipOS-Backend)** — AI core modules and data layer, documented independently
