# TownshipOS — Google Stitch Design Prompt

Paste **Section 0** first (it sets the design system), then paste one screen section at a time.

---

## 0. Product & Design System

I'm designing **TownshipOS**, an AI-powered property management platform for a Malaysian
residential township (Serenia Heights, Sepang), built for the Sime Darby Property hackathon.

It has two portals behind one login:
- **Resident portal** — mobile-first. One screen: report a maintenance problem.
- **Facility Manager portal** — desktop web. Five screens: dashboard, complaint triage,
  predictive maintenance, sustainability, knowledge assistant.

The visual direction is **corporate operations software with a Malaysian property-developer
identity** — serious, dense with real data, trustworthy. Not a playful consumer app, and not a
generic dark SaaS dashboard. Think Bloomberg terminal restraint with a property-brand palette.

### Color

| Token | Hex | Use |
|---|---|---|
| Navy | `#0B1F3A` | Sidebar background, page header banners, headings, primary text on yellow |
| Yellow | `#F2B705` | Brand accent, primary CTA background, active nav indicator |
| Page background | `#F4F7FB` | Body background behind all cards |
| Card white | `#FFFFFF` | Every card and panel surface |
| Border | `#E4EBF5` | All card borders and dividers |
| Muted text | `#6B7A99` | Labels, metadata, captions |
| Body text | `#2D3748` | Primary reading text |
| Secondary text | `#4A5568` | Summaries inside cards |
| Sidebar text | `#C9D3E0` | Sidebar body text |
| Sidebar active text | `#E8ECF4` | Nav item labels |
| Header subtitle | `#8A9DB5` | Subtitle inside navy header banners |

**Urgency colors** (used as pill backgrounds and 4px card accent borders):

| Level | Hex |
|---|---|
| Emergency | `#C62828` (red) |
| High | `#EF6C00` (orange) |
| Medium | `#F2B705` (yellow) |
| Low | `#2E7D32` (green) |
| Untriaged | `#607D8B` (slate) |
| Needs human | `#6A1B9A` (purple) |

### Typography

- **Header banner title** — 26px, weight 700, letter-spacing −0.3px, white
- **Header banner eyebrow** — 12px, weight 600, letter-spacing 2px, yellow, uppercase: `TOWNSHIPOS`
- **Header banner subtitle** — 13px, `#8A9DB5`
- **Section label** — 11px, weight 600, letter-spacing 1.5px, uppercase, `#6B7A99`, with a small
  icon 7px to its left at 65% opacity. This is the main structural device on every screen.
- **Body** — 14px, line-height 1.5
- **Metadata** — 12px, `#6B7A99`
- **Metric value** — large, weight 700, navy
- **Metric label** — 12px, `#6B7A99`

### Components

**Page header banner** — navy `#0B1F3A` block, 12px radius, 18px 24px padding, 16px bottom margin.
Stacks: yellow eyebrow `TOWNSHIPOS`, then white title, then muted subtitle. Appears at the top of
every screen except login.

**Card** — white, 1px `#E4EBF5` border, 10px radius, soft shadow `0 1px 3px rgba(11,31,58,0.05)`.

**Accent card** — same card with a 4px solid left border in an urgency color (list items) or a 4px
top border (the triage result panel).

**Metric card** — white, 1px `#E4EBF5` border, 10px radius, 18px 20px padding. Small muted label
above a large bold navy value, with an optional small delta line beneath.

**Pill badge** — fully rounded (999px), 2px 10px padding, 12px, weight 600. White text on all
colors except yellow, which takes navy text for contrast.

**Primary button** — yellow `#F2B705` background, navy text, no border, weight 600, 8px radius.
Hover darkens to `#D9A504`. Usually full width.

**Secondary button** — transparent with a 1.5px `#CDD6E0` border, navy text, 8px radius.

**Sidebar** — navy `#0B1F3A`, 1px `rgba(255,255,255,0.06)` right border. Nav items have 8px radius;
hover is `rgba(242,183,5,0.10)`; the active item has a `rgba(242,183,5,0.18)` background **and a 3px
solid yellow left border**.

Use generous vertical rhythm between sections. Cards are flat and grounded — no floating shadows,
no gradients, no glassmorphism, no glow.

---

## 1. Login Screen

Full-page, no sidebar. Page background `#F4F7FB`. Everything centered.

