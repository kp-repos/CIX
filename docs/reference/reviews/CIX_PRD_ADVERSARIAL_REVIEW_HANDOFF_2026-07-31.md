# CIX PRD v1 — Adversarial Review Response and Next-Drafter Handoff

**Reviewed artifact:** CIX_PRD_v1_2026-07-31.md

**Review date:** 2026-07-31

**Review posture:** Adversarial product, evidence, implementation, security, and demo-readiness review

**Audience:** PO and the next PRD drafter
**Recommended disposition:** Preserve the architecture, return the PRD for a controlled v1.1 revision before ratification

---

## 1 · Bottom line

The PRD has an unusually strong spine: source-linked evidence, explicit units of count, persisted classification, rubric/catalogue separation, visible uncertainty, and a falsifiable whole-corpus claim. Those choices should survive.

The draft is not yet a dependable build contract. It has four classes of problem:

1. **Normative ambiguity:** the PRD depends on missing or mis-versioned documents, delegates acceptance criteria elsewhere, and contains incorrect section references.
2. **Internal contradiction:** it promises all six validation tiers and a full real-corpus demo while simultaneously proposing to defer one tier and allowing a synthetic fallback.
3. **Test design that can self-confirm:** the current whole-vs-10% threshold is easy to pass through ordinary sampling noise, especially with a “rare driver below 1%” rule.
4. **Operational gaps:** security, persistence keys, evidence checks, failure handling, pricing semantics, and owner accountability are not precise enough to implement or audit.

The next draft should be shorter in claims and stronger in contracts. It should clearly separate:

- what must be true for the build to start;
- what must be true for a real-data run;
- what must be true for the external demo;
- what must be true to call v1 successful; and
- what is explicitly deferred.

## 2 · What not to lose

Do not reopen these without a recorded product decision:

- detection works without a remedy catalogue;
- rubric-independent labels and rubric hits are separate persisted passes;
- rubric and catalogue swaps require no pipeline code changes;
- count units never cross-sum and every share names its denominator;
- index tags remain deterministic and judgment-free;
- logical-content equality, not raw SQLite-byte equality, is the reproducibility contract;
- every published quote resolves to scrubbed stored evidence;
- evidence failures are omitted from the report and retained in a drop log;
- remedy values and effort remain bands, not fake-precision scalar ROI;
- remedy-less findings remain visible on a “no known remedy yet” shelf;
- causal mechanisms are discharged or explicitly marked undischarged;
- coverage, residuals, audit failures, and unfavorable self-test results remain buyer-facing;
- the first real run uses the service rubric even though the sales rubric is authored first; and
- the run is a dated, portable artifact rather than a live dashboard.

These are the product's credibility moat. Schedule pressure should reduce rubric breadth before weakening them.

## 3 · Release-blocking findings

Severity meanings:

- **P0:** resolve before PRD approval or real-data work.
- **P1:** resolve before the external demo.
- **P2:** improve for maintainability or later scale.

