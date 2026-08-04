# Business Briefing Report — design spec

**Date:** 2026-08-04
**Status:** ratified (brainstorm), ready for implementation plan
**Depends on:** persisted run store (R-IDX-5), leverage/priced view (A5), service rubric A9, swap catalogue v0.1
**Relates to:** R-OUT-2 (PDF report + live query; "self-contained HTML evidence companion is a first-engagement deliverable")

## 1. Problem

The current `report.json` / `report.pdf` is a faithful **instrument audit** artifact: counts, shares,
coverage, validation tiers, drop log, manifest. `render_report()` is model-free by design (AC-15) and
the PDF is literally a `json.dumps` of each section piped into `fpdf` cells — a debug dump, not a
designed document.

A business reader (RevOps SME, Commercial Principal) cannot act on it as-is:

1. It speaks in **machine IDs** (`manual_after_call_work`, `first_contact_resolution`), not business language.
2. It has **no connective story and no "Monday action"** — a list of item cards, no exec narrative, no ranked plays.
3. On the current O1 rehearsal artifact the narratives are additionally **hollowed by the known
   evidence-sampling defect** (synthesis received no snippet ranges, so every narrative honestly says
   "cannot be verified"). This is already fixed for the next run and is *not* what this spec addresses.

**This spec** adds a business-facing deliverable that re-renders the same persisted run for a commercial
reader — one headline number, plain-language findings, effort-ranked plays with a remedy action, and money
attached to the cheap wins — **without touching the frozen, calibrated instrument.**

## 2. Scope

**In scope (v1):**
- A new **model-free presentation layer** over the already-persisted run.
- A versioned presentation config mapping rubric item IDs → business labels + reader glosses, and declaring
  headline-metric membership.
- Two rigorously-defined, reproducible headline metrics.
- Three output artifacts: `briefing.json` (machine-readable), `briefing.html` (self-contained,
  first-engagement deliverable per R-OUT-2), `briefing.pdf` (the same HTML/CSS printed to PDF — a faithful
  "screenshot-type" view, **not** another fpdf dump).
- A read-only CLI: `cix briefing <run_dir>`.
- A small extension to `cix query` — a `--metric <name>` handle that resolves a headline metric to its
  underlying set (e.g. `avoidable_contact_rate` → the 33 interaction IDs), so every headline number in the
  briefing is traceable to source (§5.1). Read-only, same store-access pattern as the existing query modes.

**Explicitly out of scope (deferred):**
- **Business-register synthesis prompt change.** The synthesis prose stays as-is for v1 (instrument frozen,
  prompt hashes unchanged). A later change may rewrite the synthesis prompt so narratives come out
  business-shaped from the pipeline itself; that is a separate, post-real-run change.
- Any change to `report.json` / `report.pdf` — the technical report remains the audit deliverable. The
  briefing **supplements** it.
- Any change to synthesis, the evidence gate, aggregation, or any frozen threshold.
- Live/interactive query inside the static HTML (the briefing names the `cix query` handles; resolution
  stays in the CLI).

## 3. Architecture

Four new pieces, all **model-free** (they read the persisted run only — honoring AC-15 / R-IDX-5). Nothing
touches synthesis, the evidence gate, or any frozen threshold.

### 3.1 `configs/briefing_presentation_v1.yaml` (new versioned artifact)

A reviewable, versioned config — peer to the rubric.

- `version: "1.0.0"`, `requires: { rubric_version: "1.0.0" }`.
- Per rubric `item_id`:
  - `business_label` — short human label (e.g. `manual_after_call_work` → "Manual after-call admin").
  - `gloss` — one-line reader explanation.
- `headline_metrics:` — declares **membership only** (which item IDs compose each metric); the formula lives
  in code. E.g. `avoidable_contact_rate.members: [repeat_contact_unresolved, billing_defect_driver,
  status_chase_inbound, unanticipated_failure]`.
- Monday-action text is **not** stored here — it is pulled from the swap catalogue's existing `substitute`
  field, so remedies have one source of truth.

### 3.2 `src/cix/briefing.py`

- `build_briefing(payload, presentation_cfg, store_ro) -> dict` — pure builder. Transforms the persisted
  payload + config into the business structure (§4). Opens the run store **read-only** (as `query.py` does)
  only where a metric needs interaction-level truth (the union metric, §5). Never calls a model; never
  mutates the store. Enforces the honesty rules (§6).
- `render_briefing_html(briefing) -> str` — deterministic; one **self-contained** HTML string (inline CSS,
  no external assets).
