# TownshipOS

One AI brain for running a township — complaint triage, predictive maintenance, sustainability intel and a cited SOP assistant for property-management teams. Built for the Sime Darby Property University Hackathon.

## Run

    uv sync
    uv run python -m data.generate          # synthetic township data -> townshipos.db
    export ANTHROPIC_API_KEY=sk-ant-...     # needed for live Triage / Ask / ESG calls; cached responses work offline
    uv run streamlit run app.py

## Test

    uv run pytest                            # offline, ~10 s
    uv run python -m eval.run_triage_eval    # real API, ~USD 1, results cached in cache/

## Layout

- `core/` — pure Python modules: `triage`, `assistant`, `maintenance`, `sustainability`, `db`, `llm`
- `pages/` — Streamlit pages; `app.py` is the dashboard; `ui.py` shared helpers
- `data/` — generator, SOP documents, complaints and the triage eval set
- `eval/` — triage eval script (precision / recall / F1 per category, emergency recall)
- `cache/` — cached Claude responses (commit them so the live demo never depends on the network)
- `docs/superpowers/` — design spec and implementation plan; `docs/pitch-outline.md` — deck outline