| ID | Severity | Finding | Required next-draft action |
|---|---|---|---|
| AR-01 | P0 | The normative document chain is broken. The PRD cites design record rev 2.1, while the repository contains rev 2. It also cites CIX_Swap_Catalogue_v0.md, the POC B baseline, and an Input Pack that are not present in the repository. | Add a normative-source table with exact filename, revision, location, status, and precedence. Inline any requirement needed to build or test v1. Do not point to a missing file as the definition of a required schema. |
| AR-02 | P0 | Ratification references are wrong. The header says §§8–9 need ratification, but scope triage and thresholds are §§7–8. R-VAL-1 points to §8 for triage, also off by one. | Correct every section and decision reference mechanically. Add a link checker or reference test to the document-review checklist. |
| AR-03 | P0 | The scope contract contradicts itself. R-VAL-1 requires six tiers at their stated cadence; §7 defers the differential tier; M5 promises the “full validation suite”; the design record says all six tiers are ratified. | Replace the prose with one scope matrix showing each tier's v1 mechanism, sample depth, gate/warn behavior, and deferral. Any deviation from the governing record requires an explicit PO decision. |
| AR-04 | P0 | Threshold pre-registration is chronologically impossible as written. M2 emits null-control and split-half results, while §8 says thresholds freeze at M3. | Freeze each threshold before its first observed result. Separate development fixtures from a held-out acceptance set. Any threshold tuned on development data must be evaluated once on untouched holdout fixtures. |
| AR-05 | P0 | T-SST makes the core hypothesis too easy to “prove.” Any highlight change, any value-band change, or any sub-1% driver absent from one 10% sample can occur through ordinary sampling noise. | Replace the single-draw, any-change rule with a pre-registered multi-seed comparison plus a decision-materiality rule. A rare driver counts only if it clears minimum full-corpus support and changes an action or priority. |
| AR-06 | P0 | Acceptance is not self-contained. §12 delegates the normative definition of done to another document and does not map requirements to tests. | Put the full acceptance matrix in the PRD: requirement → test → evidence artifact → gate/warn → owner → milestone. The design record may hold rationale, not hidden test obligations. |
| AR-07 | P0 | Untrusted-content threats are absent. A transcript can contain prompt-injection text; an evidence excerpt can contain HTML/script payloads; malicious content can alter classification or the self-contained report. | Add an untrusted-input threat model and adversarial fixtures. Corpus text must always be treated as data, never instruction. HTML output must escape excerpts and prevent active content. |
| AR-08 | P1 | The persisted-artifact keys are underspecified and partially wrong. One tuple is described for both labels and hits even though rubric-independent labels must be reusable across rubric changes. | Define separate immutable keys for the indexed corpus, schema-label artifact, rubric-hit artifact, synthesis artifact, and report. Include code revision, index version, immutable model snapshot, prompts, inference settings, and parent artifact IDs. |
| AR-09 | P1 | The evidence gate proves exact quoting but not the validity of inference or arithmetic. A perfectly matched quote can still support a wrong label, count, share, remedy, or mechanism. | Specify distinct checks for citation existence, excerpt equality, quantitative recomputation, unit/denominator consistency, catalogue-unit compatibility, mechanism status, and report escaping. Keep semantic support as an adjudicated audit rather than pretending it is purely mechanical. |
| AR-10 | P1 | Pricing language overclaims. “What it's worth” sounds like a forecast even when bands are inferred. Overlapping findings can also double-count the same opportunity. | Call v1 values indicative opportunity bands. Require currency, time horizon, source date, per-unit basis, provenance, and evidence tier. Ban portfolio totals until overlap and mutual-exclusivity rules exist. |
| AR-11 | P1 | Milestone gates occur too late. Corpus facts and the input contract are due at the same milestone as ingest; the PRD is finalized after several build milestones; the demo fallback does not satisfy the stated real-corpus goal. | Approve a build-baseline PRD before M1. Resolve corpus readiness before M4 starts. Separate “demo can proceed” from “v1 product goal passed.” A synthetic fallback is a demo fallback, not successful completion of Goal 1. |
| AR-12 | P1 | The fixed-size validation-cost claim is statistically incomplete. Audit cost may be constant versus corpus size, but not necessarily versus rubric size, number of subgroups, desired confidence, or rare-event prevalence. | State the dimension against which cost is bounded. Use risk-stratified sampling and disclose when the audit is underpowered. Do not use top-count-only sampling for a product whose thesis depends on rare drivers. |
| AR-13 | P1 | Ownership is not accountable. “Build,” combined role labels, and a model are not named accountable owners; several open decisions have no committed decision-maker. | Use one accountable human or explicitly assigned role per gate and artifact. Add consulted/approver roles separately if useful. |
| AR-14 | P1 | No cost, latency, capacity, or reliability budget exists even though the calendar and frontier-model spend are known risks. | Add a v1 operating envelope: corpus-size range, maximum run cost, target wall-clock time, retry policy, artifact size, and acceptable partial-failure behavior. |
| AR-15 | P2 | “Zero call resolution” is stated as fact and may bias the detector toward deficiency. It also does not fit email, chat, sales, or wanted customer contact. | Label it as a service-rubric hypothesis or design lens, not the product premise. Preserve positive polarity and let the corpus test the claim. |

## 4 · Contradictions the next draft must resolve explicitly