- `render_briefing_pdf(html) -> bytes` (or writes file) — prints that same HTML/CSS to PDF so the PDF *is*
  the HTML view. Engine: **WeasyPrint** (HTML/CSS → PDF, no browser).

### 3.3 CLI: `cix briefing <run_dir> [--no-pdf]`

- Read-only over a persisted run; writes `briefing.json` + `briefing.html` + `briefing.pdf` into `<run_dir>`.
- Works on any existing run (renders `runs/svc-run/` immediately, for the demo).
- Fails closed with a clear message on: config↔rubric version mismatch, missing persisted synthesis, or a
  referenced swap absent from the catalogue.
- `--no-pdf` skips WeasyPrint (for environments without its system libs); HTML + JSON still emit.

### 3.4 `cix query --metric <name>` (small extension)

Adds a `--metric` mode to the existing read-only `cix query`, resolving a named headline metric to its
underlying set — `avoidable_contact_rate` → the distinct interaction IDs behind the rate. Same `mode=ro`
store-access pattern as `--item`/`--quote`; no new mutation surface. This is what makes every headline number
in the briefing traceable to source.

### 3.5 Module boundaries

`briefing.py` = builder (data→data) + renderer (data→html/pdf); config = the label/metric vocabulary; CLI =
the read-only entry point. Each is independently testable; the builder never calls a model or mutates the store.

## 4. Briefing content model (`briefing.json`)

| Block | Content | Source |
|---|---|---|
| `meta` | O-level banner, rubric/catalogue versions, source manifest hash | manifest |
| `headline` | the two metrics (§5), each with `value`/`band`, `members`, `method`, `query`, honesty label | builder + store |
| `whats_working` | positive-polarity findings (e.g. `first_contact_resolution` 82/100) | payload, polarity filter |
| `plays` | **Class-A automatable**, effort-ranked: label, gloss, count/unit, band, Monday-action (swap `substitute`), so-what | leverage grid + catalogue |
| `upstream` | **Class-D** fix-at-source defects (billing 19, repeat-contact 8) | leverage `class_d` |
| `watch_list` | shelf items with no remedy, negative polarity (unanticipated_failure 11, knowledge_inconsistency 6, status_chase 6) | leverage shelf |
| `trust` | coverage, validation pass/fail summary, drop summary, the O1 evidence-gap note, manifest ref | payload |

**Effort ranking of plays:** effort `low < medium < high`, outcome `large > medium > small`. Class-A only in
`plays`; Class-D in `upstream`; shelf (no remedy) in `watch_list`. Positives always route to `whats_working`,
never `watch_list`, regardless of shelf membership.

**So-what composition** (deterministic, no model): `"{business_label}: {count} {unit}[ ({share} of eligible)]
— {gloss}"`. A play row reads:

> **1 · Manual after-call admin** — 87 occurrences · *Low effort, large payoff* · **$3,480–$10,440/yr**
> *(indicative, inferred)* · **Do:** capture-at-source structured extraction (`SW-ADMIN-CAPTURE`)

## 5. Headline metrics (honesty-critical)

Both are defined, reproducible, and resolvable via `cix query`.

### 5.1 Avoidable-contact rate (count-based, interaction-unit only)

- **Definition:** distinct interactions matching **≥1** negative *interaction-unit* pattern —
  `{repeat_contact_unresolved, billing_defect_driver, status_chase_inbound, unanticipated_failure}` — over
  eligible interactions.
- **Computed as a set union over the `hits` table**, never a sum. On `runs/svc-run`: naïve sum =
  8+19+6+11 = **44**; true distinct union = **33** → **33 / 100 = 33%** (11 interactions would be
  double-counted by summing).
- **Unit safety:** occurrence-unit items are *structurally excluded* from this metric — counts never cross units.
- **Resolvable:** the union is a concrete set of interaction IDs → `cix query <run> --metric
  avoidable_contact_rate` lists them.
- **Honesty label:** inherits the run's O-level (O1 synthetic here).

### 5.2 Indicative automatable opportunity (dollar, additive)

- **Definition:** sum of the **Class-A** priced bands — `manual_after_call_work` ($3,480–$10,440) +
  `deterministic_request` ($380–$1,140) + `avoidable_transfer` ($180–$540) = **$4,040–$12,120 / yr** on
  `runs/svc-run`.
- **Why summing is legal:** dollars are a common unit (the "never cross-sum" rule governs counts, not money),
  and the priced occurrences are distinct events, so time-saved value is additive.
