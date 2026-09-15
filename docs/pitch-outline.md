# TownshipOS — pitch outline (10 slides, 3-minute demo inside)

1. **Title** — TownshipOS: one AI brain for running a township. Team, university.
2. **The morning** — 06:12 leak photo, 80 WhatsApp/email/phone messages, 16 lifts, 60 assets, 3 languages. Managers read; nothing is triaged.
3. **Why it matters to Sime Darby Property** — SLA compliance under the Strata Management Act 2013 (Act 757); emergency call-outs cost multiples of scheduled maintenance; utility leaks and manual ESG reporting; brand and resale value sell the next phase; 20+ townships.
4. **What TownshipOS does** — intake → triage → route → first reply automated; humans handle exceptions. Four modules on one screen.
5. **LIVE DEMO 1: Triage** — photo + "Lif rosak tingkat 5, bunyi pelik" → Lift / High / OTIS 4h / BM+EN reply → ticket.
6. **LIVE DEMO 2: Predictive maintenance** — top-risk asset (currently Pump P2, Block A at 76 %) → pre-emptive work order. "What the model learned" chart, cross-validated AUC 0.81.
7. **LIVE DEMO 3 + 4: Sustainability + Ask** — Block C water +35 % → ESG section with tCO₂e; "Penalty if OTIS misses the 4h SLA?" → RM 500, clause 4.1 cited.
8. **How it works** — Claude Opus 5 vision + typed structured output; deterministic routing table; scikit-learn on service logs; rolling z-score; SOP docs as cited documents (1M context, no vector DB). Streamlit + SQLite. Built by one coder in Python.
9. **Four pillars** — Innovation (photo → typed ticket, cited answers), Collaboration (one queue for PM, JMB/MC, contractors), Sustainability (leaks caught in a month; CO₂e at the Energy Commission grid factor 0.74 kgCO₂e/kWh), Future Ready (scales to 20+ townships, DLP tracking, WhatsApp/IoT plug-in later).
10. **Ask** — pilot in one Sime Darby township with real ticket history; mentorship on SLA data and ESG reporting formats. All numbers shown are from synthetic data.

Speaker notes: never claim Sime Darby figures; say "illustrative". Rehearse once with the API key unset to prove the cached demo path works (every page must still render, and Triage/Ask must show the friendly "unavailable" message, not a traceback).