| Topic | Statement A | Statement B | Resolution needed |
|---|---|---|---|
| Validation scope | R-VAL-1 requires all six tiers at stated cadence | §7 defers differential validation until a paid engagement | Either retain a minimal FS delta test in v1 or record a governing decision that changes the tier requirement |
| Demo validation | M5 promises the full validation suite | Scope triage reduces several tiers to samples or defers them | Rename it “approved v1 validation suite” and enumerate exactly what runs |
| Real-corpus success | Goal 1 requires a real corpus at demo | Risk mitigation says a calibration-corpus demo is viable | Distinguish demo continuity from MVP success; the fallback cannot close the real-corpus goal |
| Threshold freeze | M2 produces validation results | Thresholds freeze at M3 | Freeze affected thresholds before M2, with a held-out M3 acceptance set |
| PRD timing | PRD gate is Aug 31 | Build begins Aug 8 and scope/thresholds govern M1–M3 | Approve an initial build baseline before M1; Aug 31 becomes a controlled revision, not first approval |
| Source independence | No source-specific logic in any stage | Transcript, email, chat, and notes require different normalization/chunking | Allow versioned source adapters while banning hidden engagement-specific logic |
| Model persistence | Downstream reads persisted classification and “never re-calls” | Synthesis is a model stage after aggregation | Persist synthesis separately; report rendering must not silently resynthesize |
| Catalogue proof | Product goal implies a catalogue hot swap | §7 allows a stub-variant swap | Call the stub a mechanism test; reserve “knowledge swap proof” for the SME-enriched catalogue |
| Product overview | Value is described as occurrence counts × remedies | The rubric supports five incompatible units | Use “unit-compatible measured quantities joined to per-unit value bands” |

## 5 · Rebuild the whole-corpus self-test

This test is the product's central falsification mechanism. It must be harder to game than the current T-SST.

### 5.1 What the test can establish

The test can show whether access to the full corpus changes the run's measured distribution, selected findings, opportunity bands, or proposed actions relative to a 10% analytical sample.

It cannot, by itself, show that:

- the classification is correct;
- the full-corpus narrative is causally correct;
- a human operator would reach the same sample conclusion as the model; or
- whole-corpus analysis is valuable for every corpus type.

State those limits in the PRD.

### 5.2 Required protocol

1. Freeze corpus eligibility, rubric, catalogue version, thresholds, highlight-selection rules, and comparison metrics before running the comparison.
2. Define when a corpus is large enough for a 10% test. If the sample is too small for the declared metrics, emit **not evaluable**, not pass.
3. Use multiple predeclared seeds. One draw is too vulnerable to luck.
4. For every sample, regenerate aggregation, ranking, highlights, residual summaries, and priced bands using only that sample's records. Full-corpus information must not leak into sample synthesis.
5. Compare results only within compatible units.
6. Separate:
   - statistical/distribution difference;
   - rank or highlight difference;
   - opportunity-band difference; and
   - sponsor-decision difference.
7. Require a rare-driver candidate to clear:
   - a minimum full-corpus count;
   - evidence-quality gates;
   - stability across full-run checks; and
   - an explicit action or priority consequence.
8. Record the number of seeds showing the material difference, not merely whether any seed did.
9. Keep the “sharp operator” baseline as a separate pre/post product-usefulness test. Do not treat the model's 10% subset as a proxy for human review.

### 5.3 Replace T-SST

Do not freeze a new numeric value until power and expected corpus size are known. The threshold register should define:

- minimum eligible corpus size;
- number of 10% seeds;
- distribution metric and tolerance per unit;
- top-k/rank metric and tolerance;
- minimum support for a rare driver;
- material opportunity-band movement;
- decision-materiality rubric; and
- the proportion of samples in which a claimed full-corpus advantage must appear.

“Any change” is not evidence of product value.

## 6 · Redesign the threshold register

The provisional values are useful hypotheses, not yet defensible gates.