**Hero block** — navy `#0B1F3A`, 16px radius, 36px 48px padding, 32px bottom margin, center-aligned:
- Yellow eyebrow, 12px, letter-spacing 3px, weight 600: `SIME DARBY PROPERTY`
- White wordmark, 44px, weight 800, letter-spacing −0.5px: `TownshipOS`
- Subtitle, 15px, `#8A9DB5`: `AI-powered facility management · Serenia Heights demo`

**Login card** — a centered column about 44% of the page width:
- A single text input, no visible label, placeholder `Enter your access code`
- A full-width primary yellow button: `Enter`
- A hint panel 14px below: `#F4F7FB` background, 8px radius, 10px 14px padding, 12px text,
  `#6B7A99`, line-height 1.8, with the codes in monospace:
  - `Resident demo: A15121223 · A12014567`
  - `Staff demo: 1234567 · 7654321`

One field serves both roles — the system detects a 7-digit number as staff and a letter-prefixed
code as a resident. Do not add tabs or a role selector.

**Error state** — a red inline message under the input:
`Residents: unit + 4-digit PIN e.g. A15121223 · Staff: 7-digit badge ID`

---

## 2. Sidebar (all logged-in screens)

Narrow navy column, full height.

**Top identity block**, 12px 8px 10px padding:
- Yellow, 10px, letter-spacing 2px, weight 600: `SIME DARBY PROPERTY`
- White, 16px, weight 700: `TownshipOS`
- Muted `#6B7A99`, 11px: `Facility Manager` — or `Unit A1512` for a resident

Then a `rgba(255,255,255,0.12)` divider.

**Nav items** (facility manager only) with small outline icons:
`Dashboard` · `Triage` · `Assets` · `Sustainability` · `Assistant`

The active item gets a `rgba(242,183,5,0.18)` background and a 3px yellow left border.
The resident portal has no nav list — only the identity block and sign-out.

**Bottom**: a sign-out button, `rgba(255,255,255,0.07)` background with a
`rgba(255,255,255,0.15)` border: `← Sign out`

---

## 3. Resident — Report an Issue (mobile-first)

Header banner: title `Report an Issue`, subtitle
`Snap a photo · share your location · describe the problem`.

The page asks for device location silently on load.
- **Granted** — a transient toast appears top-right and auto-dismisses:
  `Location captured — accuracy ±12 m`. Nothing else is shown; there is no permanent
  "your location" panel.
- **Denied** — a text input appears instead, labelled `Where is the problem?`,
  placeholder `E.g. Near the lift lobby, Block C, level 3`.

Then, stacked full width:

1. Section label `PHOTO` with a camera icon
2. A drag-and-drop file upload zone: `Attach a photo (optional but very helpful)`,
   accepting JPG/PNG/WEBP. When a photo is chosen, show it full width below the zone.
3. Section label `DESCRIPTION` with a pen icon
4. A textarea about 120px tall, placeholder:
   `E.g. Lubang besar di jalan masuk Block C / Lift stuck at level 5, making loud noise`
5. A full-width primary yellow button: `Submit Report`

**Success state** — replaces the form area:
- A green success panel:
  `Report submitted — Ticket #47` / `AquaFix Plumbing Sdn Bhd has been notified (SLA 8 h)`
- Two metric cards side by side: `Category` → `Plumbing`, and `Urgency` → `High`
- A collapsed expander: `Our reply to you`, containing two labelled blocks of reply text,
  `Bahasa Malaysia` and `English`

**Duplicate state** — an amber warning panel instead:
`This issue has already been reported.` / `Ticket #31 · plumbing · Status: open` /
`AquaFix has been notified. We will update residents once it is resolved.`

---

## 4. FM — Dashboard (desktop)

Header banner: title `One AI brain for running a township`, subtitle
`Sime Darby Property University Hackathon · demo township: Serenia Heights`.

**Row of 4 metric cards:**

| Label | Value | Delta |
|---|---|---|
| Messages today | 80 | — |
| Tickets created | 23 | `57 deduplicated / informational` |
| Urgent (high + emergency) | 9 | — |
| Need a human | 3 | — |

**Morning Brief card** — white card, 16px 20px padding. Section label `MORNING BRIEF` inside,
then a bulleted list at 14px with line-height 1.9 and bold timestamps:

- **06:12** Leak photo from unit 12-3 triaged → AquaFix notified, resident replied in BM & EN
- **07:00** Overnight asset re-scoring flags **Pump P2, Block A** at **76%** 30-day failure risk
- **07:00** Sustainability flags **Block C water +40 %** vs baseline — probable leak
- **09:30** You are here. 9 urgent tickets, 3 need a decision.

