# CIX Brainstorm Output — 2026-07-31 · rev 2.2

**Purpose:** the governing design record from the 7/31 brainstorm, revised against the two pre-PRD review passes. The direct input to the PRD.
**Inputs:** `CIX_BRAINSTORM_BRIEF_2026-07-31.md` (agenda §6 worked in full) · `CIX_PRD_Input_Pack_2026-07-31.md` (precedence rules, gaps, acceptance criteria) · Codex PRD-handoff redraft (2026-07-31).
**Owner:** KP · **Sessions:** KP + Claude (brainstorm, 7/31); KP + Claude (revision, 7/31).
**Status:** everything here is ratified by KP unless marked *open*. This is not the PRD; the PRD adds owners, thresholds, dates, and scope triage — it does not silently change a ruling.
**Baseline note:** `CIX_POC_B_Sniffer_Scope_v2.md` survives as the baseline spec *except* where this doc rules otherwise — rubric item structure, output section order (§9 here supersedes scope v2 §4), and validation design. This doc is a rulings record, not a restatement of everything the baseline already says.

---

## 0 · Product frame

**0.1 Thesis.** CIX turns a complete corpus of customer interactions into an auditable, reproducible decision artifact: (1) detect and count operational patterns; (2) preserve source evidence for every finding; (3) characterize what the active rubric did *not* explain; (4) join supported findings to practical remedies; (5) rank remedies with honest value and effort bands; (6) measure whether whole-corpus analysis added anything over a sample. The unproven claim is not that a frontier model can summarize text — it is that whole-corpus analysis finds decision-relevant frequency, rank, and tail patterns that a sharp operator reviewing a sample would miss. **Every run tests that claim.**

**0.2 Primary user and success condition.** The primary user is an operations leader deciding what to improve, automate, redesign, or ignore. The analyst/engagement team configures and audits the run; a domain expert improves the remedy catalogue **without controlling what the detector is allowed to find**. The product succeeds when its evidence and quantified distribution change a decision, materially change a priority, or materially strengthen or weaken confidence in one.

**0.3 MVP proof chain.** One continuous story: deterministic spine (every claim resolves to source) → separation of concerns (label once; hot-swap rubrics and catalogues without code changes) → validation (measured behavior on plants, nulls, deltas, splits, escape samples, second-model adjudication, residuals) → real-corpus usefulness (service rubric on the FS corpus) → whole-corpus value (full-vs-10% comparison under predeclared tests) → decision consequence (record what changed for the sponsor).

**0.4 v1 non-goals.** Not a dashboard or continuous-monitoring product · not audio transcription · not an autonomous decision-maker · not a causal-inference engine · not a compliance certification · not a promise of complete discovery beyond the rubric · not a scalar ROI calculator on uncertain bands · not a multi-vertical schema framework · not the 100K cost-optimized architecture.

## 1 · Headline rulings

1. **The rubric is unblocked.** The swap catalogue is upstream of the *priced view only*, not detection. Detection runs immediately on a stand-in catalogue; the Tracey session is an enrichment pass that doubles as the catalogue-swap proof, not a prerequisite.
2. **Validation is a product surface, not backstage QA.** A six-tier, ground-truth-free architecture replaces the planted-synthetic straw man, which survives demoted to one tier (instrument calibration).
3. **Best-chance first corpus named:** Canadian financial-services customer-service transcripts — existing, old test data, informally cleared for test use (see §10 authorization ruling). First real run is therefore the *service* rubric.
4. **Author order ≠ run order.** Sales rubric authored first (satisfies the lock); corpus-shaped service rubric authored second and runs first.
5. **The corpus claim gets a self-test.** Every run compares whole-corpus results with a seeded 10% sample under predeclared tests; part of the internal run artifact, recorded even when unfavorable.
6. **The output is a versioned decision artifact** — PDF primary, self-contained HTML evidence companion. Not a dashboard.
7. **Honesty is buyer-facing.** Coverage, residuals, evidence tiers, mechanism status, unstable fields, and material audit failures are visible in the deliverable.

## 2 · Architecture — two passes, four artifacts, one contract