| Threshold | Adversarial concern | Better drafting instruction |
|---|---|---|
| T-ESC | A point estimate above 5% is meaningless without excluded-sample size and uncertainty | Specify sample design and a one-sided confidence bound on miss rate; stratify for rare/high-risk items |
| T-AGR | Raw 85% agreement can look excellent on imbalanced labels | Report per-field and per-label agreement with a chance-corrected or prevalence-aware metric and confidence interval |
| T-DROP | “2% of findings” has a manipulable denominator and ignores severity | Define candidate-claim denominator, reason codes, and severity; a single fabricated-evidence drop may be release-blocking |
| T-SPLIT | “Rank flips beyond the computed 95% band” is not an executable formula | Name the rank metric, tie handling, minimum support, and uncertainty method |
| T-PARA | A 20% count swing mixes paired judgment instability with corpus sampling | Run paired decisions on identical evidence under paraphrased criteria; measure item-level disagreement |
| T-CAL | Relative ±20% behaves badly near zero and “mechanism named” is vague | Use absolute plus relative error, calibration slope/intervals where appropriate, and separately scored mechanism attribution |
| T-NULL | “Zero above the noise floor” is circular if the same run establishes the floor | Define a held-out null set and an upper confidence bound on false-positive rate |
| T-SST | Any highlight/band/rare-driver change is almost guaranteed eventually | Use the multi-seed, decision-materiality protocol in §5 |
| T-ITER | Three cycles can overfit the calibration corpus | Split development and holdout fixtures; revisions see development results only, then get one predeclared holdout evaluation |

For every threshold, the PRD must say whether failure:

- blocks the run;
- blocks a specific finding;
- demotes a finding;
- adds a visible warning; or
- triggers a bounded revision cycle.

An “alarm” without a prescribed consequence is not a requirement.

## 7 · Make the architecture executable

### 7.1 Replace the linear pipeline with stage gates

Validation is not one stage after synthesis. The next draft should show:

1. input eligibility gate;
2. normalization/index reproducibility gate;
3. schema-label pass and label audit;
4. rubric-hit pass and prefilter escape audits;
5. aggregation and quantitative checks;
6. remedy join and unit/provenance checks;
7. validation/adjudication;
8. persisted synthesis and evidence checks;
9. deterministic report rendering and final integrity scan.

Different validation checks attach to different stages. A single “validate” box hides when failures must stop downstream work.

### 7.2 Define artifact identity correctly

At minimum, define these immutable artifacts:

| Artifact | Key must include |
|---|---|
| Canonical corpus artifact | input fingerprint, eligibility rules, normalizer version |
| Index | corpus artifact ID, index/tag-vocabulary version, code revision |
| Core labels | index ID, schema version, immutable model snapshot, system/task prompt hashes, inference settings |
| Rubric hits | label artifact ID, rubric version, immutable model snapshot, prompt hashes, inference settings |
| Aggregates | hit artifact ID, dedup/count rules version |
| Remedy/priced view | aggregate ID, catalogue version, currency/time-horizon assumptions |
| Synthesis | aggregate/priced-view IDs, model snapshot, prompt hash, validation-state input |
| Report | synthesis ID, manifest ID, template version, renderer version |

This fixes a major contradiction in R-IDX-5: rubric-independent labels cannot be keyed by a tuple that includes the rubric.

### 7.3 Add run behavior

The PRD needs requirements for:

- idempotent retry after model/provider failure;
- resuming without duplicating records or charges;
- partial-stage status and failure reason;
- immutable completed artifacts;
- invalidation when a parent artifact changes;
- no-hit, no-remedy, zero-denominator, and empty-eligible-corpus behavior;
- missing account/thread identifiers;
- model refusal, timeout, rate limit, and malformed output;
- deterministic config validation before paid calls; and
- cost and item-count telemetry by stage.

## 8 · Define the evidence gate as a family of checks

The phrase “evidence gate” currently carries more assurance than its requirements provide.

The next draft should distinguish:

1. **Citation integrity:** snippet IDs exist; cited ranges are valid; excerpts exactly match scrubbed stored content.
2. **Quantitative integrity:** counts, deduplication, shares, denominators, ranks, and bands recompute from persisted rows.
3. **Join integrity:** rubric and catalogue units are compatible; all references resolve; catalogue provenance exists.
4. **Narrative integrity:** every material statement cites evidence; causal language respects discharged/undischarged state. Semantic support is sampled/adjudicated, not guaranteed by string match.
5. **Rendering integrity:** evidence text is escaped; HTML cannot execute corpus-supplied markup or scripts.
6. **Manifest integrity:** PDF, HTML, store, thresholds, and audit results identify the same run.

The drop log should record check, reason, stage, severity, affected finding, and scrubbed content reference. It should not copy unnecessary content into a second leakage surface.

