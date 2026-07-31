# CIX PRD v1 — Red Team

**Target:** `CIX_PRD_v1_2026-07-31.md` (v1 DRAFT)
**Governing record checked against:** `CIX_BRAINSTORM_OUTPUT_2026-07-31.md` **rev 2** · `CIX_PRD_Input_Pack_2026-07-31.md` (with rev-2 addendum)
**Posture:** adversarial. This document argues the case *against* the PRD. Findings are ordered by severity, each with a proposed fix. §7 states what survives the attack.
**Created:** 2026-07-31 · Claude (Cowork)

---

## 0 · Verdict

The PRD is faithful to the design record — that part worked. The Input Pack did its job: I found **one** substantive rollback (RT-11) across ~35 ratified positions, which is a good result.

The problem is elsewhere. **This PRD is not a plan; it's a rendering of the design record with dates attached.** Three separate mechanisms make it non-binding:

1. **All three abandon triggers have been individually defanged** by the threshold seeds in §8 and the missing sponsor. The document preserves the *language* of pre-registered falsifiability while removing every route by which the project could actually be killed.
2. **The calendar and the capacity are unmodelled.** Eight days to M1, five artifacts, no named engineer, three specialist owner roles silently reassigned to PO or to a placeholder called "build."
3. **The triage cuts only cheap things.** Every expensive surface rides into v1 intact.

Any one of those would be a serious PRD defect. Together they describe a document that will be ratified, then quietly missed, with no trigger firing to say so.

---

## 1 · The headline attack: falsifiability has been removed

The design record's best feature is §12 — three pre-registered abandon triggers aimed at the only unproven claim. The PRD is where those triggers acquire numbers. **All three numbers, taken together, make the triggers unfireable.**

### RT-1 · T-SST makes abandon trigger 2 impossible to fire *(critical)*

Trigger 2 fires when the 10% sample **reproduces** the full corpus's decision-relevant output within tolerance. §8 sets the materiality bar at:

> "any highlight change, any value-band change, or any rare driver (< 1% prevalence) absent from the sample"

A 10% seeded sample will *almost always* shift at least one highlight and drop at least one sub-1% driver — that's a property of sampling, not evidence of corpus value. The bar is set so that any difference counts as a material difference, so the sample essentially never reproduces the full corpus, so the trigger never fires.

This is precisely inverted from the design record's intent. §8 there is explicit: the diff "is the value proposition, measured," and "recorded even when unfavorable." A threshold that cannot produce an unfavorable result records nothing.

**Fix:** define materiality as *decision-relevant* difference, per the design record's own wording — a different top-3 action, a value band that crosses a pricing boundary, a rank flip that survives the split-half sampling band. "Any highlight change" must go. And state the null hypothesis explicitly: *the sample reproduces the decision* is the default the corpus must beat.

### RT-2 · T-CAL loosens the calibration bar with no stated basis *(critical)*

±20% relative magnitude recovery. The superseded MVP Scope v2 carried ±10 points. The PRD moves the number that decides whether the core capability is falsified — in the permissive direction — and presents it as a "provisional seed" with no derivation.

Adversarially: pick a wide enough tolerance and calibration cannot fail, so trigger 1 joins trigger 2 in the decorative pile.

**Fix:** derive it, don't assert it. State what magnitude error would make a finding decision-useless (if a driver is 20% of volume vs 24%, does anything change? If not, ±20% is fine and *say why*). Tie the tolerance to the decision, and record the derivation in the threshold register so a future reader can attack it.

### RT-3 · T-NULL is circular *(high)*

> "zero pathology reports above the noise floor **established in calibration**"

The noise floor is an output of calibration. The threshold that judges whether calibration passed is defined in terms of calibration's own results. That violates the PRD's own freeze-before-viewing rule (§8 preamble, R-VAL-6, design record §12) *in the definition of the threshold itself*.

**Fix:** set an absolute pre-registered floor (e.g. "≤ N false pathology reports per 100 null-corpus interactions, N fixed before the null run"), and keep the empirical noise floor as a separate reported statistic, not as the gate.

### RT-4 · Abandon trigger 3 cannot run — there is no sponsor *(critical)*

The decision test needs an operations leader with a decision riding on the run. The PRD names one in §1 ("primary user: an operations leader…") and again in §12 ("the sponsor records whether the first real run affected a decision"). **That person does not exist in this project.** The FS corpus is old test data from a contact; the Sept 15 event is a demo to an unnamed external party.

Consequences the PRD doesn't acknowledge:

- §1's success condition is unmeasurable at demo.
- A14 (sponsor decision-log template) is an artifact with no sponsor.
- D-10 ("sharp operator" baseline, due before M5) has no counterparty.
- The third abandon trigger is decorative.