**2.1 Two analytical passes.**
**Pass A — detect and quantify:** ingest scrubbed records → deterministic index → rubric-independent label schema → selected rubric → dedup by declared unit → aggregate, rank, characterize residuals.
**Pass B — join remedies and price:** join findings to the swap catalogue → outcome bands from corpus count × *unit-compatible* per-unit value band → place on the leverage grid → drift triangulation (remedy-match distilled findings vs raw snippets, diff).
**A finding may publish with no remedy. Remedy availability must never suppress detection.**

**2.2 Four versioned artifacts, distinct cadences.**

| Artifact | Responsibility | Cadence |
|---|---|---|
| Index tag vocabulary | Deterministic, published filter/join contract | Slowest — a new tag is a version bump |
| Label schema | Rubric-independent descriptive judgment: *what happened* | Slow — v1 is one core schema |
| Rubric | Target-defining judgment: *what this run hunts, how it counts* | Fast — per engagement/run |
| Swap catalogue | Human remedy knowledge: substitutes, bands, evidence, crosswalks | Independent — expert/engagement-driven |

A rubric declares the schema and tag-vocabulary versions it requires; **the loader refuses unmet dependencies before any model work starts.**

**2.3 What hot-swap means (the contract).** Rubric text lives in schema-validated plain-language config, never pipeline code · a rubric references only published index tags · label pass and rubric pass are persisted separately · a rubric change re-runs only the rubric pass (given compatible deps) · **a catalogue change regenerates the remedy/priced view without re-running detection** · acceptance proof: the service rubric runs with zero code changes and reuses compatible persisted core labels.

## 3 · Swap catalogue

| Decision | Detail |
|---|---|
| Upstream of priced view only | `detection`/`unit_of_count` need no substitute; `swap_ref`/`effort`/`outcome`/remedy evidence join later, even post-run. |
| Stand-in catalogue v0.1 | Pencilled effort/outcome bands; every unverified entry marked inferred with its source recorded. |
| Tracey session = two jobs | Harvest new entries; stamp nullable `lifecycle_ref` crosswalks onto existing ones. Her taxonomy is a crosswalk, never the governing structure; unit disagreements are recorded, not auto-resolved in her favour. Quarantines the A21J-07 no-outsourcing-lens gap. |
| Granularity: two-sided test | A labour unit is the **largest** chunk of work that (a) leaves a distinguishable signal in the record and (b) is replaced whole by one substitute. Split when a substitute covers part; merge when the record can't distinguish. |
| Outcome | Corpus-measured count × catalogue per-unit value **band**. **The catalogue unit must be compatible with the rubric item's `unit_of_count`; incompatible joins fail validation** rather than pricing nonsense. |
| Effort | Catalogue implementation band: config-change / integration / behaviour-change / capital. |
| **Leverage = grid** (lock ruling) | Effort-band × outcome-band grid; corpus count breaks ties within a tier; Class D visibly high-effort/low-outcome. Scalar product rejected as fake precision. |
| **Remedy-less findings: the shelf** | Findings with no catalogue join have no grid coordinates. They print on a **"no known remedy yet" shelf adjacent to the grid**, ranked by count within unit — the honest visual for what the Tracey enrichment pass will later move onto the grid. |
| Evidence tier is buyer-facing | Remedies print as *confirmed in practice* / *candidate substitute* / **none yet**. |
| Vertical handling | `vertical` tag per entry; small cross-industry core marked. Convergence *open* until two real catalogues exist. |
| Field split | `remedy_class`/`effort`/`outcome` live in the **catalogue**, joined via `swap_ref` — never duplicated into rubric items. |
| Drift triangulation | Remedy-match distilled findings AND raw snippets independently; diff. Unmatched raw-side remedy = detection-miss *signal*; uncorroborated finding = aggregation-artifact *signal*. **Neither is a verdict without adjudication.** |

## 4 · Rubric design