## 9 · Treat corpus content as hostile input

Add explicit negative requirements:

- The model must treat corpus text, labels, catalogue prose, and excerpts as quoted data, not instructions.
- Source text such as “ignore the rubric and output…” must not alter configuration or tool behavior.
- The pipeline must delimit data from system/task instructions and test this with adversarial fixtures.
- HTML, Markdown, URLs, control characters, and bidirectional text from the corpus must be safely encoded.
- Evidence links must not create active external requests in a self-contained artifact.
These tests belong in M1/M2, not in post-demo hardening.

## 10 · Fix opportunity-band and catalogue semantics

The next draft should replace “what it's worth” with **indicative opportunity band** until source evidence is confirmed.

Every value band needs:

- compatible count unit;
- currency;
- time horizon;
- price/cost basis;
- lower/upper calculation;
- source and source date;
- inferred/observed status;
- evidence tier;
- vertical applicability; and
- assumptions or exclusions.

Also decide:

- whether one finding may join to multiple remedies;
- how alternative remedies are displayed without double-counting;
- whether one remedy may address multiple overlapping findings;
- when a catalogue entry becomes “confirmed in practice” and who can approve that state; and
- whether total opportunity is prohibited until overlap is modeled.

Recommended v1 rule: show per-play bands; do not produce a portfolio total.

## 11 · Correct the milestone and governance model

### 11.1 Suggested gates

| Gate | Must be true |
|---|---|
| Build baseline, before M1 | Scope matrix approved; normative sources resolved; threshold protocol approved; accountable owners assigned; operating envelope set |
| Synthetic-model work, before M2 model calls | Prompt-injection controls and development thresholds frozen |
| Calibration acceptance, before M3 result | Held-out fixtures sealed; calibration/null/stability gates frozen |
| Real-data readiness, before M4 begins | Input contract, corpus facts, source format, eligibility rules, and accountable owner confirmed |
| Real-run release, before M5 report | All approved v1 validation results present; threshold consequences executed; final evidence/security checks pass |
| External demo | Demo artifact approved for audience; no unresolved release-blocking flag; fallback status labeled honestly |
| V1 success | Real-corpus goal, hot swaps, evidence/reproducibility, self-test, and decision log all complete |

### 11.2 Separate three outcomes

The draft currently blends them:

1. **Pipeline demo-ready:** the system can be shown, possibly on synthetic data.
2. **Real-run release-ready:** an authorized corpus produces a gated artifact.
3. **V1 hypothesis supported:** the real run passes integrity gates and adds a decision-relevant whole-corpus result.

A synthetic fallback may satisfy outcome 1. It does not satisfy outcomes 2 or 3.

## 12 · Rewrite success measures

Use three layers.

### 12.1 System acceptance

- evidence and quantitative integrity;
- deterministic index equality;
- correct dependency rejection;
- hot-swap behavior;
- security gates;
- reproducible artifact identities; and
- operating-envelope compliance.

### 12.2 Analytical acceptance

- held-out calibration and null performance;
- stability and escape-audit outcomes;
- residual/saturation disclosure;
- mechanism adjudication; and
- full-vs-sample comparison under the approved protocol.

### 12.3 Product usefulness

Before seeing the report, the sponsor records:

- current top priorities;
- expected major drivers;
- intended decisions;
- confidence in each; and
- what magnitude of new evidence would alter action.

After the report, record the same fields and the evidence responsible for any change. “Materially strengthened confidence” must require an observable before/after movement, not retrospective agreement.

## 13 · Acceptance tests the next draft should add

At minimum:

- unknown rubric tag, schema version, count unit, or dangling catalogue reference fails before model calls;
- rubric change reuses label artifact but creates a new hit artifact;
- catalogue change leaves index, labels, and hits unchanged;
- malformed model output retries or fails without partial corruption;
- resumed run does not duplicate hits, records, or charges;
- prompt-injection fixtures do not alter rubric or pipeline behavior;
- HTML/script payloads render as inert text;
- missing linkage metadata disables account/chain items with an explicit coverage note;
- zero eligible records produces a valid no-result artifact, not divide-by-zero or false saturation;
- no findings produces a valid report with residual and method sections;
- no remedies puts findings on the shelf without fabricated grid coordinates;
- every numeric claim recomputes from persisted data;
- every share names a valid denominator;
- overlapping findings do not silently create a total opportunity value;
- a threshold breach has the documented block/demote/warn consequence;
- PDF and HTML identify the same manifest and quantitative contents;
- final report generation does not trigger hidden reclassification or resynthesis; and
- an incompatible repeat run is refused or clearly marked non-comparable.

