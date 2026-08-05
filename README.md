# CIX — Customer Intelligence Module

CIX ingests an organisation's customer-facing interaction record (call transcripts, email, chat, field notes) and produces an **auditable, reproducible decision artifact**: what's working, where it's failing (counted), where the greatest leverage sits (effort × outcome), and what it's worth (per-play indicative opportunity bands). The unproven claim — measured by every run — is that whole-corpus analysis yields decision-relevant completeness, frequency, and rank that a sampled read cannot.

**Private repo. MVP in a controlled environment — build in progress. G1–G4 complete; G5 rehearsal + G6 demo tooling landed; an O1 demo is presentable now; the G5 first real run is gated only on the FS corpus (OD-1).**

## Pipeline

```
ingest → normalize → index → classify → aggregate → synthesize → validate → report
                       │         │
                       │         └─ two persisted passes: schema labels (rubric-independent),
                       │            rubric hits — a rubric swap re-runs only the second
                       └─ deterministic snippet store (SQLite): every downstream claim
                          resolves to a snippet ID; provenance is structural, not requested
```

Four independently versioned knowledge artifacts, all plain-language config: **index tag vocabulary** · **label schema** · **rubric** (what a run hunts) · **swap catalogue** (known remedies). One hard gate: **evidence integrity** — every quote string-matches its source, every number recomputes from the store, failures are dropped and drop-logged. The falsifiability surface is live: a read-only `cix query` resolves any published claim to its scrubbed source in seconds (R-OUT-2) — `--item` walks a finding's count back to the source interactions, `--quote` matches a pasted line to its snippet or fails closed.

## Status

| | |
|---|---|
| Design | Brainstorm output **rev 2.3** — ratified |
| PRD | **v1.2 RATIFIED** 2026-07-31 (satisfies KR 5.1j-2) |
| Build | **G4 complete.** Assembly staging gate shipped on synthetic/cleared data: scrub pipeline + privacy gate (A11, linkage survives), catalogue join + priced view (A5), FS service rubric (A9, 10 items), swap proofs (AC-6/AC-7), four-layer full-vs-10% self-test (A10), differential tooling (AC-16). **T-SST + T-DIFF frozen before any result** (R-VAL-6). G5 rehearsal complete (2026-08-03): synthetic FS-shaped service corpus (servicegen), `cix self-test` + `cix differential` shipped, full G5 path executed end-to-end, O1-labeled. **G6 demo tooling landed (2026-08-03):** `cix query` live evidence resolution, method page, demo runbook — the pipeline is **O1 demo-ready now**; a demo-prep pass also found and fixed a real evidence-sampling defect (synthesis never received snippet ranges, so rehearsal findings carried no quotes — fixed, prompt hash unchanged, numbers unaffected). Prior: G3 calibration holdout **T-CAL 6/6**, **T-NULL 0/100**. Next gate: **G5 (first real run)** — gated only on the FS corpus (OD-1) |
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
| [`docs/superpowers/specs/2026-08-04-business-briefing-report-design.md`](docs/superpowers/specs/2026-08-04-business-briefing-report-design.md) | **Business briefing design** — model-free presentation layer (`cix briefing`) rendering a persisted run for a commercial reader |
| [`docs/method.md`](docs/method.md) | **Method page** — one-page, non-technical "how it works and why you can trust it": pipeline, the one hard evidence gate, the six validation tiers, calibration results, and the O1/O2/O3 honesty ladder. Every claim cited to the PRD/design record |
| [`docs/demo_runbook.md`](docs/demo_runbook.md) | **O1 demo runbook** — the exact walkthrough on `runs/svc-run/`: narrate `report.pdf`, resolve a count to source live with `cix query`, show the gate fail closed, and read the honest O1 script |
| [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md) | **Calibration operations guide** — decisions of record, the configuration surface (every knob + when to change it), and the re-run procedure for each build iteration |
| [`docs/superpowers/plans/ROADMAP.md`](docs/superpowers/plans/ROADMAP.md) | **G3–G6 roadmap** — logic sketch of the remaining gates (calibration → assembly → real run → demo) |
| [`docs/reference/`](docs/reference/) | Vendored planning record: baseline spec, PRD input pack, swap catalogue schema, opportunity library, and adversarial reviews (`reviews/`) |

## Governance

- **This repository is self-contained** — every document the PRD depends on lives here (`docs/` normative, `docs/reference/` background). No external folders are dependencies.
- The design record governs; the PRD adds requirements, owners, and gates without silently changing rulings. Any PRD-ratified change to a design ruling is back-propagated to the design record in the same pass.
- People appear by role (Product Owner, RevOps SME, Commercial Principal, Data Provider) — see the PRD's roles table (§0.2).
- Build posture: narrowest end-to-end spine that can demo, MVP in a controlled environment, no calendar pressure — a dependency-ordered gate sequence (G0–G6) run as cycles allow.

## Next action

G1–G4 are complete — the instrument is calibrated (holdout 6/6 T-CAL, 0/100 T-NULL) and the assembly gate has proven every mechanism the real run needs on synthetic data, with **T-SST + T-DIFF frozen before any result** (R-VAL-6). The **G6 demo tooling has landed**, so an **O1 demo is presentable now**: `cix query` resolves any claim to its scrubbed source live, backed by `docs/method.md` and `docs/demo_runbook.md`, on the O1-labeled rehearsal artifact at `runs/svc-run/` (demo prep also fixed a real evidence-sampling defect — synthesis had been receiving no snippet ranges; the fix touches no config and leaves the prompt hash and all numbers unchanged). Next gate is **G5 — first real run**: run the service rubric (A9) on the scrubbed FS corpus under the full validation matrix, construct the predeclared differential variants, and execute the whole-corpus self-test (A10) — every G5-governing threshold is already frozen, so G5 is near-pure execution. The G4 follow-on's tooling half is done (G5 rehearsal, 2026-08-03): `cix self-test` and `cix differential` are shipped and the whole G5 path has run end-to-end on a synthetic service corpus (O1-labeled). G5 is now blocked only on the **FS corpus landing (OD-1)**; when it lands, the remaining slice is real scrub+ingest and running the same commands on real language. The calibration corpus remains permanent validation infrastructure (D§10) — re-run after any material detector change (see [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md)); all frozen threshold values move only with a versioned register change and changelog entry (R-VAL-6).