**Fix:** pick one and say it out loud. Either (a) recruiting a named sponsor becomes a dependency in §6 with a date before M5, or (b) the decision test is explicitly marked **post-MVP**, the demo's success condition is restated honestly as *"an external party finds the artifact credible and traceable,"* and A14 ships as a template for the first real engagement. Option (b) is the honest one given the calendar — but it must be *written*, because right now the PRD claims a test it cannot perform.

### RT-5 · No threshold states a minimum sample size, and at v1 scale most lack power *(high)*

M2 runs "tens of interactions." The mini-rubric is 3–5 items. Against that:

- **T-DROP** — ">2% of findings." A 5-item rubric produces perhaps 10–20 findings. 2% of 15 is 0.3. The threshold cannot be crossed by a whole number. It's also the wrong denominator: the design record drops per *claim*, not per finding.
- **T-ESC** — ">5% per item." If the escape-audit sample per item is 20 excluded snippets, one hit is 5%. The threshold has a resolution of one snippet.
- **T-AGR** — "< 85%." On a seeded sample of 20 re-judgments, 85% is 3 disagreements. The confidence interval is wider than the effect.

Every threshold in §8 is written as if corpus scale were large. **The PRD never commits to a v1 corpus scale anywhere** — not in §1, not in §5, not in §7. "Hundreds" appears in the design record's ancestors and in scope v2; the PRD says "tens" at M2 and "the FS corpus" at M5, size unknown.

**Fix:** state the v1 scale target as a requirement. Then give every threshold a minimum sample size for validity, and a stated behaviour when the sample is below it (report "insufficient power," never a spurious pass). A threshold that silently passes on n=12 is worse than no threshold.

---

## 2 · Calendar and capacity

### RT-6 · M1 is eight days away and is the largest milestone in the plan *(critical)*

M1 (Aug 8) requires: index + store + evidence gate + manifest + drop log, working, on synthetic transcripts, with a logical-equality property test passing — **plus** A1 (tag vocabulary v1), A2 (label schema v1), A3 (manifest schema), A4 (threshold register), A12 (input-data contract).

Five artifacts and a tested deterministic spine, in eight days, from zero lines of code. In the same window, per the workstream brief: Oatmeal 1.1 ships Aug 1 (KR 5.5e), Candidates 2+3 selection was due Jul 31 (KR 5.5f), and PO holds the interim-PM seat on the contractor track.

The PRD's own risk 1 says "six weeks, one plate" and mitigates with the cut rule. **The cut rule cuts rubric items.** Cutting rubric breadth recovers no schedule for a spine that hasn't been built. The mitigation does not address the failure mode it's attached to.

**Fix:** re-baseline M1 honestly, or split it (M1a = spine + manifest, no property test; M1b = property test + judgment artifacts). Then state the schedule assumption explicitly: *hours per week available to this build.* Every date in §5 rests on a number that appears nowhere in the document.

### RT-7 · There is no engineer, and three specialist owners are unassigned *(critical)*

§6 says the build is "sized to PO's plate, built in `Projects_gh/CIX` with Claude Code sessions." The §4 owner column assigns A3, A12, A13, A15 to **"build"** — which is not a person.

Meanwhile the design record's open-decision register names owners the PRD does not have:

| Design record | Owner named there | PRD assignment |
|---|---|---|
| #2, #3 thresholds | PO + **tech lead** | PO (§8) |
| #5 model selection, F4 assignment | **Tech/privacy** | unassigned (D-5, "before M3") |
| #6 scrub protocol, run-package controls | **Privacy owner** | PO (A11) |
| #12 run-to-run compatibility | **Tech lead** | "build" (A15) |

Three specialist roles quietly collapsed into PO or a placeholder. The PRD is the artifact where that collapse should be visible and costed, and it isn't.

**Fix:** name the humans, or state plainly that PO + Claude Code is the entire build team and that "tech lead"/"privacy owner" are roles PO wears — then re-check whether the six-week plan survives that admission. It may not, which is the point of writing it down.

### RT-8 · Thresholds freeze at M3 before corpus facts are known at M4 *(high)*

§8: thresholds freeze at M3 (Aug 22), before calibration results are viewed. §10: D-1 (FS corpus facts — volume, date range, format) resolves "before M4 ingest" (Aug 29).

So the thresholds that govern the first real run are frozen a week before anyone knows how big the corpus is or what it looks like. Per RT-5, several thresholds are meaningless without that number.

Worse, it stacks with risk 2: if the corpus turns out unusable, that is discovered on ~Aug 27, with M5 (first real run, Sept 8) eleven days out and the demo eighteen.

**Fix:** move D-1 forward — corpus facts are a phone call, not a milestone. Make it due **before M1**, and make "FS corpus confirmed fit / not fit" an explicit gate with a fallback path that has its own milestone. Freezing thresholds against an unknown corpus is pre-registration theatre.

---

