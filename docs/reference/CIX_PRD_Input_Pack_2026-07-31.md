# CIX — PRD Input Pack

**Purpose:** the single briefing document for the pre-PRD session. It exists to stop the design regressing to positions the 7/31 brainstorm already moved past.
**Owner:** PO · **Created:** 2026-07-31 · **Feeds:** pre-PRD re-brainstorm → PRD (5.1j-2, due Aug 31)
**Read this before anything else. It tells you which document wins when two disagree.**

---

> ⚠️ **Rev-2 addendum (2026-07-31, after this pack was written).** The brainstorm output was revised to **rev 2** (pre-PRD session: Input Pack + Codex redraft considered, four PO rulings). Rev 2 governs; where this pack conflicts with it, rev 2 wins. Specifically:
>
> 1. **§2.3's "byte-identical index build" row is superseded** — the normative index-determinism test is now **logical-content equality** (canonical hash over snippets/IDs/hashes/tags, cross-environment); byte-identity is not promised. §4's acceptance list updates the same way.
> 2. **§4's three must-decides are decided:** v1 residual characterization = frontier-LLM grouping (embeddings stay v1.5) · remedy-less findings print on a "no known remedy yet" shelf adjacent to the grid · coverage uses the interaction-coverage denominator scheme (per-unit coverage only with a defined eligible universe; within-unit shares are "distribution," never "coverage").
> 3. **Corpus authorization ruled informal for the cleared FS test data** — clearance recorded in the run manifest; a written-authorization gate was explicitly rejected for MVP.
> 4. Rev 2 also absorbs: F4 collusion rule, the sales-side realism-donor gap, the assembled acceptance criteria (rev 2 §16), release gates split from abandon triggers, and the merged 16-item open-decision register.

## 0 · How to use this pack

The CIX design has been rewritten three times. Four documents in the folder describe the product, and **the older three are wrong in specific, identifiable ways** — they were superseded by the 7/31 design brainstorm, but they still read as authoritative because nothing in them says "this bit is dead."

So the rule for this session:

> **The brainstorm output governs. Everything else is background.**
> A predecessor document may only override it where the brainstorm was working from context it didn't have — and §3 lists exactly where that is. Nowhere else.

If you find yourself proposing something that matches a predecessor doc and contradicts the brainstorm output, check §2 first. It's probably a ruling you're about to undo without knowing it.

**Reading order and precedence:**

| # | Document | Role | Precedence |
|---|---|---|---|
| 1 | `CIX_BRAINSTORM_OUTPUT_2026-07-31.md` | The ratified design | **Governs** |
| 2 | `CIX_BRAINSTORM_OUTPUT_review_2026-07-31.md` | Gaps found in review; no rulings changed | Governs on gaps |
| 3 | `CIX_POC_B_Sniffer_Scope_v2.md` | Baseline — survives *except* on rubric item structure, output section order, and validation design | Fills silence only |
| 4 | `CIX_Swap_Catalogue_v0.md` | Entry schema + the RevOps SME extraction protocol | Current |
| 5 | `CIX_Opportunity_Library_v1.md` | RO-1–5 / CX-1–4 seeds, remedy classes, evidence tiers | Reference |
| 6 | `CIX_BRAINSTORM_BRIEF_2026-07-31.md` | **§4 locked list only** — the rest is pre-brainstorm framing | Constraints only |

**Do not read** (superseded, and actively misleading): `CIX_MVP_Scope_v2.md` (pre-index-stage: detector library, ±10-pt eval bar), `CIX_MVP_Scope_v1.md`, `CIX_POC_B_Sniffer_Scope_v1.md`, `CIX_HANDOFF_2026-07-27.md`. `CIX_POC_Scope_v3.md` is POC A — a **separate track**, referenced in one line, never converged with this one.

---

## 1 · What the brainstorm was for, and why its output is load-bearing

The 7/31 session worked the brief's agenda §6 (eight items) in order, in a single sitting, with the §4 locked list held firm and every deviation flagged rather than absorbed. It produced rulings, not options — PO ratified in-session.

Three of those rulings are the reason the project moved:

