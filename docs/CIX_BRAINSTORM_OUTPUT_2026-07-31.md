# CIX Brainstorm Output — 2026-07-31

**Purpose:** decisions record from the design brainstorm; the direct input to the PRD.
**Input:** `CIX_BRAINSTORM_BRIEF_2026-07-31.md` (agenda §6 worked in full, in order).
**Owner:** KP · **Session:** KP + Claude, 2026-07-31.
**Status of everything here:** ratified in-session by KP unless marked *open*.

---

## 0 · Headline rulings — what changed today

1. **The rubric is unblocked.** The swap catalogue is upstream of the *priced view only*, not of detection. Detection runs on a stand-in catalogue immediately; the Tracey session becomes an enrichment pass, not a prerequisite.
2. **Validation is no longer the weakest part.** A six-tier, ground-truth-free validation architecture replaces the planted-synthetic straw man (which survives, demoted to instrument calibration). See §5.
3. **Best-chance first corpus named:** Canadian financial-services customer-service call transcripts (transcripts exist; old test data; informal; cleared for test use). First real run will therefore be the *service* rubric — resolved against the sales-first lock by splitting author order from run order.
4. **The unproven corpus claim gets a self-test.** Every run measures whether whole-corpus analysis beat a 10% sample. The value proposition becomes a number the pipeline emits (§8, abandon trigger 2).

## 1 · Swap catalogue

| Decision | Detail |
|---|---|
| Upstream of priced view only | Findings without remedies print. Rubric `detection`/`unit_of_count` need no substitute; `swap_ref`/`effort`/`outcome` join later — even post-run. |
| Two-pass structure | Pass A: bottom-up detection (hunt, count, rank). Pass B: remedy join from catalogue. |
| Stand-in catalogue v0.1 | Pencilled effort/outcome, every entry marked inferred. Tracey catalogue swap-in is a roadmap item that doubles as the **catalogue-swap proof** (sibling of the second-rubric proof). |
| Granularity: two-sided test | A labour unit is the **largest** chunk of work that (a) leaves a distinguishable signal in the record and (b) is replaced whole by a single substitute. Split when a substitute covers part; merge when the record can't distinguish. |
| Tracey taxonomy = crosswalk, not structure | Nullable `lifecycle_ref` field (pillar→process→subprocess→task coordinates). Her session does two jobs: harvest new entries, stamp `lifecycle_ref` on existing ones. Unit disagreements are recorded, not resolved in her favour. Quarantines the A21J-07 no-outsourcing-lens gap. |
| Effort/outcome = bands, split provenance | Outcome = corpus-measured count × catalogue per-unit value **band**. Effort = catalogue implementation **band** (config-change / integration / behaviour-change / capital). |
| **Leverage = grid** (KP ruling on the §4 lock) | Effort-band × outcome-band grid; corpus count breaks ties within a tier; Class D falls in the high-effort/low-outcome corner. Scalar product rejected as fake precision at this stage. |
| Vertical handling | `vertical` tag per entry; small cross-industry core marked as such. Convergence = *open question*, trigger: revisit after two real catalogues exist. |
| Evidence tier is buyer-facing | Remedies print as *confirmed in practice* vs *candidate substitute*. Honesty buys credibility. |
| Field split consequence | `remedy_class`, `effort`, `outcome` live in the **catalogue**, not duplicated into rubric items; joined via `swap_ref`. |
| Drift triangulation (KP) | Run remedy-matching over distilled findings AND independently over raw snippets; diff. Raw-side remedies with no finding = detection miss; findings with no raw corroboration = aggregation artifact. Adopted as a validation fixture (§5). |

## 2 · Rubric design