**Section label `LATEST TICKETS`** with a ticket icon, then 8 stacked ticket cards. Each is a white
card, 12px 16px padding, 8px bottom margin, with a **4px left border in its urgency color**:
- Row 1: an urgency pill (`emergency` / `high` / `medium` / `low`) beside a bold navy `#47`
- Row 2: the complaint text at 14px, truncated to about 110 characters —
  e.g. `Bocor dari atas, air menitik masuk unit 12-3`
- Row 3: 12px muted metadata — `plumbing · AquaFix Plumbing Sdn Bhd · SLA 8 h`

Show a mix of urgency levels so the left borders read as red, orange, yellow and green down the list.

**Section label `OPEN ISSUE MAP`** with a map-pin icon, then a street map zoomed to a residential
township, with scattered pins clustered around four apartment blocks.

---

## 5. FM — Complaint Triage (desktop)

Header banner: title `Complaint Triage`, subtitle
`Photo + message in → category, urgency, contractor, SLA and a bilingual reply out`.

**Two equal columns.**

**Left — intake.** Section label `SIMULATED WHATSAPP INTAKE` with a WhatsApp icon, then:
- A dropdown: `Load a sample message`, first option `(type your own)`, the rest real complaints
  in Malay, English and Chinese
- A file upload: `Voice note (optional)` — mp3, wav, m4a, ogg, webm, mp4.
  When present, a small caption underneath: `Transcribed: Lif rosak tingkat 5, bunyi pelik`
- A textarea ~120px: `Resident message`, placeholder `Lif rosak tingkat 5, bunyi pelik`
- A file upload: `Photo (optional)`, preview capped at 320px wide
- A full-width primary yellow button: `Triage`

**Right — result.** A white card with a **4px top border in the urgency color**, 16px 18px padding:
- A wrapping row: `Ticket #47` at 18px weight 700 navy, then an urgency pill, then a navy category
  pill, then optionally a purple `needs human` pill
- The summary at 14px `#4A5568`
- A 12px muted line: `Location: Blok C aras 3 · Language: ms`

Below that card, three metric cards in a row: `Contractor` → `AquaFix Plumbing Sdn Bhd`,
`SLA` → `8 h`, `Confidence` → `92%`.

Then section label `DRAFTED REPLY` with a reply-arrow icon, and two read-only textareas about 80px
tall, labelled `Bahasa Malaysia` and `English`. Finish with a green confirmation:
`Ticket created and contractor notification queued (simulated).`

**Full width below both columns:** a horizontal divider, section label `TICKET QUEUE` with a
checklist icon, a multi-select `Status` chip group (`untriaged`, `open`, `assigned`, `closed` —
first two selected), and a dense data table with columns:
`id · created_at · urgency · category · contractor · sla_hours · needs_human · status · raw_text`.

---

## 6. FM — Predictive Maintenance (desktop)

Header banner: title `Predictive Maintenance`, subtitle
`30-day failure risk per asset, from 24 months of service logs`.

**Top alert**, as a prominent heading rather than a box:
`⚠️ Pump P2, Block A — 76% failure risk in 30 days`
with a muted caption beneath:
`Drivers: breakdowns last 12m, age months · Contractor: AquaFix Plumbing Sdn Bhd`

A primary yellow button: `Create pre-emptive work order`. On click, a green confirmation:
`Work order #4 created for AquaFix Plumbing Sdn Bhd (scheduled, not emergency).`

**Two columns, 2:1 ratio.**

**Left (wider) — `Risk ranking`.** A data table where the `risk %` column renders as a horizontal
progress bar from 0–100 rather than a number. Columns:
`asset_id · name · block · type · risk % · top_drivers · contractor`.
Rows are sorted by descending risk, so the bars form a descending staircase. Sample rows:
`P2-A · Pump P2, Block A · A · pump · 76 · AquaFix Plumbing Sdn Bhd`, then lifts, gensets,
chillers and gates at lower risk.

**Right (narrower) — `What the model learned`.** A horizontal bar chart of machine-learning feature
importances, with these five labels on the y-axis:
`age_months`, `avg_runtime_hours`, `breakdowns_last_12m`, `days_since_service`, `vibration_score`.
Bars run 0.00 to about 0.35. A muted caption beneath:
`Cross-validated AUC 0.82 · 1152 training rows`.

**Below, full width:** a dropdown `Service history` listing asset IDs, then a data table of that
asset's maintenance log (date, kind, runtime hours, vibration score, notes), newest first. Then a
subheading `Open work orders` with another table.

---

## 7. FM — Sustainability (desktop)