1. **The rubric got unblocked.** Before: the rubric was blocked on the swap catalogue, which was blocked on a the RevOps SME session that hadn't been scheduled. The whole build sat behind one person's calendar. The session split the catalogue's role — it's upstream of the *priced view only*, not of detection — and the critical path evaporated.
2. **Validation stopped being the weak point.** The brief called validation "the weakest part of the whole design" and offered a straw man to attack. The session replaced it with a six-tier architecture that needs no ground truth, and demoted the straw man to one tier (instrument calibration).
3. **The unproven claim got an instrument.** The corpus claim — that whole-corpus analysis beats a sample on completeness, frequency, rank — was previously an assertion. It's now a number the pipeline emits every run, with a pre-registered abandon trigger attached.

None of that exists in any predecessor doc. That's the material at risk of being rolled back.

---

## 2 · Ratified — do not reopen

Each row: the current ruling, the predecessor position it replaced, and what regression costs. **The middle column is what a predecessor doc still says.** Treat any proposal matching it as a rollback.

### 2.1 · Sequencing and dependencies

| Ruling (governs) | Predecessor position (dead) | Cost of regression |
|---|---|---|
| Swap catalogue is upstream of the **priced view only**. Detection runs immediately on a stand-in catalogue v0.1; findings without remedies print. | "The rubric is blocked on this." (brief §5, scope v2 §8) | Puts the RevOps SME's calendar back on the critical path and stalls the build indefinitely. **Highest-value ruling of the session.** |
| Two-pass structure: Pass A bottom-up detection; Pass B remedy join. | Single fused detection+remedy pass. | Re-couples the two, restoring the block. |
| the RevOps SME session = **enrichment pass** that doubles as the catalogue-swap proof (sibling of the second-rubric proof). | the RevOps SME session = prerequisite. | Same as above. |
| **Author order ≠ run order.** Sales rubric authored first (satisfies the lock); service rubric authored second and *runs first* on the FS corpus. | "Sales/outbound rubric first, service second" read as run order (brief §4 lock). | Forfeits the only corpus we can actually get, in service of a lock the split already satisfies. |
| Spine first, no LLM: index + store + evidence gate on synthetic transcripts, byte-reproducible. Then label pass → 3–5-item mini-rubric → aggregate → synthesize → report at tens of interactions, with null control + split-half wired into run one. | No sequencing existed. | Loses the "every contract exercised end-to-end before scale" property. |

### 2.2 · Rubric, schema, and the contracts

| Ruling (governs) | Predecessor position (dead) | Cost of regression |
|---|---|---|
| **Field split:** `remedy_class`, `effort`, `outcome` live in the **catalogue**, joined via `swap_ref`. Rubric item = `id` · `description` · `polarity` · `detection` · `unit_of_count` · `swap_ref` (nullable) · declared schema + tag-vocab versions. | Both brief §3 and scope v2 §2 table `remedy_class`/`effort`/`outcome` **as rubric fields**. | **Highest rollback risk in the pack** — two predecessor docs say the opposite in a formatted table. Undoing it re-blocks the rubric on the catalogue (see 2.1). |
| `polarity` carried unchanged — "one mechanism, two polarities." | *(unchanged; listed because the session never restated it and silence reads as deletion)* | "What's working" becomes a separate subsystem. |
| **Four versioned artifacts, distinct cadences:** index tag vocabulary (slowest) · label schema (slow) · rubric (fast) · swap catalogue (independent). Both swap; rubric declares the versions it was written against; loader refuses unmet deps. | "Rubric vs. label schema is currently conflated… don't decide it here." (scope v2 §2) | Returns the boundary to open and the PRD can't specify contracts. |
| **Classify = two sub-passes.** Pass 1 schema labels (rubric-independent); pass 2 rubric hits. **A rubric swap re-runs only pass two.** | Single classify stage. | Makes hot-swap expensive and the swappability proof a full reprocess — and drops the shape that v1.5 model-routing plugs into. |
| `unit_of_count` = **closed enum** (`occurrence`/`interaction`/`account`/`time-estimate`/`chain`), one per item, defined in the label schema. **Dedup is the item's declaration, not the model's judgment.** Counts never cross-sum. | Open list — "interactions, minutes, occurrences, accounts" (scope v2 §2). | Counts stop being comparable, which breaks the priced view. |
| `chain` = deterministic metadata links only (thread ID / account ID). Never LLM-inferred. | Unspecified. | Repeat-contact counts become unfalsifiable. |
| Hot-swap = 3 mechanics: schema-validated plain-language config, no rubric text in code · **rubric may only reference published tag-vocabulary tags** (the index↔rubric contract) · acceptance test = loading the service rubric touches zero code. | "Proving a second rubric loads cleanly is a v1 success condition" — asserted, no mechanism. | The swappability claim goes back to being untestable. |
| Core-only schema for v1 (motion, intent, driver-origin, automatability, outcome, handoffs). Domain extensions **rejected** for v1. | Not addressed. | One schema + two rubrics is the purest form of the swappability claim; extensions dilute the proof. |
| Rubric v1 is generic, and a **corpus-arrival adaptation pass is a named build step** — v1 does not pretend to fit corpus-blind. | Implicit assumption that rubric v1 is final. | Hides an inevitable step, making the first run look like a failure. |