| Decision | Detail |
|---|---|
| Rubric v1 = generic sales/outbound | Drafted from RO-1–RO-5 + catalogue seeds. **Corpus-arrival adaptation pass is a named PRD step** — v1 does not pretend to fit corpus-blind. |
| `detection` structure | `prefilter` (optional; deterministic predicates over the index tag vocabulary) + `criterion` (plain-language LLM judgment) + `exemplars` (few-shot anchors). |
| Escape audits on every prefilter | Classify runs filtered candidates **plus** a seeded random sample of excluded snippets; hits in the excluded sample estimate miss rate; above-threshold auto-flags the filter for widening. Recall loss is measured, never silent. |
| `unit_of_count` = closed enum | `occurrence` / `interaction` / `account` / `time-estimate` / `chain`, defined once in the label schema; each item declares exactly one. **Dedup is the item's declaration, not the model's judgment.** Counts never sum across units. |
| `chain` = deterministic links only | Same thread / same account-ID metadata via the index. Never LLM-inferred "sounds like the same issue." |
| Hot-swap mechanics (3) | (a) Schema-validated plain-language config, loaded at run start, no rubric text in code. (b) **Rubric may only reference tags from the published tag vocabulary** — the real index↔rubric contract; a new tag = index version bump, not code. (c) Acceptance test: loading the service rubric touches zero code. |
| Author order vs run order | Sales rubric authored first (lock satisfied, generic). Service rubric authored second, **shaped to the FS corpus**; its run = first real-data run *and* the swappability proof. Recorded as the lock-compatible resolution. |
| FS corpus consequences | CX-1–CX-4 are the service-rubric spine (failure-demand evidence strongest in FS); contact-centre catalogue seeds become the thickest stand-in region; transcripts exist so the audio carve-out is untouched. |

## 3 · Rubric vs. label schema — the boundary

Four versioned artifacts, distinct change cadences:

| Artifact | Nature | Cadence |
|---|---|---|
| Index tag vocabulary | Deterministic, published contract | Slowest — version bump is an event |
| Label schema | LLM judgment, descriptive ("what happened") | Slow — per domain/vertical |
| Rubric | LLM judgment, target-defining ("what we hunt") | Fast — per engagement/run |
| Swap catalogue | Human knowledge, remedy | Independent — Tracey/engagement-driven |

- **Both swap, at different speeds.** A rubric declares the schema + tag-vocabulary versions it was written against; the loader refuses unmet dependencies.
- **Classify = two sub-passes.** Pass one: schema labels, rubric-independent. Pass two: rubric hits, consuming labels + snippet text. **A rubric swap re-runs only pass two** — this is what makes hot-swap operationally cheap and the swappability proof an incremental pass, not a reprocess.
- **Schema-SPOF bounded, not eliminated:** (a) the schema mediates *aggregation dimensions, not evidence* — hits cite snippet text, quotes string-match source, so label error distorts where counts land, never what evidence says; (b) per-run **label self-agreement audit** (seeded sample re-judged blind); unstable fields marked in the run log and flagged in the report wherever a finding leans on them.
- **Core-only schema for v1** (motion, intent, driver-origin, automatability, outcome, handoffs — the MVP contract). Domain extensions rejected for v1: one schema + two rubrics is the purest form of the swappability claim. Extensions return as a versioned capability later.

## 4 · Index stage

- **Snippet = smallest natural discourse unit per source type** (transcript→speaker turn; email→paragraph-in-message; note→paragraph), positional content-stable IDs `{interaction_id}:{seq}`, **span addressing** (claims cite contiguous ID ranges — signals cross turns). Chunking rules are part of the index version.
- **Tag vocabulary, four families:** structural (source type, speaker role from metadata only, position, length, timestamps) · lexical (versioned regex/keyword families: repeat markers, transfer/hold language, negation, currency/date presence — the prefilter workhorses) · metadata joins (account ID, thread ID, date, duration — the only legal `chain` basis) · computed (length, speaker balance, gaps). **Bright line: nothing in the vocabulary requires judgment; judgment belongs to the label schema.**
- **Store = one SQLite file per run.** Snippets, tags, labels, hits, rollups, drop log. Portable (satisfies customer-owns-the-intelligence), queryable both directions (ID→text+offset for provenance; predicates→snippet sets for pre-selection). Content hash per snippet row is what the evidence gate string-matches.
- **"Same answer twice," structurally:** (1) deterministic index build — same corpus + version → byte-identical store, property-tested; (2) every sample is seeded, seeds in the run manifest; (3) **classification is a persisted artifact, not a live call** — labels/hits written once per (corpus, schema, rubric, model) tuple; all downstream questions read the store. LLM nondeterminism survives only in synthesis prose; quantities, citations, rankings are pinned. Run manifest: corpus hash, four artifact versions, model+version, prompt hashes, seeds.
- **Drop log** (resolves the recall-vs-silent-drop lock interaction): evidence-gate failures are dropped from the report per the lock, but every drop writes a row — what died, which check, what it claimed. Drop *rate* above threshold = run-health signal.

## 5 · Validation without ground truth