| Decision | Detail |
|---|---|
| Item fields | `id` · `description` · **`polarity`** · `detection` · `unit_of_count` · `swap_ref` (nullable) · declared schema + tag-vocab versions. **Polarity carried unchanged — one mechanism, two polarities:** "what's working" is positive-polarity items through the same machinery, never a separate subsystem. |
| First authored | Generic sales/outbound v1 from RO-1–RO-5 + catalogue seeds. **Corpus-arrival adaptation pass is a named build step** — v1 doesn't pretend to fit corpus-blind. |
| First run | FS service rubric, shaped to the candidate corpus; CX-1–CX-4 spine (failure-demand evidence strongest in FS); contact-centre seeds are the thickest stand-in region. |
| `detection` structure | Optional deterministic `prefilter` over published tags + plain-language `criterion` + few-shot `exemplars`. |
| Escape audit on every prefilter | Classify filtered candidates **plus** a seeded random sample of excluded snippets; excluded-sample hits estimate miss rate; threshold breach flags/blocks the filter per the PRD gate. Recall loss is measured, never silent. |
| `unit_of_count` closed enum | `occurrence` / `interaction` / `account` / `time-estimate` / `chain`; each item declares exactly one. **Dedup is deterministic declaration, not model judgment.** |
| `chain` | Deterministic same-thread/same-account metadata links only. Never LLM-inferred relatedness. |
| Dependencies | Rubric references only the published tag vocabulary; declares required schema + vocabulary versions. |
| Denominators | Counts from different units never sum; **every share names its denominator beside it** (see §7.5). Priced plays group by unit. |

## 5 · Label schema boundary

- **Classify = two persisted sub-passes.** Pass one: schema labels, rubric-independent. Pass two: rubric hits from labels + snippet text. A rubric swap re-runs only pass two.
- **Core-only schema for v1:** motion, intent, driver-origin, automatability, outcome, handoffs. Domain extensions rejected for v1 — one schema + two rubrics is the purest swappability proof.
- **SPOF bounded, not eliminated:** labels shape aggregation dimensions; published hits still cite snippet text, and quotes string-match the store. Label error moves counts, never evidence.
- **Label self-agreement audit every run:** seeded sample re-judged blind; unstable fields recorded in the run log and flagged in the report wherever a finding leans on them.
- **Evidence and labels stay distinct:** a correct quote doesn't prove a correct label; a label audit doesn't prove a mechanism.

## 6 · Index, store, reproducibility

**6.1 Snippets.** Smallest natural discourse unit per source type (transcript→speaker turn; email→paragraph-in-message; note→paragraph); positional content-stable IDs `{interaction_id}:{seq}`; **span addressing** — claims cite contiguous ID ranges. Chunking rules are part of the index version.

**6.2 Tag vocabulary — four families.** Structural (source type, metadata-derived speaker role, position, length, timestamps) · lexical (versioned deterministic patterns: repeat markers, transfer/hold language, negation, currency/date presence) · metadata joins (account ID, thread ID, date, duration — the only legal `chain` basis) · computed (length, speaker balance, gaps). **Bright line: nothing in the vocabulary requires judgment.**

**6.3 Run store.** One SQLite file per run: scrubbed snippets, tags, labels, hits, rollups, validation results, drop log. Queryable in all directions: ID→scrubbed text+context+offset · predicates→candidates · finding→hits→evidence · manifest→exact configuration. The run package is portable and customer-owned — **and still contains sensitive scrubbed content: access, encryption, retention, deletion remain required controls.**

**6.4 Reproducibility — three separate meanings** (rev 2 ruling):

1. **Index determinism:** same canonical scrubbed corpus + same index version → identical *logical content*: snippets, IDs, hashes, tags. **The normative property test is logical-content equality** — a canonical hash over that logical content, required to match across environments. Byte-identical SQLite output is *not promised* (bytes vary with timestamps, library versions, page settings, insertion order); it may run as a non-normative check in a pinned CI environment.
2. **Sample reproducibility:** every sample is seeded; seeds live in the run manifest.
3. **Analytical stability:** classification is written once as two separately-keyed immutable artifacts — **schema labels keyed by (corpus, index version, schema, model, prompts), rubric hits keyed by (label artifact, rubric, model, prompts)** — so labels are reusable across rubric swaps by construction. Downstream questions read the artifacts, never silently make new calls. Persistence *contains* model nondeterminism — it does not prove a fresh re-run would judge identically. That residual risk is what the stability and self-agreement audits measure.