### 2.3 · Index and reproducibility

| Ruling (governs) | Predecessor position (dead) | Cost of regression |
|---|---|---|
| Snippet = smallest natural discourse unit per source type; positional content-stable IDs `{interaction_id}:{seq}`; **span addressing** (claims cite contiguous ranges). Chunking rules are part of the index version. | "Split into snippets, assign stable IDs" — no unit defined. | Signals that cross turns become uncitable. |
| Tag vocabulary = four families (structural · lexical · metadata joins · computed). **Bright line: nothing in the vocabulary requires judgment.** | "Tag deterministically" — no vocabulary. | The bright line is what keeps the index deterministic and the prefilters auditable. |
| Store = **one SQLite file per run** — snippets, tags, labels, hits, rollups, drop log. Portable, bidirectionally queryable, content hash per row. | "Build a retrievable provenance store." | Portability satisfies customer-owns-the-intelligence; the content hash is what the evidence gate matches against. |
| **"Same answer twice" = three structural mechanisms:** deterministic byte-identical index build (property-tested) · all samples seeded, seeds in manifest · **classification persisted per (corpus, schema, rubric, model) tuple, not a live call.** LLM nondeterminism survives only in synthesis prose. | "Reproducibility is the point" — asserted, no mechanism. | Reproducibility returns to aspiration. |
| **Drop log:** evidence-gate failures are dropped from the report per the lock, but every drop writes a row. Drop *rate* above threshold = run-health signal. | "Failures are dropped, not flagged." | Silent recall loss with no way to measure it — the exact lock interaction the session was convened to resolve. |
| Run manifest: corpus hash, four artifact versions, model+version, prompt hashes, seeds. | Did not exist. | Kills the report-diff re-measure (§2.5). |

### 2.4 · Validation — the section most at risk

The brief offered planted-synthetic as a straw man *to be attacked*. It was attacked. **Reverting to "synthetic corpus with planted pathologies" as the validation design is a regression to a position the session explicitly demoted**, not a simplification.

| Ruling (governs) | Predecessor position (dead) |
|---|---|
| **Six tiers, all ratified:** Calibration (planted synthetic + null controls + collusion-broken plants + loudness curves) · Differential (delta injection into real corpora) · Stability (split-half, paraphrase invariance) · Self-consistency (drift triangulation, escape audits, label self-agreement, drop-rate) · Adjudication (**second frontier model, different lab, in the audit seat**) · Honesty (coverage accounting + saturation curve). | Single tier: planted synthetic scored on precision/recall + magnitude tolerance. |
| Planted-synthetic survives as **instrument calibration only**, with three repairs: null controls · collusion-broken plants (plant author never sees rubric text; vocabulary disjointness) · loudness curves (sensitivity floor, not pass/fail). | Planted synthetic as the whole answer. |
| **Escape audits on every prefilter** — classify a seeded random sample of *excluded* snippets; hits estimate miss rate. Recall loss is measured, never silent. | Not addressed. |
| **Competing-mechanism discharge:** single-narrative causal claims forbidden; each finding names its top alternative mechanism and the discriminating evidence; pipeline checks the store. Not found → ships marked *undischarged*. **Plausibility is not sufficient to print.** | Not addressed — and this is the direct answer to the brief's stated worry ("fluent, plausible, slightly-wrong output whose arithmetic is internally consistent"). |
| **Completeness claim restated permanently:** not "these are all the drivers" but "the rubric accounts for X% of volume; the residual is characterized into these clusters; discovery saturated / did not saturate." Residual size is a **headline** number. | Completeness asserted as a product claim. |
| **Validation cost is O(1) by construction** — every audit fixed-size sampled. Corpus cost linear, validation cost flat. | Not addressed. |
| Failure taxonomy the evidence gate cannot catch (5 named modes: biased classification · genre hallucination · mechanism error · artifact findings · false completeness). | Not addressed. |

### 2.5 · Output, corpus, PII, abandon