- **Mandatory inline caveat:** `evidence_tier: candidate`, `inferred: true`, plus a note that two of the three
  plays share one remedy (`SW-STATUS-SELFSERVE`) — so *implementation effort* is shared even though *value* is
  additive.
- **Gated:** only appears when a catalogue is loaded; otherwise the section states its absence (mirrors the
  report's honest empty state).

## 6. Honesty rules (enforced in the builder, covered by tests)

1. **Never cross-sum units** — count metrics are single-unit; the union metric is interaction-only by construction.
2. **Union, not sum**, for any "N of M contacts" rate — dedupe overlap via the `hits` table.
3. **Every headline number carries its formula + a query handle** — no bare number stands alone.
4. **O-level banner mandatory and prominent**, pulled from `manifest.corpus_clearance`.
5. **Honest empty/zero states** — no catalogue → no cost metric (said in place); all-zero member set → omit,
   don't fake.
6. **The current evidence gap is stated, not hidden** — where a quote would sit, the O1 briefing says
   "quote-level evidence pending (next run)" rather than silently showing nothing.

## 7. Data flow

```
cix briefing <run_dir>
   ├─ load run store (mode=ro)
   ├─ load persisted payload (synthesis, aggregate rollup, priced, validations, manifest)
   │     — the same payload render_report() consumes; no re-synthesis
   ├─ load configs/briefing_presentation_v1.yaml
   │     └─ assert requires.rubric_version == manifest.rubric_version   (fail closed on mismatch)
   ├─ build_briefing(payload, presentation_cfg, store_ro) → briefing dict
   │     • union metric queried from hits (store_ro)
   │     • labels/glosses from config; actions from catalogue substitute
   │     • honesty rules (§6) enforced here
   ├─ write briefing.json
   ├─ render_briefing_html(briefing) → briefing.html     (self-contained, inline CSS)
   └─ render_briefing_pdf(briefing.html) → briefing.pdf   (same HTML/CSS via WeasyPrint; skipped by --no-pdf)
```

## 8. Dependencies

- **WeasyPrint** (HTML/CSS → PDF) added as an **optional/extra** dependency so core `cix` installs clean.
  `--no-pdf` is the graceful fallback when its system libs (pango/cairo) are absent.
- Alternative considered and rejected for v1: Playwright/headless-Chromium — truer "screenshot" fidelity but a
  heavy browser download; our CSS is simple enough that WeasyPrint fidelity is excellent.

## 9. Testing (TDD, matching existing suite style)

1. **Builder unit tests** (`build_briefing` over a fixture payload):
   - Structure: all seven blocks present; `plays` Class-A only and effort-ranked; `upstream` = Class-D;
     `watch_list` = negative-polarity shelf; positives route to `whats_working`.
   - **Union metric:** a fixture with known overlap asserts the distinct union, not the sum (the 44→33 case in miniature).
   - **Unit-safety guard:** feeding an occurrence-unit item into the interaction rate is structurally impossible / raises.
   - **Dollar metric:** sums Class-A bands, carries `inferred/candidate` + shared-remedy note; **absent when no catalogue**.
   - **O-level banner** always present and equal to `manifest.corpus_clearance`.
   - **Evidence-gap note** present when findings carry no quotes.
2. **Config validation:** version mismatch (config rubric ≠ manifest rubric) fails closed; missing swap ref fails closed.
3. **Golden render test:** `build_briefing` on `runs/svc-run` → `briefing.json` matches a committed golden
   (headline 33/100, $4,040–$12,120, the three plays in order). HTML contains the O1 banner, both headline
   metrics, and each play's Monday-action.
4. **Read-only guarantee:** `drop_log` count identical before/after `cix briefing`; no model client constructed.
5. **`--no-pdf`** path emits HTML + JSON and exits 0 without importing WeasyPrint.
6. **`cix query --metric avoidable_contact_rate`** on `runs/svc-run` lists 33 distinct interaction IDs,
   read-only (`drop_log` unchanged), and errors clearly on an unknown metric name.

## 10. Acceptance

- `cix briefing runs/svc-run` produces `briefing.json` + `briefing.html` + `briefing.pdf`.
- Headline avoidable-contact rate reads **33/100** (union, not 44) and resolves via `cix query`.
- Automatable opportunity reads **$4,040–$12,120/yr** with the inferred/candidate + shared-remedy caveat.
- O1 banner present; evidence-gap note present; technical `report.*` untouched; `drop_log` unchanged.
- Full test suite green; `--no-pdf` works without WeasyPrint installed.