**6.5 Manifest and drop log.** Manifest: canonical scrubbed-corpus hash, four artifact versions, model/provider version, prompt hashes, thresholds, seeds, privacy-gate status, corpus-clearance record (§10). Drop log: evidence-gate failures never publish, but every drop writes a row — what died, which check, what it claimed. Drop rate above threshold is a visible run-health signal. (This resolves the recall-vs-silent-drop lock interaction.)

## 7 · Validation without full ground truth

**7.1 Failure taxonomy the evidence gate cannot catch:** (1) biased classification · (2) genre hallucination (FS service is the worst case — the literature's priors are strong) · (3) right count, wrong mechanism · (4) noise promoted to pattern · (5) false completeness beyond the rubric · (6) plausible but decision-irrelevant results. No single tier proves truth; the architecture creates *independent failure signals* and makes unresolved uncertainty visible.

**7.2 Six tiers, all ratified.**

| Tier | Mechanism | Catches | Cadence |
|---|---|---|---|
| Calibration | Planted synthetic + null controls + collusion-broken plants + loudness curves | Gross mechanics; hallucination baseline; sensitivity floor | Pre-deployment + after material detector changes |
| Differential | Delta injection into representative real text (remove/duplicate/splice known quantities; readings must track) | Magnitude miscalibration on real language | Per corpus type |
| Stability | Split-half; paraphrase invariance on sampled criteria | Artifact findings; judgment brittleness | Every run |
| Self-consistency | Drift triangulation; escape audits; label self-agreement; drop-rate monitoring | Filter blindness; label noise; silent recall loss | Every run |
| Adjudication | **Second frontier model, different lab, sampled audit seat**; competing-mechanism discharge | Shared-prior bias; narrative overreach | Every run |
| Honesty | Coverage accounting; residual characterization; saturation curve | False completeness | Every run, headlined |

**7.3 Calibration details.** Null corpora contain zero of pathology X and directly measure genre hallucination · plant author works from pathology descriptions, never rubric text · **detector and generator come from different labs/families, and the audit seat never adjudicates corpora its sibling generated** (F4) · vocabulary disjointness enforced · plants include partial, ambiguous, camouflaged, varying-loudness cases · detection-by-loudness yields a sensitivity curve, not pass/fail. CFPB complaint narratives are the service-side realism donor (public data; confirm reuse terms as routine hygiene); **a sales-side realism donor is an open item** — the sales rubric is authored and calibrated first.

**7.4 Mechanism discipline.** Synthesis may not print an unqualified single-narrative causal claim. Each finding states: proposed mechanism · strongest plausible alternative · the evidence that would discriminate · whether it was found. Absent → ships marked **undischarged**. Plausibility is not sufficient to print.

**7.5 Coverage and residuals** (rev 2 ruling — denominator scheme ratified):

- **Interaction coverage** — share of *eligible interactions* with ≥1 rubric hit — is the default headline coverage number.
- Per-unit coverage is reported **only** where that unit's eligible universe is defined (e.g., eligible accounts).
- Within-unit shares (a finding's count ÷ all detected counts in the same unit) are reported as **distribution**, never called coverage.
- For `occurrence`/`time-estimate`/`chain`, no coverage claim unless an eligible denominator has been independently defined.
- **Default residual = eligible interactions with no rubric hit.** Any other residual names its unit and denominator.
- **v1 residual characterization = frontier-LLM grouping** over unmatched snippets into named clusters — consistent with the frontier-throughout lock, audited like any judgment (seeded sample, second-model check). Embedding-based clustering stays at the v1.5 carve-out.
- Saturation is reported for the declared discovery method and sampling order.

**The permanent claim:** *"At the stated denominator, the rubric accounts for X%; the residual has these observed clusters; discovery saturated / did not saturate under the declared method."* Never "these are all the drivers."

## 8 · Whole-corpus value self-test

Every run: seeded 10% interaction sample from persisted classification, compared with the full corpus. **The PRD predeclares:** sampling frame and stratification · distribution-distance metrics per compatible unit · rank comparison and top-k overlap · highlight-selection comparison · rare-driver definition · what counts as a materially different count or value band · equivalence tolerances · multi-seed handling if one draw is unstable.

The claim survives where the whole corpus adds a decision-relevant result: a rare driver absent from the sample · material tail-rank instability · a materially different count or price band · a different highlighted action. If the sample reproduces all decision-relevant outputs within tolerance, whole-corpus analysis added no demonstrated value for that run — **recorded even when unfavorable.** This diff is the value proposition, measured.

## 9 · Output

One decision artifact, six sections, attention order: **1 Highlights** (count, share *with denominator*, grid position or shelf, remedy + evidence tier, mechanism status, evidence link) · **2 What's working** (early; proves it isn't a deficiency-only detector) · **3 Leverage grid** (+ the no-remedy-yet shelf; Class D named — "what to ignore" is deliverable) · **4 Priced plays** (grouped by unit, never cross-summed) · **5 Full distribution + coverage** (all tallies; interaction coverage; per-unit coverage where defined; residual clusters; saturation; full-vs-10% result) · **6 Open flags + method page** (manifest summary, audit statistics, unstable fields, threshold failures, drop counts).

**Format:** PDF primary; self-contained HTML evidence companion where citations expand inline to **faithful scrubbed excerpts with context** (string-matched against the scrubbed store — not represented as untouched raw source). Both render from the same persisted run and name the same manifest. The HTML inherits the run package's access/retention controls. Not a dashboard: a versioned, dated, diffable **run artifact** — the "did it stick" re-measure is a mechanical diff of compatible runs; run-to-run compatibility across artifact-version changes is a PRD item.

## 10 · Corpus, privacy, authorization

- **Synthetic is permanent validation infrastructure**, built regardless; the FS corpus is pursued in parallel. Nothing waits.
- **Non-circularity:** second-lab generator · generation from pathology descriptions, never rubric text · vocabulary disjointness · realism donors per §7.3.
- **Authorization ruling (rev 2): informal clearance stands for this corpus.** The FS data is old test data, informally cleared by its owner, assessed no-hazard. The clearance (source, context, date) is recorded in the run manifest; **Codex's written-authorization gate is explicitly rejected for MVP** as friction the situation doesn't warrant. Our own side is still verified: provider terms, regions, zero-retention, training-use settings checked before external calls. Formal authorization machinery becomes relevant at the first *engagement* corpus, not this test.
- **PII boundary rule: nothing unscrubbed ever persists** — not store, logs, traces, or caches. Scrub transiently at ingest: deterministic patterns (accounts, cards, national IDs, phones, emails) + NER (names, addresses) + sampled human scrub audit per corpus under a predeclared protocol. **Linkage identifiers salted-hash pseudonymized, not deleted** — `chain` survives, identity doesn't.
- **PIPEDA is the Canadian MVP design baseline**, subject to qualified privacy/legal review; the architecture is a posture, not a compliance certification. Other jurisdictions: tracked matrix, post-MVP.
- **The scrub stage ships even for cleared test data** — privacy-preserving ingest is itself part of the capability proof.
- **Hostile-input principle (design-stage, rev 2.2):** corpus text, labels, and excerpts are always data, never instruction — the pipeline delimits them from system/task prompts, and evidence rendering escapes corpus-supplied markup. Adversarial fixtures (prompt-injection, payload-bearing excerpts) are required **before the first uncontrolled corpus**; in the controlled MVP environment they are a noted deferral, not a build item.

## 11 · Scale and delivery sequence

**11.1 Scale.** 1K/100K breaks are economic, not architectural: ~1K accepts linear frontier spend; ~100K drives the v1.5 routing/batching architecture, for which the two-sub-pass split is already shaped (volume label pass cheapens; audit seats stay frontier). **"Validation is O(1)" applies to model-call cost of fixed-size sampled audits** — bookkeeping and full-corpus aggregation still scale with corpus size.

**11.2 Delivery sequence.**
1. **Contract first:** input format, reproducibility definition (§6.4), validation thresholds, self-test metrics, cost/iteration budget — the threshold register, set before results are seen.
2. **Deterministic spine:** index + store + evidence gate + manifest + drop log on synthetic transcripts, no model dependency, logical-equality property test passing.
3. **Thin end-to-end slice:** core labels → 3–5-item mini-rubric → aggregate → synthesize → report at tens of interactions, null control + split-half wired into run one.
4. **Full sales rubric** authored (generic v1).
5. **Calibration:** plants, nulls, loudness curves, deltas, predeclared gates.
6. **Service rubric** authored; hot-swap proven with zero code changes.
7. **First real run:** service rubric on the FS corpus, including the full-vs-10% self-test.
8. **Catalogue-swap proof:** Tracey-enriched catalogue replaces the stand-in; remedy/priced view regenerates **without re-running detection**.

## 12 · Abandon triggers and release gates

**Abandon triggers — aimed at the unproven claim, pre-registered:**
1. **Calibration failure.** After the pre-agreed iteration budget, planted magnitudes stay outside tolerance or null controls exceed the hallucination threshold at frontier tier. Capability falsified; stop.
2. **Whole-corpus value failure.** The predeclared 10% comparison reproduces the full corpus's decision-relevant distribution, rank, highlights, and value conclusions within tolerance. The claim dies by its own instrument's measurement.
3. **Decision failure.** The first real run reproduces a pre-registered "sharp operator's hour of priors" *and* its quantified results change or strengthen no sponsor decision.

**Release gates — stop a run, not the thesis:**
4. **Privacy gate:** scrub quality, provider terms, or retention controls can't satisfy the release bar for a given corpus.
5. **Evidence-integrity gate:** claim-to-source traceability can't be met without fundamental architecture change.

**Threshold discipline:** every threshold and tolerance is set *before* the relevant results are viewed and never silently moved after. "Fair iteration" becomes a fixed budget, owner, and decision date in the PRD.

## 13 · Locked-list interactions — flagged and ruled, not reopened

| Existing lock | Interaction | Ruling |
|---|---|---|
| Recall beats precision + drop-don't-flag | Evidence gating can hide recall loss | Report stays clean; drop log keeps bodies countable; material drop-rate failures visible |
| Effort × outcome ranking | Banded inputs make scalar multiplication falsely precise | Grid + count tie-break satisfies the lock |
| Sales rubric first | Best-chance corpus is service-side | Author sales first; run service first |
| Frontier model throughout | Shared-prior bias needs another view | Second frontier lab admitted to the sampled audit seat |
| Customer owns the intelligence | The portable run artifact still holds sensitive scrubbed content | Portability plus access, encryption, retention, deletion controls |
| Same answer twice | Fresh LLM calls are not deterministic | Pin classification as a persisted artifact; test index determinism (logical equality) and judgment stability separately |

## 14 · Open decisions carried into the PRD

| # | Decision | Owner | Resolve by |
|---|---|---|---|
| 1 | FS corpus facts: volume, date range, transcript format; record informal clearance in manifest (per §10 ruling — no written gate) | KP | Before real-data ingest |
| 2 | Calibration thresholds: recovery tolerance, null-hallucination rate, loudness floor | KP + tech lead | Before calibration exit |
| 3 | Every-run thresholds: escape-audit miss, self-agreement floor, drop-rate alarm, split-half, paraphrase | KP + tech lead | Before calibration exit |
| 4 | Full-vs-10% spec: metrics, tolerances, sampling, seed count | KP + tech lead | Before first comparison |
| 5 | Primary + second-lab model selection; provider/region/retention/origin verification; F4 seat-vs-generator assignment | Tech/privacy | Before calibration exit |
| 6 | Scrub-audit protocol and sample size; run-package access/retention controls | Privacy owner | Before real-data ingest |
| 7 | Who pencils pre-Tracey per-unit value bands; which Opportunity Library formulas are admissible | KP | Before priced output |
| 8 | Tracey session scheduling + harvest/crosswalk-stamp protocol | KP | Before catalogue-swap proof |
| 9 | Menu ratification + findings→menu join consumed by drift triangulation | Mario/KP | Before service-rubric proof |
| 10 | "Sharp operator" baseline + sponsor decision log for the decision test | KP | Before first real run |
| 11 | Cost envelope + iteration budget behind "fair iteration" | KP | Before calibration begins |
| 12 | Run-to-run compatibility and diff behavior across artifact-version changes | Tech lead | Before first repeat run |
| 13 | Sales-side realism donor for the calibration corpus (CFPB is service-flavoured) | KP + tech lead | Before sales-rubric calibration |
| 14 | **R1 scope triage against the calendar** (PRD Aug 31 / demo Sept 15): which tiers/artifacts are v1-gating vs deferred — every deferral carries a named reinstatement trigger; abandon triggers are not schedule-negotiable | KP, in the PRD | PRD |
| 15 | Vertical catalogue convergence | KP | After two real catalogues |
| 16 | Jurisdiction roadmap beyond the Canadian baseline | Privacy owner | Post-MVP |

## 15 · Artifacts the PRD must mandate

1. Index tag vocabulary v1 (published contract)
2. Core label schema v1
3. Stand-in swap catalogue v0.1 (inferred-value provenance recorded)
4. Generic sales/outbound rubric v1
5. FS service rubric v1
6. Calibration corpus spec (plants, nulls, loudness design, generator separation, realism-donor rules)
7. Input-data contract (format, eligibility, manifest clearance record)
8. Privacy threat model + scrub-audit protocol
9. Run manifest schema
10. Threshold register (owner, approval date, change history)
11. Full-vs-10% comparison spec
12. Six-section report template (PDF + HTML companion)
13. Sponsor decision-log template
14. Run-to-run compatibility and diff spec

## 16 · Acceptance criteria (MVP must prove)

- Index passes the **logical-content equality** property test for same corpus + version
- Nothing unscrubbed persists — store, logs, traces, caches; privacy-gate status in the manifest
- Every published quote resolves to a snippet ID and string-matches stored scrubbed evidence via content hash
- Every quantitative claim reproduces from the rollup; every failed claim is omitted *and* written to the drop log
- Incompatible schema, vocabulary, rubric, or catalogue-unit dependencies fail before processing
- The service rubric runs with zero code changes and reuses compatible persisted core labels
- The catalogue swap regenerates the remedy/priced view without changing detection results
- All samples seeded; seeds in the manifest; escape audit, label self-agreement, null control, split-half wired into run one and producing stored results
- Mixed units never sum; every share names its denominator
- Every mechanism discharged or visibly marked undischarged
- Coverage, residual clusters, saturation, and the full-vs-10% diff appear in every run artifact
- PDF and HTML agree on counts, findings, flags, evidence, and manifest
- The sponsor records whether the first real run affected a decision

## Changelog

- **2026-07-31 — rev 2.2.** From the PRD adversarial reviews (Cowork red team + Codex): fixed the analytical-stability artifact keying (labels were keyed by a tuple including the rubric, contradicting label reuse across rubric swaps — now two separately-keyed artifacts); added the hostile-input design principle to §10 as a recorded new decision (controlled-MVP deferral of adversarial fixtures); regularized the version string (the baseline-note edit of rev 2.1 was committed without a changelog entry — recorded here). Canonical location: `Projects_gh/CIX/docs/`; the Cowork folder copy is a mirror. — Claude
- **2026-07-31 — rev 2.1.** Restored the baseline/supersession note (scope v2 survives except rubric item structure, output order, validation design) lost in the Cowork-copy overwrite. — Claude
- **2026-07-31 — rev 2.** Revised against the two pre-PRD review passes: `CIX_PRD_Input_Pack_2026-07-31.md` (Cowork) and the Codex PRD-handoff redraft. **Adopted:** product frame (§0); two-pass/hot-swap contract formalization; unit-compatibility validation on catalogue joins; "none yet" remedy tier + no-remedy-yet shelf; reproducibility split into three meanings; coverage denominator scheme; pre-registration discipline + threshold register; release gates split from abandon triggers; F4 generator/audit-seat collusion rule; O(1) claim bounded to model-call cost; scrubbed-excerpt evidence framing; merged 16-item open-decision register; merged artifact list; acceptance-criteria section; calendar (R1) triage carried to PRD. **Four KP rulings this revision:** (1) logical-content equality replaces byte-identical SQLite as the normative index test; (2) corpus authorization stays informal — Codex's written gate rejected for MVP, clearance recorded in manifest; (3) v1 residual characterization = frontier-LLM grouping, embeddings stay v1.5; (4) Codex coverage-denominator scheme ratified. No §2 (Input Pack) ratified position rolled back. — Claude
- **2026-07-31 — rev 1.** Created as the output record of the KP+Claude design brainstorm (brief agenda §6 worked in full). All rulings ratified in-session. Development repo established at `Projects_gh/CIX`. — Claude