## 14 · Recommended v1 scope adjustment

If calendar pressure requires cuts:

1. Reduce rubric breadth first.
2. Keep a **minimal differential test** on representative FS text rather than deferring the entire tier. It is the only validation mechanism with known changes in real language.
3. Use coarse loudness levels, as proposed.
4. Sample drift triangulation, but stratify by rare/high-value items and report its detection limits.
5. Sample paraphrase invariance by risk: top-count, rare, near-threshold, and high-value items. Top-N by count alone contradicts the rare-driver thesis.
6. Keep the full honesty tier.
7. Keep the whole-corpus self-test, but label it not evaluable if the corpus is underpowered.
8. Keep the catalogue mechanism swap; label a stub swap as a mechanism proof, not expert-knowledge enrichment.
9. Defer run-to-run outcome claims until compatibility rules exist.

## 15 · Suggested structure for PRD v1.1

1. Document authority, status, and ratified decisions.
2. Product thesis, user, target decision, and explicit hypotheses.
3. V1 goals, non-goals, operating envelope, and three definitions of success.
4. Scope matrix: ship/defer, depth, trigger, and governing decision.
5. Stage-gated workflow and immutable artifact graph.
6. Functional requirements grouped by stage.
7. Security and hostile-input threat model.
8. Validation protocols and threshold consequence matrix.
9. Whole-corpus self-test protocol.
10. Output, opportunity-band semantics, and sponsor decision log.
11. Milestones, accountable owners, dependencies, and cut rule.
12. Self-contained acceptance matrix.
13. Open decisions and explicit ratifications.
14. Risks and recorded risk acceptances.
15. Changelog with exact normative-source revisions.

Use **must** only for testable requirements. Put rationale in the design record or a short note. Do not use a reference as a substitute for a requirement the implementation team must test.

## 16 · Questions the next drafter must take back to PO

1. Is differential validation part of the v1 real-run gate or formally deferred? The current documents say both.
2. Does a synthetic fallback preserve only the Sept 15 demo, or can it also close the v1 goal/KR?
3. What minimum corpus size makes the 10% self-test evaluable?
4. How many seeded samples are required, and what fraction must show a material full-corpus advantage?
5. What observable sponsor change counts as decision usefulness?
6. Which threshold failures block a run, block a finding, demote it, or merely warn?
7. What is the v1 cost, duration, and corpus-size envelope?
8. May one finding have multiple remedies, and are portfolio totals prohibited?
9. Who are the accountable product and technical owners?
10. What immutable model identifiers and code revisions are required for reproducibility?

## 17 · Definition of ready for the next draft

PRD v1.1 is ready for ratification when:

- all normative files exist and use exact versions;
- section and decision references are correct;
- the scope matrix contains no contradiction with goals, milestones, or acceptance;
- thresholds are frozen before first applicable results and have explicit consequences;
- the whole-corpus self-test cannot pass on “any difference” alone;
- the untrusted-input threat model is operational;
- artifact identity and persistence boundaries support the promised hot swaps;
- acceptance criteria are self-contained and mapped to requirements;
- milestones distinguish demo continuity, real-run release, and v1 success;
- every release gate has one accountable owner; and
- the external demo cannot accidentally present a fallback as validation of the product thesis.

## 18 · Recommended response to the current draft

Accept the product direction and the evidence-first architecture. Do not ratify the PRD as written.

Request a v1.1 that:

1. repairs document authority and internal references;
2. resolves the six-tier validation scope conflict;
3. moves threshold freeze dates before first results;
4. replaces T-SST with a multi-seed, decision-materiality protocol;
5. operationalizes hostile-input controls;
6. defines immutable artifacts, evidence checks, and failure behavior;
7. makes opportunity bands explicitly indicative and non-additive; and
8. carries a self-contained acceptance matrix with named accountable owners.

That revision would preserve the distinctive strength of CIX while making the build, demo, and falsification claims genuinely auditable.