Header banner: title `Sustainability`, subtitle
`Water & energy consumption by block vs baseline · Peninsular grid 0.74 kg CO₂/kWh`.

A `Month` dropdown, newest first (`2026-08`).

**Row of 4 metric cards:**

| Label | Value | Delta |
|---|---|---|
| Electricity (kWh) | 214,596 | `-1.0% vs prev month` |
| Water (m³) | 13,180 | `+9.2% vs prev month` |
| CO₂e (tonnes) | 158.80 | — |
| Anomalies this month | 1 | `⚠ review below` |

**Section label `BLOCK BREAKDOWN`** with a grid icon, then a four-row table
(blocks A, B, C, D) with columns `Block · Electricity (kWh) · Water (m³) · CO₂e (tonnes)`.

**Section label `CONSUMPTION TREND — ALL BLOCKS`** with a line-chart icon, then two line charts
side by side. Both span 24 months on the x-axis (`2024-09` through `2026-08`) with four series
(A, B, C, D). Left chart is electricity, y-axis `kWh`, roughly 0–70,000. Right chart is water,
y-axis `m³`, roughly 0–4,000. The water chart shows Block C spiking sharply in the final month.

**Section label `ANOMALIES — ALL MONTHS`** with a warning-triangle icon, then stacked anomaly
cards — white, 12px 16px padding, 8px bottom margin, **4px left border** (orange `#EF6C00` when the
deviation exceeds 30%, yellow `#F2B705` otherwise):
- Line 1, weight 600 navy 14px: `Block C · 2026-08 · m³`
- Line 2, 14px `#2D3748`: `4,500 m³ — 35.3% above baseline (3,327 m³ avg)` with the percentage bold

Second card: `Block A · 2026-05 · kWh` / `68,222 kWh — 31.8% above baseline (51,778 kWh avg)`.

Empty state is a centered muted card: `No statistical anomalies detected (z-score threshold: 2.5).`

**Section label `ESG NARRATIVE REPORT`** with a document icon, a muted caption
`AI-written monthly sustainability section — cite in your JMB committee report.`, and a primary
yellow button `Generate ESG narrative for 2026-08`. Below it, room for generated rich text with a
heading, a table and paragraphs.

---

## 8. FM — Knowledge Assistant (desktop)

Header banner: title `Knowledge Assistant`, subtitle
`Ask about SOPs, SLAs, Strata Management Act, and renovation guidelines`.

A collapsed expander: `5 documents loaded`, which opens to a bulleted list:
`01 Lift Maintenance SLA`, `02 Plumbing SLA`, `03 Renovation Guidelines`, `04 Emergency SOP`,
`05 Strata Management Act 2013 Extracts`.

**Section label `ASK A QUESTION`** with a question-mark-circle icon, then a text input labelled
`Question`, placeholder:
`E.g. What is the SLA for emergency lift breakdown? / Berapa lama SLA untuk kerosakan lif?`
Then a full-width primary yellow button: `Ask`.

**Answer area** — a white card, 20px 22px padding, with the section label `ANSWER` inside at the
top, followed by rich text: a direct answer paragraph, then the supporting clause.

**Section label `SOURCES`** with an open-book icon, then stacked source chips — `#F4F7FB`
background, 1px `#E4EBF5` border, 8px radius, 8px 14px padding, 13px navy text — one per cited
document, e.g. `02 Plumbing SLA`.

**Section label `SAMPLE QUESTIONS`** with a list icon, then five full-width secondary buttons
stacked vertically:
- `What is the SLA for a burst pipe emergency?`
- `Can a resident hang laundry on the balcony railing?`
- `What are the permitted renovation hours under the guidelines?`
- `What does the Strata Management Act say about JMB quorum?`
- `Who is responsible for common area lift maintenance?`

---

## 9. Things to avoid

- No blue-to-purple gradients, no glow, no glassmorphism, no blurred background orbs
- No dark mode — this is a light operations tool on a `#F4F7FB` background
- Do not make every card the same weight; the urgency left-borders and the navy header banners
  are what create hierarchy
- Do not round everything into pills — only badges are fully rounded; cards stay at 10px
- Keep the data tables dense and real. Do not replace them with decorative cards
- Use real Malaysian content: contractor names like `AquaFix Plumbing Sdn Bhd`,
  `OTIS Malaysia`, `Voltra Electrical Sdn Bhd`, `CoolTech M&E Sdn Bhd`, `SecureGuard Services`,
  and Malay complaint text like `Lif rosak tingkat 5, bunyi pelik`