**Failure taxonomy the evidence gate cannot catch:** (1) biased classification · (2) genre hallucination (model finds what the literature says should be there — maximal risk on an FS service corpus) · (3) mechanism error (right count, wrong causal story) · (4) artifact findings (noise read as pattern) · (5) false completeness (complete over the rubric, silent beyond it).

**Straw-man verdict: right tool, wrong job.** Planted-synthetic survives as **instrument calibration** (known weights on a new scale), with three repairs: **null controls** (corpora with zero of pathology X — direct measurement of genre hallucination); **collusion-broken plants** (plant author works from pathology descriptions, never rubric text; vocabulary disjointness enforced; partial/ambiguous/camouflaged cases included); **loudness curves** (detection rate vs plant loudness → sensitivity floor, not pass/fail).

**The architecture (all ratified):**

| Tier | Mechanism | Catches | When |
|---|---|---|---|
| Calibration | Planted synthetic + null controls + collusion-broken plants + loudness curves | Gross mechanics; hallucination baseline; sensitivity floor | Pre-deployment |
| Differential | **Delta injection into real corpora** (remove/duplicate/splice known quantities; reading must track the delta) | Magnitude miscalibration on real text — ground truth of *changes*, not levels | Per corpus type |
| Stability | Split-half (labels exist; aggregation is cheap) · paraphrase invariance on sampled criteria | Artifact findings; judgment brittleness | Every run |
| Self-consistency | Drift triangulation (§1) · escape audits · label self-agreement · drop-rate monitoring | Filter blindness; label noise; silent recall loss | Every run |
| Adjudication | **Second frontier model, different lab, in the audit seat** (KP ruling: consistent with the frontier-throughout lock) · competing-mechanism discharge | Correlated shared-prior bias; narrative overreach | Every run, sampled |
| Honesty | Coverage accounting + saturation curve | False completeness | Every run, headlined |

**Competing-mechanism discharge:** synthesis is forbidden single-narrative causal claims — each finding states the top alternative mechanism and the evidence that would discriminate; the pipeline checks the store for it. Found → mechanism stands, cited. Not found → finding ships marked *undischarged*. Plausibility is no longer sufficient to print.

**The completeness claim, restated permanently:** not *"these are all the drivers"* but *"the rubric accounts for X% of volume; the residual is characterized into these clusters; discovery saturated / did not saturate."* Residual size is a headline number.

## 6 · Output

One document, six sections, in attention order: **1 Highlights** (each finding: count, share, grid position, remedy + evidence tier — *confirmed / candidate / none yet* — mechanism status) · **2 What's working** (placed early; proves the instrument isn't a deficiency-hunter) · **3 Leverage grid** (Class D visibly parked, with names — "what to ignore" is deliverable) · **4 Priced plays** (grouped by `unit_of_count`, never cross-summed) · **5 Full distribution + coverage block** (every tally; coverage %, residual clusters, saturation curve) · **6 Open flags + method page** (one page: manifest summary, audit stats, drop counts — built to survive a skeptical ops director).

**Format (KP ruling): PDF primary, self-contained HTML evidence companion** — citations expand inline to verbatim snippets with context; falsifiability-by-click. Not a dashboard: a versioned, dated **run artifact**, diffable — the "did it stick" re-measure is a diff of two reports, mechanical via the run manifest.

## 7 · Corpus + PII

- **Synthetic corpus is permanent validation infrastructure** (calibration + null controls), not a fallback. Built regardless; FS corpus pursued in parallel. Nothing waits.
- **Non-circularity:** generator and detector must not share a mind — second-lab model as generator; generation from pathology descriptions, never rubric text; vocabulary disjointness; **CFPB complaint narratives as realism donor** (public, PII-scrubbed, real FS service-failure language — kills "synthetic is easier than real" cheaply).
- **PII boundary rule: nothing unscrubbed ever persists.** Scrub at ingest before the index writes a byte: deterministic patterns (accounts, cards, national IDs, phones, emails) + NER for names/addresses + sampled human audit per corpus. **Identifiers are salted-hash pseudonymized, not deleted** — `chain` linkage survives, identity doesn't. Zero-retention API terms.
- **Jurisdiction (KP ruling): PIPEDA sets the MVP floor** (firm and we are Canada-domiciled). Other jurisdictions: tracked matrix on the roadmap, not delivered against in MVP. The FS data is old test data, informally cleared, no live hazard — **the scrub stage ships anyway, as a capability demonstration**: the architecture behaves as if the data were live PII.