| Ruling (governs) | Predecessor position (dead) |
|---|---|
| **Leverage = grid**, not scalar product. Effort-band × outcome-band; corpus count breaks ties within a tier; Class D in the high-effort/low-outcome corner. | "Effort × outcome" (lock) read literally as multiplication — **the lock is satisfied by the grid**; the session ruled the scalar product fake precision at this stage. |
| Effort/outcome = **bands with split provenance** — outcome = corpus-measured count × catalogue per-unit value band; effort = catalogue implementation band (config-change / integration / behaviour-change / capital). | Two numbers of unstated origin. |
| Evidence tier is **buyer-facing**: remedies print as *confirmed in practice* vs *candidate substitute*. | Internal-only metadata. |
| Output = one document, six sections, **in attention order: Highlights → What's working → Leverage grid → Priced plays → Full distribution + coverage → Open flags + method page.** | Scope v2 §4 lists the same material in a different order (what's working first, priced view last). |
| **PDF primary + self-contained HTML evidence companion** — citations expand inline to verbatim snippets. Not a dashboard: a versioned, dated **run artifact**, diffable; the "did it stick" re-measure is a diff of two reports, mechanical via the manifest. | Format unspecified. |
| **Synthetic corpus is permanent validation infrastructure**, built regardless; FS corpus pursued in parallel. Nothing waits. | Synthetic listed as one of four *fallback* options for the first corpus. |
| Non-circularity: second-lab model as generator · generation from pathology descriptions, never rubric text · vocabulary disjointness · **CFPB complaint narratives as realism donor.** | "What makes a synthetic corpus non-circular?" — open question. |
| **PII: nothing unscrubbed ever persists.** Scrub at ingest before the index writes a byte; deterministic patterns + NER + sampled human audit. **Identifiers salted-hash pseudonymized, not deleted** — `chain` survives, identity doesn't. Zero-retention API terms. | "PII posture unresolved for the text phase." |
| **PIPEDA sets the MVP floor.** Other jurisdictions tracked, not delivered against. Scrub stage ships even though the FS data is cleared test data — **as a capability demonstration.** | Unresolved. |
| **Three abandon triggers, pre-registered:** calibration failure · **the sample self-test** (10% subsample vs whole-corpus diff, published internally every run — the value proposition, measured) · the decision test (findings ≈ an operator's hour of priors *and* counts change no decision). | No abandon trigger existed. |
| **1K/100K breaks are economic, not architectural** — and the two-sub-pass split is already routing-shaped for the v1.5 carve-out. | Open question. |

---

## 3 · Reopen-eligible — where the brainstorm lacked context

This is the **only** list of things the session got wrong-by-omission. Everything here is fair to revisit; nothing outside it is.

The session was run deliberately narrow: agenda-driven, MVP-shaping, with an explicit instruction to skip business strategy and competitive positioning. It also had no calendar, no stack, and no corpus facts in front of it. Those absences are real, and three of them can legitimately move a ruling.

| # | Missing context | What it can legitimately move | What it must **not** move |
|---|---|---|---|
| R1 | **The calendar.** No dates were in the room; the session targeted "ASAP." Actual gates: PRD due **Aug 31** (5.1j-2), demoable end-to-end to an external party **Sept 15** (5.1j-1). The §8 spine plus eight mandated artifacts plus six validation tiers may not fit. | Scope triage — *which tier ships at v1 vs v1.1*, how thin the first rubric is, whether the FS run makes Sept 15. | Triage means **defer with a named trigger**, never delete. A validation tier dropped for time must appear in the roadmap with the condition that reinstates it. The abandon triggers are not schedule-negotiable — they're what make the claim honest. |
| R2 | **FS corpus facts.** Volume, date range, transcript format, provenance note all unknown (open q #4). "Best-chance corpus" was a judgment on availability, not on fitness. | If the corpus turns out too small or unusable: the author-order/run-order resolution goes back in play and sales-first-run is live again. Also moves the corpus-adaptation pass and the sample self-test's statistical floor. | The *reason* for the split (locks constrain authoring, not sequencing) survives regardless. Don't re-fuse them. |
| R3 | **Stack, runtime, repo conventions.** SQLite-per-run and "self-contained scalable unit" were ruled stack-blind. `Projects_gh/CIX` exists; nothing specifies language, execution host, or CI. | Implementation shape of the store and the unit; testing tooling; how the property test for byte-identical builds is written. | The store's *role* — portable, bidirectional, content-hashed, one file per run — is a design ruling, not an implementation detail. |
| R4 | **Models and spend.** Second-lab audit seat ruled without naming a model or a budget (open q #5). Western-origin guardrail applies. | Model selection; whether the audit seat and plant generator are the same model (review finding F4 — if so, the seat must never adjudicate corpora its sibling generated). | "Frontier throughout for the proof" is a lock. Cost optimisation is the v1.5 carve-out; don't pull it forward. |
| R5 | **Competitive position.** Explicitly excluded from the session. Encore AI ($30M Series A, 7/29, "interaction mining" + agent deployment), Operative Intelligence, SentiSum all ship adjacent capability. | The PRD's differentiation framing and which outputs are demo-load-bearing on Sept 15. | Must not reshape a technical ruling. If competitive pressure argues for a design change, that's a new decision to record — not a reason to prefer a predecessor doc. |
| R6 | **Build ownership.** the Contract Engineer's track boundary, junior-dev hire, PO's interim-PM seat — none were in the room. | Who builds which artifact; parallelization of the §8 sequence. | The sequence's dependency order. |
| R7 | **Menu ratification** (open q #8) — the findings→menu join that drift triangulation consumes. External to this build (the Commercial Principal/PO). | The join's shape once the menu ratifies. | Drift triangulation itself, which stands on the raw-vs-distilled diff regardless of menu state. |

**Not reopen-eligible, stated explicitly because they look like gaps and aren't:** the SME catalogue being unfilled (that's the design — stand-in now, enrichment later), the corpus being unsecured (opportunistic by design, synthetic ships regardless), and POC A convergence (separate track validating a segment, not a technology).

---

## 4 · Known gaps — carry these in

From the review pass. None contradicts a ruling; all are things the PRD must resolve.

**Three that must be decided — they can't stay open past this session:**

1. **Residual clustering at v1 scale.** §5 headlines "residual characterized into clusters" *every run*, but §8 parks embedding-based clustering at the 100K carve-out. Something else must produce clusters at tens–hundreds scale. Frontier-LLM grouping over unmatched snippets is the obvious candidate and is consistent with frontier-throughout.
2. **Grid placement of remedy-less findings.** §1 rules they print; the grid needs effort/outcome bands that only exist via a catalogue join. An unjoined finding has neither coordinate. Likely a "no known remedy yet" shelf adjacent to the grid — which is also honest framing for the SME enrichment pass.
3. **Coverage denominator.** "Rubric accounts for X% of volume" — volume in snippets, interactions, or per-`unit_of_count`? It's a headline number *and* an abandon-trigger input, so it's load-bearing, not a tuning detail.

**Three that can travel as tracked items:** the audit-seat/plant-generator collusion rule (F4, folded into open q #5) · a realism donor for the **sales-side** calibration corpus (CFPB is service-flavoured; the sales rubric is authored and calibrated first) · plus the nine original open questions in output §10.

**One thing no source document has:** per-stage **acceptance criteria** as a list. The session produced them implicitly, scattered across §2/§4/§5. Assembled:

- Index build is byte-identical for the same corpus + version (property-tested)
- Loading the service rubric touches zero code
- Every quote resolves to a snippet ID and string-matches source via content hash
- Every quantitative claim reproduces from the rollup
- All samples seeded; seeds in the run manifest
- Escape audit, label self-agreement, null control, split-half all wired into run one
- Sample self-test diff emitted every run
- Rubric loader refuses unmet schema/tag-vocabulary dependencies

---

## 5 · What good output from this session looks like

Enough to write the PRD without re-deciding anything: the three §4 decisions ruled · R1 scope triage against Sept 15, with deferrals carrying reinstatement triggers · the §11 artifact list ordered into a dependency graph with owners · acceptance criteria confirmed and assigned to stages · R3–R6 context supplied by PO and recorded.

**Session rules:**

- The brainstorm output governs. Contradict it only via a §3 row, and say which one.
- If you think a ratified ruling is wrong, **say so explicitly and say why** — don't quietly design around it. That's the same rule the 7/31 session ran under, and it's why the locked list survived intact.
- Ask before proposing wherever the answer depends on something only PO knows — R2 through R6 are all in that category.
- Deferring is fine; deleting is not. Anything cut for the calendar leaves a named trigger behind.

## Changelog

- **2026-07-31** — Created as the single input document for the pre-PRD session, consolidating the brainstorm output, the review findings, and the precedence rules needed to prevent regression to superseded docs. — Claude (Cowork)