## 3 · The triage doesn't triage

### RT-9 · Everything expensive ships; everything cheap is deferred *(high)*

§7 defers seven items. Look at what they cost: a subset of paraphrase invariance, a 3-level loudness scale instead of a curve, a sampled drift pass instead of full-width, a stub swap instead of the RevOps SME's, a spec deferred to first repeat run. These are the inexpensive items.

Now look at what is *not* deferred and must be built by Sept 15 by one person:

five of six validation tiers · calibration corpus generated via a second-lab model · full scrub pipeline with NER and a sampled human audit · PDF **and** self-contained HTML with click-through evidence · run manifest · threshold register · sponsor decision log · two rubrics + a mini-rubric · mechanism discharge on every finding · coverage, residual clustering (frontier-LLM), saturation reporting · the full-vs-10% self-test with a predeclared comparison spec · drop log · escape audits · label self-agreement · split-half · null controls · second-model adjudication.

That is not a triaged v1. It's the full design with the trim removed.

**Fix:** triage something that hurts. Candidates, in order of cost-to-value at demo:

- **The HTML evidence companion.** Expensive (self-contained, click-through, inherits access controls). A PDF plus a live query against the SQLite store demos falsifiability just as well to one external party. Defer with trigger: *first engagement deliverable.*
- **Mechanism discharge as an automated pipeline check.** For a 5-item rubric it can be a manual analyst step with the same output marking. Defer the automation, keep the discipline.
- **Second-model adjudication every run** → adjudication on the calibration run and the first real run only, sampled.
- **Sponsor decision log** → follows RT-4's ruling.

Then re-check: does the remainder fit eight days to M1?

### RT-10 · The cut rule has no floor, and below the floor the product's claim is untestable *(medium)*

"Cut from the bottom of the rubric (fewer items), never the spine, the evidence gate, the honesty tier, or the self-test." Good instinct, wrong shape. The mini-rubric is already 3–5 items. Below ~3 items you cannot measure a distribution, a rank, or a tail — **the corpus claim becomes untestable, which means the demo proves the plumbing and nothing else.**

**Fix:** state the floor. "Below N rubric items the run cannot test the corpus claim; that is a milestone failure, not a cut." Pick N with the self-test in mind — you need enough items that rank and tail behaviour exist to differ between the sample and the whole.

---

## 4 · Drift from the design record

### RT-11 · The legal-review qualifier was dropped *(high — the only real rollback found)*

Design record §10: *"PIPEDA is the Canadian MVP design baseline, **subject to qualified privacy/legal review**; the architecture is a posture, not a compliance certification."*

PRD R-PII-3: *"PIPEDA is the design baseline; architecture ≠ certification."*

The qualified-review clause is gone, and no legal or privacy review is assigned to anyone in §4 or §6. The PRD keeps the modest half of the ruling (not a certification) and drops the half that creates an obligation. This is exactly the quiet-softening pattern the Input Pack exists to catch.

**Fix:** restore the clause in R-PII-3 and add a line item in §6 — who reviews, by when, gating what. Even "PO obtains a qualified read before the first engagement corpus, not before the test corpus" is a decision; silence is not.

### RT-12 · The PRD cites a design-record version that doesn't exist, and points at a second copy *(high)*

Header: *"Governing design record: `CIX_BRAINSTORM_OUTPUT_2026-07-31.md` **rev 2.1** (this repo, `docs/`)."*

The file's title and changelog both say **rev 2**. Either 2.1 exists somewhere unreferenced, or the number was invented. And "this repo, `docs/`" implies a copy inside `Projects_gh/CIX`, while the canonical file lives in `CLAUDE OUTPUTS/agentic-build/cix/`. **Two copies, no stated canonical, in a governance system whose entire premise is knowing which document wins.**

**Fix:** fix the version string; declare one canonical location and make the other a pointer (or a synced copy with the sync direction stated). This is small to fix and expensive to leave.

### RT-13 · §12 contains no acceptance criteria *(high)*

*"The design record §16 list is normative, verbatim, and testable at M5."* Verbatim to *what*? It isn't reproduced. So the PRD's acceptance section is a pointer plus a demo-day definition of done — and per RT-12 the pointer names a phantom version. If the design record moves to rev 3, the PRD's acceptance criteria change silently and nobody signs off.

The plan stage decomposes from the PRD. Handing it a reference instead of a list means the criteria can be lost in one hop.

**Fix:** inline all 13 criteria with IDs (AC-1…AC-13), each mapped to the milestone that proves it. "Don't restate rationale" is right; "don't restate the pass/fail list you're being measured against" is not.

### RT-14 · The one hard gate has no requirement ID *(high)*

