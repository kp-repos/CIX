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
| Build | **G3 complete.** Calibration passed on a second-lab-generated corpus: **holdout T-CAL 6/6 pathologies pass**, **T-NULL 0/100** false reports (floor 4/100), 1 dev cycle of 3 (0 detector revisions). Sales rubric A8 v1.1.0 (10 items); thresholds frozen before results (R-VAL-6, auditable in git); F4 audit seat recused in code on every split. Next gate: G4 (service rubric + catalogue join + scrub) |
| Stack | Python 3.12 · uv · pytest · pydantic v2 · PyYAML · SQLite |

## Documents

| Doc | Role |
|---|---|
| [`docs/CIX_PRD_v1_2026-07-31.md`](docs/CIX_PRD_v1_2026-07-31.md) | **The build contract** (v1.2, ratified). Self-contained requirements, scope matrix, gate sequence, threshold protocol, acceptance matrix |
| [`docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md`](docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md) | **Governing design record** (rev 2.3). Rationale and ratified rulings |
| [`docs/superpowers/plans/2026-07-31-g1-deterministic-spine.md`](docs/superpowers/plans/2026-07-31-g1-deterministic-spine.md) | **G1 implementation plan** — 12 TDD tasks building the deterministic spine (no model calls) |
| [`docs/superpowers/plans/2026-07-31-g2-thin-slice.md`](docs/superpowers/plans/2026-07-31-g2-thin-slice.md) | **G2 implementation plan** — 14 TDD tasks; first model calls, corpus→report in one command |
| [`docs/superpowers/plans/2026-08-01-g3-calibration.md`](docs/superpowers/plans/2026-08-01-g3-calibration.md) | **G3 implementation plan** — 11 tasks; sales rubric (A8), calibration corpus (A7), threshold freeze, second-lab seat, calibration runs |
| [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md) | **Calibration operations guide** — decisions of record, the configuration surface (every knob + when to change it), and the re-run procedure for each build iteration |
| [`docs/superpowers/plans/ROADMAP.md`](docs/superpowers/plans/ROADMAP.md) | **G3–G6 roadmap** — logic sketch of the remaining gates (calibration → assembly → real run → demo) |
| [`docs/reference/`](docs/reference/) | Vendored planning record: baseline spec, PRD input pack, swap catalogue schema, opportunity library, and adversarial reviews (`reviews/`) |

## Governance

- **This repository is self-contained** — every document the PRD depends on lives here (`docs/` normative, `docs/reference/` background). No external folders are dependencies.
- The design record governs; the PRD adds requirements, owners, and gates without silently changing rulings. Any PRD-ratified change to a design ruling is back-propagated to the design record in the same pass.
- People appear by role (Product Owner, RevOps SME, Commercial Principal, Data Provider) — see the PRD's roles table (§0.2).
- Build posture: narrowest end-to-end spine that can demo, MVP in a controlled environment, no calendar pressure — a dependency-ordered gate sequence (G0–G6) run as cycles allow.

## Next action

G1, G2, and G3 are complete — the instrument is calibrated (holdout 6/6 T-CAL, 0/100 T-NULL, thresholds frozen before results). Next gate is **G4 — assembly**: author the service rubric (A9), which reuses `load_rubric` + the persisted label artifact unchanged (AC-6 zero-code-swap proof) and grows `paraphrases_v1.yaml` under a `rubric_version` bump; wire the catalogue join / priced view; build the scrub pipeline for the real FS corpus. The calibration corpus is now permanent validation infrastructure (D§10) — re-run after any material detector change (see [`docs/G3_calibration_operations.md`](docs/G3_calibration_operations.md)); T-CAL/T-NULL values move only with a versioned register change and changelog entry (R-VAL-6). G0's FS-corpus items feed G4.
