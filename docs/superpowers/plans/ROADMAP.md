# CIX Build Roadmap — G3–G6 Logic Sketch

**Status:** high-level overview, not an implementation plan. The G1/G2/G3 plans in this directory are executable; G4–G5 plans get written as each prior gate lands — their interfaces derive from the shipped code, their contents from G0 corpus facts and PO-authored artifacts (rubrics, calibration spec). This document records the *logic* of each remaining gate so the shape of the whole build is visible now.

**Progress:** ✅ G1 (deterministic spine) · ✅ G2 (thin end-to-end slice) · ✅ **G3 (calibration — holdout 6/6 T-CAL, 0/100 T-NULL, 2026-08-01)** · ✅ **G4 (assembly — capability subset, 2026-08-02; scrub + A11, catalogue/priced + A5, A9 service rubric, swap proofs AC-6/AC-7, four-layer self-test + A10, differential tooling; T-SST + T-DIFF frozen)** · ▶ **G5 next** (first real run), gated on the FS corpus (OD-1) + a thin scrub+ingest / differential-construction follow-on. Executed detail lives in `2026-08-02-g4-assembly.md`, the design spec, and the PRD changelog.

**Source of truth:** `docs/CIX_PRD_v1_2026-07-31.md` (v1.2, ratified) — gate table §5, thresholds §6, self-test §7, triggers §8. This sketch adds nothing normative.

---

## G3 — Calibration: prove the instrument can measure *anything* before pointing it at real data

**Core logic:** G2 proved the plumbing moves; G3 proves the needle means something. Manufacture a corpus where the truth is known, check the instrument recovers it — and, just as important, check it reports *nothing* where nothing was planted.

**Authoring (PO — the bulk of the gate):**
- **Sales rubric v1 (A8, ≥8 items)** — first evaluable-floor rubric, drafted from RO-1–5 + catalogue seeds. Generic by ruling; corpus-adaptation pass is a named later step.
- **Calibration corpus spec (A7)** — planted pathologies with known magnitudes at three loudness levels (loud / moderate / camouflaged), plus a **held-out null set** containing zero of each target pathology.

**Code (small — mostly harness):**
- **Second-lab client** — same `ModelClient` protocol, different vendor (account from G0; model chosen at OD-2). Two jobs: *generate* the calibration corpus (collusion-breaking: the generator sees pathology descriptions, never rubric text) and sit in the sampled audit seat. **F4 rule enforced in code:** the audit seat never adjudicates corpora its sibling generated.
- **Calibration scorer** — planted truth vs. recovered counts (absolute + relative error), mechanism attribution scored separately, detection-by-loudness table.

**Freeze choreography (must not be botched):** T-CAL, T-NULL, T-PARA freeze **before** the first calibration run, with a dev/holdout split — revision cycles see dev fixtures only; **one** predeclared holdout evaluation at the end. T-ITER's 3-cycle budget starts at the first run.

**Exit / failure:** calibration numbers vs. pre-frozen gates. **Abandon trigger 1 becomes live here** — if after the T-ITER budget the holdout numbers are still outside T-CAL, or nulls breach T-NULL, the honest outcome is stopping, not tuning. Est. spend ~$60–200.

## G4 — Assembly: everything the real run needs, proven on the way in

**Core logic:** the staging gate — every mechanism the real run depends on gets proven here on cheap data, so G5 contains no first-times except the corpus itself.

**Authoring:**
- **FS service rubric (A9, ≥8 items)** — CX-1–4 spine, shaped to what the corpus call (OD-1) revealed.
- **Stand-in catalogue v0.1 (A5)** — pencilled bands, everything marked inferred.
- **Self-test spec (A10)** — seeds, metrics, tolerances, minimum evaluable size; **T-SST frozen here**, before any comparison exists.
- **Differential variant design** — 2–3 perturbations of the scrubbed FS corpus (delete a known subset, duplicate repeat-chains, splice known instances), each with its expected delta; **T-DIFF frozen with the design.**

**Code (three real modules):**
- **Scrub pipeline + A11 protocol** — deterministic patterns + NER, salted-hash pseudonymization (chain linkage survives, identity doesn't), sampled human audit. Runs on the FS data even though it's cleared — the capability *is* the point.
- **Catalogue join (Pass B)** — `swap_ref` join, unit-compatibility validation, leverage grid + shelf, evidence tiers in output. First appearance of the priced view.
- **Two swap proofs, run as acceptance tests:** the service rubric loads with **zero code changes and reuses the persisted label artifact** (the R-IDX-5 keying from G2 pays off); a stub-variant catalogue swap regenerates the priced view **without re-running detection**.

**Exit:** swap tests green, privacy gate satisfied, FS corpus scrubbed and ingested, every G5-governing threshold frozen. After G4, nothing about G5 is improvised.

## G5 — The first real run: everything fires at once, and the claim gets measured

**Core logic:** almost no new code — G5 is *execution* of machinery that has individually passed. Three measurements come back; they are the reason the project exists:

1. **The run itself → O2:** a fully gated artifact from real data — every quote string-matched, every count recomputed, drop log populated, coverage + residual clusters + saturation headlined.
2. **The differential runs:** does the instrument track known injected deltas on *real language*? (Calibration proved it on synthetic; this is the honest version.) Breach = abandon-trigger-1 input.
3. **The self-test → O3:** full corpus vs. seeded 10% samples under the frozen A10 protocol, emitting `material-advantage` / `no-material-advantage` / `not-evaluable`. **The corpus claim's verdict.** `no-material-advantage` on an evaluable run fires abandon trigger 2 — recorded even though nobody wants to see it.

**Also produced, unused:** the sponsor decision-log template (A14) — the decision test is post-MVP by ruling. Est. spend ~$120–370 (run + differentials).

## G6 — Demo pack (thin; likely a checklist, not a plan)

Demo narrative + rehearsal, audience named (OD-6), PDF + live store query as the falsifiability demo, and the honesty rule enforced one last time: the artifact **labels its own outcome level** — if the FS corpus fell through and the demo runs on the calibration corpus, it says O1-only, out loud.

---

## The shape across the gates

Code shrinks, authoring grows, stakes rise: G3 is mostly PO judgment artifacts plus a scorer; G4 is proofs and staging; G5 is nearly pure execution against pre-frozen gates. The design's discipline converges on one property: **by G5, every number that could kill the project was defined before anyone saw data that could influence it.**

| Gate | Code weight | Authoring weight | Spend est. | Kill-switch exposure |
|---|---|---|---|---|
| G3 | Light (client + scorer) | Heavy (rubric, corpus spec) | ~$60–200 | Trigger 1 goes live |
| G4 | Medium (scrub, Pass B, swap tests) | Heavy (service rubric, catalogue, specs) | Dev only | Freezes complete |
| G5 | Near zero | None | ~$120–370 | Triggers 1 + 2 measured |
| G6 | Near zero | Demo narrative | — | Honest labeling only |
