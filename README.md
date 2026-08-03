# CIX — Customer Intelligence Module

CIX ingests an organisation's customer-facing interaction record (call transcripts, email, chat, field notes) and produces an **auditable, reproducible decision artifact**: what's working, where it's failing (counted), where the greatest leverage sits (effort × outcome), and what it's worth (per-play indicative opportunity bands). The unproven claim — measured by every run — is that whole-corpus analysis yields decision-relevant completeness, frequency, and rank that a sampled read cannot.

**Private repo. MVP in a controlled environment, pre-build.**

## Pipeline

```
ingest → normalize → index → classify → aggregate → synthesize → validate → report
                       │         │
                       │         └─ two persisted passes: schema labels (rubric-independent),
                       │            rubric hits — a rubric swap re-runs only the second
                       └─ deterministic snippet store (SQLite): every downstream claim
                          resolves to a snippet ID; provenance is structural, not requested
```

Four independently versioned knowledge artifacts, all plain-language config: **index tag vocabulary** · **label schema** · **rubric** (what a run hunts) · **swap catalogue** (known remedies). One hard gate: **evidence integrity** — every quote string-matches its source, every number recomputes from the store, failures are dropped and drop-logged.

## Status

| | |
|---|---|
| Design | Brainstorm output **rev 2.3** — ratified |
| PRD | **v1.2 RATIFIED** 2026-07-31 (satisfies KR 5.1j-2) |
| Build | **G4 complete.** Assembly staging gate shipped on synthetic/cleared data: scrub pipeline + privacy gate (A11, linkage survives), catalogue join + priced view (A5), FS service rubric (A9, 10 items), swap proofs (AC-6/AC-7), four-layer full-vs-10% self-test (A10), differential tooling (AC-16). **T-SST + T-DIFF frozen before any result** (R-VAL-6). Prior: G3 calibration holdout **T-CAL 6/6**, **T-NULL 0/100**. Next gate: **G5 (first real run)** — gated on the FS corpus (OD-1) + a thin scrub+ingest / variant-construction follow-on |
| Stack | Python 3.12 · uv · pytest · pydantic v2 · PyYAML · SQLite |

## Documents

| Doc | Role |
|---|---|
| [`docs/CIX_PRD_v1_2026-07-31.md`](docs/CIX_PRD_v1_2026-07-31.md) | **The build contract** (v1.2, ratified). Self-contained requirements, scope matrix, gate sequence, threshold protocol, acceptance matrix |
| [`docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md`](docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md) | **Governing design record** (rev 2.3). Rationale and ratified rulings |
| [`docs/superpowers/plans/2026-07-31-g1-deterministic-spine.md`](docs/superpowers/plans/2026-07-31-g1-deterministic-spine.md) | **G1 implementation plan** — 12 TDD tasks building the deterministic spine (no model calls) |
| [`docs/superpowers/plans/2026-07-31-g2-thin-slice.md`](docs/superpowers/plans/2026-07-31-g2-thin-slice.md) | **G2 implementation plan** — 14 TDD tasks; first model calls, corpus→report in one command |
| [`docs/superpowers/plans/2026-08-01-g3-calibration.md`](docs/superpowers/plans/2026-08-01-g3-calibration.md) | **G3 implementation plan** — 11 tasks; sales rubric (A8), calibration corpus (A7), threshold freeze, second-lab seat, calibration runs |
| [`docs/superpowers/specs/2026-08-02-g4-assembly-design.md`](docs/superpowers/specs/2026-08-02-g4-assembly-design.md) | **G4 design spec** — architecture + module map, phases, checkpoint/freeze choreography for the assembly gate |
| [`docs/superpowers/plans/2026-08-02-g4-assembly.md`](docs/superpowers/plans/2026-08-02-g4-assembly.md) | **G4 implementation plan** — 15 tasks; scrub + A11, catalogue/priced + A5, service rubric (A9), swap proofs, self-test (A10), differential; T-SST/T-DIFF freeze |
| [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md) | **Calibration operations guide** — decisions of record, the configuration surface (every knob + when to change it), and the re-run procedure for each build iteration |
| [`docs/superpowers/plans/ROADMAP.md`](docs/superpowers/plans/ROADMAP.md) | **G3–G6 roadmap** — logic sketch of the remaining gates (calibration → assembly → real run → demo) |
| [`docs/reference/`](docs/reference/) | Vendored planning record: baseline spec, PRD input pack, swap catalogue schema, opportunity library, and adversarial reviews (`reviews/`) |

## Governance

- **This repository is self-contained** — every document the PRD depends on lives here (`docs/` normative, `docs/reference/` background). No external folders are dependencies.
- The design record governs; the PRD adds requirements, owners, and gates without silently changing rulings. Any PRD-ratified change to a design ruling is back-propagated to the design record in the same pass.
- People appear by role (Product Owner, RevOps SME, Commercial Principal, Data Provider) — see the PRD's roles table (§0.2).
- Build posture: narrowest end-to-end spine that can demo, MVP in a controlled environment, no calendar pressure — a dependency-ordered gate sequence (G0–G6) run as cycles allow.

## Next action

G1–G4 are complete — the instrument is calibrated (holdout 6/6 T-CAL, 0/100 T-NULL) and the assembly gate has proven every mechanism the real run needs on synthetic data, with **T-SST + T-DIFF frozen before any result** (R-VAL-6). Next gate is **G5 — first real run**: run the service rubric (A9) on the scrubbed FS corpus under the full validation matrix, construct the predeclared differential variants, and execute the whole-corpus self-test (A10) — every G5-governing threshold is already frozen, so G5 is near-pure execution. It is blocked on two things: the **FS corpus landing (OD-1)**, and a **thin follow-on carried over from G4** (real scrub+ingest, differential-variant construction on real language, and the `cix self-test` / `cix differential` CLI glue). The calibration corpus remains permanent validation infrastructure (D§10) — re-run after any material detector change (see [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md)); all frozen threshold values move only with a versioned register change and changelog entry (R-VAL-6).