## 8 · Scale, sequencing, and the abandon trigger

- **1K/100K breaks are economic, not architectural.** 1K: linear frontier spend, nothing structural. 100K: spend dominates (that *is* the v1.5 model-routing carve-out — the two-sub-pass split is already routing-shaped: the volume label pass cheapens, the audit seats stay frontier); batch API for wall-clock; embedding-based residual clustering. **Validation cost is O(1) by construction** — every audit is fixed-size sampled; corpus cost is linear, validation cost is flat.
- **Smallest first slice — the spine, no LLM first:** index + store + evidence gate on synthetic transcripts, proven byte-reproducible. Then: core-schema label pass → 3–5-item mini-rubric from strongest seeds → aggregate → synthesize → report, tens of interactions, with null control + split-half wired into run one. Every contract exercised end-to-end. Then, one artifact at a time against a proven spine: generic sales rubric v1 → FS service rubric → real-corpus run → Tracey catalogue swap.
- **Abandon triggers, aimed at the only unproven claim (completeness/frequency/rank):**
  1. **Calibration failure** — after fair iteration, planted magnitudes unrecoverable within tolerance, or null controls keep hallucinating at frontier tier. Capability falsified; stop.
  2. **The sample self-test** (in v1; cheap — subsample aggregation reuses labels): diff a random-10%-sample run against the whole-corpus run. Distribution + rank + highlights reproduced from the sample → whole-corpus added nothing; **the corpus claim dies by its own instrument's measurement.** Claim survives only where the diff shows what the thesis predicts: rare drivers invisible at 10%, tail-rank instability, counts a sample can't price. The diff is published internally every run — it is the value proposition, measured.
  3. **The decision test** — on the first real corpus: findings ≈ a sharp operator's hour-of-priors list *and* counts change no decision → the instrument informed nobody. Earned only by an actual run.

## 9 · Locked-list interactions — flagged and ruled, not reopened

| §4 lock | Interaction | KP ruling |
|---|---|---|
| Recall beats precision + drop-don't-flag | Silent recall loss at the evidence gate | Drop log in the store; report clean, bodies countable |
| Effort × outcome ranking | Banded values make scalar product fake | **Grid + count tie-break satisfies the lock** |
| Sales rubric first | Best-chance corpus is service-side | **Author order ≠ run order**; sales authored first, service runs first |
| Frontier model throughout | Shared-prior bias needs a second opinion | **Second frontier lab admitted to the audit seat** |

## 10 · Open questions carried into the PRD

| # | Question | Trigger/owner |
|---|---|---|
| 1 | Vertical catalogue convergence | Revisit after two real catalogues |
| 2 | Per-unit value band sources pre-Tracey (who pencils, from what) | KP + Opportunity Library formulas; Tracey session corrects |
| 3 | Tracey session scheduling + extraction protocol (two jobs: harvest + crosswalk-stamp) | KP |
| 4 | FS corpus confirmation: volume, date range, transcript format, test-data provenance note | KP |
| 5 | Second-lab audit model selection (Western-origin guardrail applies) | Plan stage |
| 6 | Thresholds: escape-audit miss rate, self-agreement floor, drop-rate alarm, sample self-test tolerance | Plan stage — set provisional, tune on calibration corpus |
| 7 | Scrub-audit sample size + protocol per corpus | Plan stage |
| 8 | Menu ratification and the findings→menu join used by drift triangulation | Mario/KP, external to this build |
| 9 | Jurisdiction matrix beyond PIPEDA | Tracked, post-MVP |

## 11 · Artifacts the PRD should mandate

1. Index tag vocabulary v1 (published contract, versioned)
2. Core label schema v1 (plain-language, versioned)
3. Stand-in swap catalogue v0.1 (seeds + pencilled bands, all marked inferred, `lifecycle_ref` empty)
4. Sales/outbound rubric v1 (generic, from RO-1–5; declares schema + vocab deps)
5. FS service rubric v1 (corpus-shaped; the swappability proof)
6. Calibration corpus spec (plants + null controls + loudness design; CFPB realism donor; second-lab generator)
7. Run manifest schema
8. Report template (six sections; PDF + HTML companion)

## Changelog

- **2026-07-31** — Created as the output record of the KP+Claude design brainstorm (brief agenda §6 worked in full). All rulings ratified in-session by KP. Development repo established at `Projects_gh/CIX`; planning docs remain in Claude COWORK. — Claude