Evidence integrity is described across every ancestor document as **the sole hard pass/fail gate**. In the PRD it appears as a goal (§2 goal 2) and by implication in R-IDX-3 (content hash) and R-IDX-7 (drop log). **There is no `R-EVD-*` requirement stating the gate itself**: every quote resolves to a snippet ID, string-matches the stored scrubbed evidence, every quantitative claim reproduces from the rollup, failures are dropped rather than flagged.

Same defect, smaller: the sponsor decision log (design record §16, final bullet) has an artifact (A14) but no requirement.

The plan stage decomposes from §3. Anything not in §3 can be dropped without violating the PRD.

**Fix:** add `R-EVD-1` through `R-EVD-3` for the gate, and a requirement for the decision record. Then run a coverage check: every design-record §16 criterion should map to at least one R-ID.

### RT-15 · Goal 3 promises more than the triage delivers *(low)*

§2 goal 3 — "all four must hold at demo" — says a catalogue change regenerates the priced view. §7 defers the SME swap to a "stub-variant catalogue swap." The stub swap does prove the mechanism, so the substance is fine; the sentence just claims a stronger artifact than will exist.

**Fix:** one clause — "proven with a stub-variant catalogue; the SME swap becomes the recorded proof when it lands."

---

## 5 · What's missing entirely

- **Cost.** D-11 puts a cost envelope in the open register at M1, but no figure appears anywhere, no estimate of frontier spend for the FS corpus at unknown scale, and no requirement that a run stay inside a budget. Two frontier models, a full corpus, a 10% re-run, sampled adjudication, and multi-seed self-tests — this is the line item most likely to surprise a self-funded build.
- **A real fallback path.** Risk 2 disposes of "FS corpus turns out unusable" in one clause. Given RT-8's sequencing, this is arguably the *most likely* bad outcome. It deserves: a decision date, a named alternative corpus, and a demo shape that doesn't require real data.
- **The demo audience.** "External demo (5.1j-1)" — to whom, and what do they need to see? §12's definition of done helps, but an unnamed audience is the same defect as the missing sponsor.
- **Availability assumption.** Hours per week. Every date depends on it; it appears nowhere.

---

## 6 · Priority fix list for the next turn

**Must fix before ratification:**

1. RT-1 / RT-2 / RT-3 — re-derive T-SST, T-CAL, T-NULL so the abandon triggers can actually fire. *(This is the review's headline.)*
2. RT-4 — rule on the sponsor: recruit one with a date, or mark the decision test post-MVP and restate the demo success condition.
3. RT-6 / RT-7 — state hours-per-week and the real build team; re-baseline M1 against both.
4. RT-14 — add `R-EVD-*` for the hard gate; coverage-check §3 against design record §16.
5. RT-9 — cut something expensive; the current triage doesn't buy schedule.

**Fix in the same pass (cheap, high leverage):**

6. RT-8 — move D-1 (corpus facts) before M1; add a fit/no-fit gate with a fallback milestone.
7. RT-5 — commit a v1 corpus scale; give every threshold a minimum sample size and an "insufficient power" behaviour.
8. RT-11 — restore the qualified privacy/legal review clause and assign it.
9. RT-12 — fix the version string; declare one canonical location for the design record.
10. RT-13 — inline the acceptance criteria as AC-1…AC-13, mapped to milestones.
11. RT-10 — state the rubric-item floor below which the corpus claim is untestable.
12. RT-15 — one clause on the stub-variant swap.

**Add:** cost envelope with a figure · fallback path with a date · named demo audience.

---

## 7 · What survives the attack

Stated plainly, because the above is one-sided by design:

- **Fidelity to the design record is high.** One rollback (RT-11) across ~35 ratified positions in the Input Pack's §2 ledger. The field split, polarity, the two sub-passes, the closed `unit_of_count` enum, grid-not-scalar, author-order ≠ run-order, catalogue-upstream-of-priced-view-only, the drop log, logical-content equality, the coverage denominator scheme — all correctly carried. The precedence apparatus worked.
- **The requirement-ID structure is the right form**, and stable IDs with `(D§n)` back-pointers is exactly how a PRD should reference a design record it must not restate.
- **The cut rule's instinct is correct** — protect the spine, the gate, the honesty tier, the self-test; degrade breadth. It just needs a floor (RT-10) and needs to actually buy time (RT-9).
- **§7's defer-with-trigger table is the right mechanism** even though the contents are too cheap. Keep the shape, change the entries.
- **Milestone gates are testable**, not vibes ("logical-equality property test passes; gate drops a planted bad quote"). That's better than most PRDs manage.

The document's problem is not that it's wrong. It's that it's optimistic in exactly the places where the design record spent its effort building pessimism in — and the design record's pessimism is the product's main claim to credibility.

## Changelog

- **2026-07-31** — Created as an adversarial review of `CIX_PRD_v1_2026-07-31.md`, checked against brainstorm output rev 2 and the PRD Input Pack. — Claude (Cowork)
