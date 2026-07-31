# CIX Brainstorm Output — Review Notes · 2026-07-31

**Purpose:** analysis pass over `CIX_BRAINSTORM_OUTPUT_2026-07-31.md`, input to the PRD pre-cook (PO will merge with other analysis).
**Reviewed against:** `CIX_BRAINSTORM_BRIEF_2026-07-31.md` · `CIX_POC_B_Sniffer_Scope_v2.md` · `CIX_Swap_Catalogue_v0.md` · `CIX_Opportunity_Library_v1.md` (ref check only).
**Verdict:** structurally sound, PRD-ready with the fixes below applied. No ruling contradicts a lock or an upstream doc; all six review findings are gaps/ambiguities, not errors.

---

## 1 · What checked out clean

- **Agenda coverage:** brief §6 items 1–8 all worked, in order, each landing ratified decisions. Nothing skipped.
- **Cross-references:** RO-1–RO-5, CX-1–CX-4, A21J-07 all resolve in the Opportunity Library.
- **Lock discipline:** all four lock interactions flagged and ruled (§9) rather than silently reopened — recall/drop, effort×outcome, sales-first, frontier-throughout. Author-order-vs-run-order resolution is consistent everywhere it appears (§0.3, §2, §9).
- **Internal consistency:** `unit_of_count` no-cross-sum rule holds between §2 (declaration) and §6 (priced plays grouping); drop log (§4) correctly discharges the recall-vs-silent-drop tension; validation cost O(1) claim (§8) is consistent with every audit being fixed-size sampled (§5).
- **The strongest moves of the session**, worth carrying into the PRD's framing prose: unblocking the rubric via the priced-view-only ruling (§0.1 — kills the SME critical path), the six-tier ground-truth-free validation architecture (§5), and the sample self-test that turns the value proposition into an emitted number (§8, trigger 2).

## 2 · Findings (fixed or flagged in the doc)

**F1 — Polarity silently dropped.** `polarity` is core in scope v2 and the brief ("one mechanism, two polarities"; §6's "What's working" output depends on it), but §2's rubric design never mentions it, and the §1 field split re-defines the item structure without stating what remains. Under the doc's own convention ("ratified unless marked open"), silence reads as deletion. **Fix applied:** explicit post-split item structure row in §2, restating polarity as carried (settled upstream, not reopened in session). *Confirm this matches your recollection of the session — if polarity was actually reconsidered, that's a ruling to record, not a restatement.*

**F2 — Remedy-less findings have no grid home.** §1 rules findings without remedies print; the §6 leverage grid places findings by effort-band × outcome-band — both of which now live in the catalogue and only attach via `swap_ref`. An unjoined finding has neither coordinate. Needs a rule (likely a "no known remedy yet" shelf adjacent to the grid — it's also honest marketing for the SME enrichment pass). **Flagged as open q #11.**

**F3 — Residual clustering mechanism undefined at v1 scale.** §5's honesty tier headlines "residual characterized into these clusters" *every run*, but §8 parks embedding-based residual clustering in the 100K/v1.5 carve-out. At tens–hundreds scale something else must produce the clusters (frontier-LLM grouping over unmatched snippets is the obvious candidate and is consistent with frontier-throughout). **Flagged as open q #10.**

**F4 — Second-lab model wears two hats.** §5 seats a second-lab model as auditor; §7 uses a second-lab model as plant generator. If they're the same model, the auditor may recognize its sibling's plants during calibration runs, flattering exactly the audit that's supposed to be independent. Cheap rule: audit seat never adjudicates calibration corpora its generator sibling produced. **Folded into open q #5.**

**F5 — Sales-side realism donor missing.** CFPB narratives (§7) donate FS *service*-failure language. The sales/outbound rubric — authored first, calibrated first per the §8 spine — has no named realism donor for its plants. Either name one or rule explicitly that sales plants fly solo. **Flagged as open q #12.**

**F6 — Coverage denominator undefined.** "Rubric accounts for X% of volume" — volume in which unit? Snippets, interactions, or per-`unit_of_count`? The number is a headline (§5) and an abandon-trigger input, so the definition is load-bearing, not a tuning detail. **Folded into open q #6.**

**Also fixed:** header now carries a baseline note (scope v2 survives unchanged except rubric item structure, output section order, validation design) so the PRD writer doesn't misread a deltas record as the full spec; §6 now states its section order supersedes scope v2 §4.

## 3 · PRD pre-cook guidance

- **Structure is nearly free:** §11's eight mandated artifacts + §8's sequencing = the PRD's deliverables and milestones sections almost verbatim. §10 (now 12 items) = the open-issues register. §9 = the constraints section.
- **Three decisions the PRD must make** (can't stay open past plan stage): F3's v1 residual mechanism, F2's grid shelf rule, F6's coverage denominator. The rest of §10 can carry forward as tracked items.
- **One thing the PRD needs that no source doc has:** acceptance criteria per pipeline stage. The brainstorm produced them implicitly (byte-identical index build, zero-code rubric load, evidence-gate string match, fixed-size audits) — the PRD should surface them as a testable list; they're scattered across §2, §4, §5.
- **Scope-v2 supersession:** when the PRD lands, banner scope v2 the way v1 was bannered, pointing here — three docs deep, the "which doc governs" question is already expensive.

## Changelog

- **2026-07-31** — Created as the review companion to the brainstorm output, ahead of PRD drafting. — Claude (Cowork)
