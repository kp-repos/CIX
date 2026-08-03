# G4 — Assembly: Design Spec

**Status:** ✅ implemented — merged to `main` (PR #4), 2026-08-02 · **Date:** 2026-08-02 · **Owner:** PO
**Gate:** G4 (assembly) · **Source of truth:** `docs/CIX_PRD_v1_2026-07-31.md` v1.2 — §5 gate row, §6 freeze points (T-DIFF/T-SST), §7 self-test, §8 abandon/release gates, R-CAT/R-PRC/R-PII/R-VAL families, AC-6/AC-7/AC-16.
**Prior gate:** ✅ G3 (calibration) exited 2026-08-01 — holdout T-CAL 6/6, T-NULL 0/100.
**Roadmap logic of record:** `docs/superpowers/plans/ROADMAP.md` §G4.

---

## 1 · Purpose and framing

G4 is the **staging gate**: every mechanism the first real run (G5) depends on gets proven here on cheap/synthetic data, so G5 contains no first-times except the corpus itself. It is the project's largest gate by code weight — three real code capabilities (scrub, catalogue join, validation machinery), four PO authoring artifacts (A9 service rubric, A5 stand-in catalogue, A10 self-test spec, differential design), and two threshold freezes (T-SST, T-DIFF).

### 1.1 Scoping decisions (ratified in brainstorming, 2026-08-02)

Two decisions shape the whole plan:

1. **The FS (real) corpus is not in hand (OD-1 still open).** G4 therefore builds and freezes *all capability* on synthetic/cleared test data now. R-PII-4 explicitly authorizes this: "the scrub stage ships and runs even on cleared test data." The two exit items that hard-depend on the real corpus — *FS corpus scrubbed and ingested* and *differential variants constructed on real language* — move to a thin post-G4 follow-on that runs when the corpus lands. This honours the brainstorm ruling "the FS corpus is pursued in parallel; nothing waits."

2. **Build + prove the G5 execution machinery at G4.** The self-test harness (full-vs-10%, R-VAL-5/§7) and the differential-perturbation tooling (R-VAL-7) are written and proven on synthetic/calibration data *here*, not first-appearing at G5. This is what makes the roadmap's "G5 is almost no new code — execution of machinery that has individually passed" literally true. A10/T-SST and the differential design/T-DIFF are still frozen at G4.

### 1.2 What G4 does **not** touch

- The two-artifact keying (R-IDX-5: labels keyed without rubric; hits keyed by label-artifact + rubric) — already shipped in G2; G4 *consumes* it (the AC-6 swap proof is where it finally pays off).
- The evidence gate (R-EVD-1…3) — unchanged; Pass B priced claims flow through the existing gate.
- Pass A detection — R-ARCH-2 holds: remedy availability (Pass B) never suppresses detection.

---

## 2 · Architecture and module map

G4 adds **five new source modules** and touches **four existing ones**, slotting into seams the earlier gates left open. The only rubric-schema change is one optional field.

### 2.1 New source modules

| Module | Responsibility | Governs |
|---|---|---|
| `src/cix/scrub.py` | Deterministic patterns + NER + salted-hash pseudonymization; runs at ingest on any corpus (incl. cleared/synthetic); returns scrubbed `InteractionUnit`s + a scrub report | R-PII-1…4, A11 |
| `src/cix/catalogue.py` | Load A5 catalogue; `swap_ref` join; unit-compatibility validation; leverage grid + shelf; evidence tiers | R-CAT-1…5 |
| `src/cix/priced.py` | Assemble the priced view (indicative bands, no portfolio totals, multi-remedy = alternatives) from rollup × catalogue | R-PRC-1, R-OUT-1 |
| `src/cix/selftest.py` | Full-vs-10% harness: reseeded sample synthesis, four comparison layers, three output states | R-VAL-5, §7 |
| `src/cix/differential.py` | Perturbation ops (delete-labeled-subset / duplicate repeat-chains / splice known instances) + delta scorer vs predeclared T-DIFF | R-VAL-7, AC-16 |

### 2.2 Touched existing modules

- **`rubric.py`** — add optional `swap_ref: str | None = None` to `RubricItem` (R-RUB-1). Backward-compatible: the G3 sales rubric omits it and still loads. **This is the only schema change.** It does not break AC-6, because the loader already accepts arbitrary item content; the swap proof is about a *new config* loading with zero code changes, and this field is added once, before either rubric uses it.
- **`cli.py`** — insert `scrub` between `load_corpus` and `build_store` (scrub at ingest, R-PII-1); wire the `swap_ref` join + priced view into `_cmd_run` (flip the existing `catalogue_loaded` flag `render_report` already accepts). (`cix self-test` and `cix differential` subcommand wiring is deferred to G5.)
- **`report.py`** — populate the priced-play section from `priced.py` when a catalogue is loaded (the section already exists; today it renders the honest "no remedy loaded" shelf).
- **`manifest.py`** — replace the `privacy_gate="synthetic-fixture"` placeholder with the real scrub-audit status; add catalogue version to the four-artifact block.

### 2.3 Pipeline integration points (confirmed against shipped `_cmd_run`)

The current flow is `load_corpus → build_store → label_corpus → run_rubric → rollup → [validations] → synthesize → gate → manifest → render_report`. G4 inserts:

- **Scrub** between `load_corpus` and `build_store` — nothing unscrubbed ever reaches the store (R-PII-1). Sets `privacy_gate` for the manifest.
- **Catalogue join + priced view** after `rollup`/findings, before `render_report` — flips `catalogue_loaded` and supplies the priced section.
- **Self-test** and **differential** ship as **library modules** at G4 (`selftest.py`, `differential.py`), invoked programmatically and proven via tests. Their thin CLI execution glue (`cix self-test`, `cix differential`) is deferred to G5, where they run against the real corpus — the harness logic (the part that can fail) is proven here; wiring an already-tested function to a subparser is trivial glue, not a logic first-time.

### 2.4 Design invariant carried from G3

All new code is TDD'd offline against `ScriptedClient`; the only live model calls are opt-in tests that skip without a key. Scrub's NER defaults to **rules + a deterministic offline pass** so scrub is fully testable without a live call; a model-backed NER stage is an opt-in path. At most one new opt-in live test.

---

## 3 · Phases, checkpoints, and freeze choreography

One plan file (`docs/superpowers/plans/2026-08-02-g4-assembly.md`), internally ordered into five phases with **three PO ratification checkpoints** (P, A, B) — one more than G3, the extra being the privacy gate.

### Phase 1 — Privacy / scrub (A11) → **Checkpoint P**

`scrub.py` runs at ingest on every corpus (R-PII-4). Three stages:

1. **Deterministic patterns** — emails, phone numbers, and other regex-clear identifiers. Currency amounts, dates, and quantities are *kept* (they carry the measurable signal); names, orgs, and locations are flagged.
2. **NER pass** — catches residual person/org/location entities the patterns miss.
3. **Salted-hash pseudonymization** — linkage identifiers (participant handles, account refs) are salted-hash pseudonymized, **never deleted** (R-PII-2). The salt is recorded in the run manifest, so **chain/account linkage survives while identity does not** — the property that keeps `chain`/`account` unit items viable downstream.

Output: scrubbed `InteractionUnit`s + a **scrub report** (counts by entity type, sampled-audit rows per the A11 protocol). The manifest `privacy_gate` becomes a real status: `pass` / `audit-pending` / `fail`. A `fail` is a **release gate** (§8) — it stops the run, not the thesis.

**A11** (`docs/A11_privacy_protocol.md`) is the privacy threat model + the *predeclared* sampled-audit protocol (sampling rule, reviewer, sign-off). **Checkpoint P:** PO ratifies A11 before scrub output is trusted in any manifest.

*Error/edge behaviour:* a unit that fails to scrub (e.g. NER stage errors) is dropped + drop-logged, never passed through unscrubbed (R-PII-1 is absolute). Empty/whitespace segments after scrub are handled as the existing normalize path already handles them.

### Phase 2 — Catalogue + Pass B priced view

`catalogue.py` loads A5 (`configs/catalogue_v0_1.yaml`) and:

- **Joins** `rollup.items[*].swap_ref` → catalogue entries by `id`.
- **Validates unit-compatibility** — an incompatible unit join (e.g. an `occurrence`-unit item joined to a per-`account` value band) **fails validation, drops the priced claim, and writes the drop log** (R-CAT-3). Detection is untouched; only the price is withheld.
- **Builds the leverage grid** — effort-band × outcome-band; count tie-break within tier; Class D ("not ours") named in its corner (R-CAT-4).
- **Builds the shelf** — remedy-less findings on the "no known remedy yet" shelf, ranked by count within unit (R-CAT-4).
- **Carries evidence tiers** — confirmed-in-practice / candidate-substitute / none-yet (R-CAT-5), buyer-facing.

`priced.py` assembles the **indicative opportunity bands**: each band names its count-unit, currency, time horizon, per-unit basis, source + date, inferred/observed status, and evidence tier (R-PRC-1). **No portfolio totals anywhere** (ruling 6). A finding joining multiple remedies is displayed as **alternatives, never summed**. Pass B never suppresses Pass A (R-ARCH-2).

**A5** (`configs/catalogue_v0_1.yaml` + entries per `docs/reference/CIX_Swap_Catalogue_v0.md` §2 schema) ships with pencilled bands, every unverified entry marked **inferred with source** (R-CAT-2). Proven on synthetic hits + the stub catalogue.

### Phase 3 — Service rubric A9 + swap proofs → **Checkpoint A**

Author **A9** (`configs/service_rubric_v1.yaml`, ≥8 items, CX-1…4 FS-service spine, `swap_ref` populated, declares schema + tag-vocab versions). A9 is authored second but *runs first* on the real corpus (R-RUB-6) — G4 authors it; G5 runs it.

Two acceptance tests, run against a persisted G2/G3-style run:

- **AC-6** — swap the sales rubric → service rubric: the run **reuses the persisted label artifact** and creates a **new hit artifact**, with **zero code changes** (R-IDX-5 keying). This is the payoff of the G2 investment.
- **AC-7** — swap the catalogue (stub → variant): only the priced view regenerates; index / labels / hits untouched (R-ARCH-5).

**Checkpoint A:** PO ratifies A9 + A5 (mirrors G3 Checkpoint A).

### Phase 4 — Self-test harness + A10 → (part of Checkpoint B)

`selftest.py` implements §7:

1. Freeze eligibility, rubric, catalogue version, thresholds, highlight rules, and metrics before the comparison.
2. **Minimum evaluable corpus size** predeclared; below it → `not-evaluable`.
3. **N predeclared seeds** (working hypothesis: 5). For each 10% sample: regenerate aggregation, ranking, highlights, residuals, and bands **from that sample's records only** — no full-corpus leakage into sample synthesis.
4. Compare within compatible units only; four separated layers: distribution distance · rank/top-k · opportunity-band movement · highlighted-action difference.
5. Rare-driver claims count only if they clear min full-corpus support + evidence-quality + stability + explicit action consequence.
6. Report **the fraction of seeds** showing each material difference.
7. Output state: `material-advantage` / `no-material-advantage` / `not-evaluable` (R-VAL-5) — never a spurious pass.

**A10** (`configs/selftest_spec_v1.yaml` + `docs/A10_selftest_spec.md`) is the parameter set (resolves OD-10). **T-SST** freezes its protocol parameters.

### Phase 5 — Differential tooling + design → completes **Checkpoint B (the freeze)**

`differential.py` implements the three perturbations as pure functions over a scrubbed + labeled corpus, each emitting the variant + its expected delta:

- **Delete a known-labeled subset** — expected: the corresponding counts drop by the deleted magnitude.
- **Duplicate repeat-chains** — expected: chain-unit counts rise per the dedup declaration.
- **Splice known instances** — expected: targeted item counts rise by the spliced magnitude.

`configs/differential_design_v1.yaml` predeclares which perturbations, expected deltas, and per-variant tolerances. **T-DIFF** freezes with the design. Proven on synthetic (AC-16 mechanism dry-run): apply a perturbation → re-run detection → confirm the reading tracks the injected delta within tolerance.

### Freeze choreography (R-VAL-6) — **Checkpoint B**

**Checkpoint B is the freeze.** PO ratifies the T-SST and T-DIFF register rows. The ratification commit must precede any harness result that could bias those thresholds. Therefore the **order within G4** is:

1. Build the self-test + differential harnesses against **fixed `ScriptedClient` fixtures** whose numbers are predetermined and pathology-free (no threshold-setting observation occurs).
2. Author A10 + the differential design.
3. **Freeze** (Checkpoint B commit).
4. *Only then* run the synthetic mechanism dry-runs that produce "real-ish" numbers.

This mirrors G3's "nothing generates or scores a live artifact until the freeze commit exists." The key difference from G3: T-SST and T-DIFF's first *gating* result is the **G5 real run**, so G4 carries **no in-gate pass/fail** against them — G4 proves the mechanism and freezes the gate; G5 measures against it.

---

## 4 · Exit criteria

All provable on synthetic/cleared data:

- Scrub pipeline runs at ingest; **A11 ratified**; `privacy_gate` emits a real status; sampled-audit protocol executes (AC-2 mechanics on cleared data).
- Catalogue join + priced view green; unit-incompatible joins fail validation + drop-log; **no portfolio totals** anywhere (AC-9, AC-14 mechanism).
- **AC-6** (rubric hot-swap, label reuse, new hit artifact) and **AC-7** (catalogue swap → priced view only) green.
- Self-test harness produces all three states on synthetic corpora sized above/below the min; **T-SST frozen**.
- Differential tooling tracks predeclared deltas on synthetic (**AC-16 mechanism**); **T-DIFF frozen** with the variant design.
- All G5-governing thresholds frozen (Checkpoint B commit is the freeze); **A9 + A5 + A10 + A11 ratified**; full test suite green.

### 4.1 Deferred to the post-G4 follow-on (runs when OD-1 resolves)

A thin plan, executed when the FS corpus lands: FS corpus **scrubbed and ingested** on real data; differential variants **constructed** from the real scrubbed corpus; the real privacy-gate `pass` in a real manifest. G4 proves every mechanism these need, so the follow-on is execution, not first-times.

---

## 5 · Testing and honesty

**Testing.** Per-module TDD against `ScriptedClient` (offline), following G3's pattern: `test_scrub.py`, `test_catalogue.py`, `test_priced.py`, `test_selftest.py`, `test_differential.py`, plus `test_swap_proofs.py` (AC-6/AC-7) and an extended `test_runconfig.py` for the two new threshold rows. At most one new opt-in live test (model-backed NER path), skipping without a key.

**Honesty / manifest.** Every G4 artifact stays **O1** (synthetic) — scrub, priced view, and self-test all run on synthetic/calibration data and are labeled as such; nothing here claims O2/O3. The manifest gains catalogue version + real privacy-gate status; the report method page notes the corpus is synthetic. This is the honesty rule the roadmap enforces to G6: the artifact labels its own outcome level.

---

## 6 · File manifest (additions to the shipped tree)

```
CIX/
├── configs/
│   ├── service_rubric_v1.yaml        # A9 — ≥8 items, CX-1–4 spine, swap_ref populated
│   ├── catalogue_v0_1.yaml           # A5 — stand-in catalogue, pencilled/inferred bands
│   ├── selftest_spec_v1.yaml         # A10 — §7 parameters (seeds, min size, metrics)
│   ├── differential_design_v1.yaml   # perturbations + expected deltas + tolerances
│   └── thresholds_v1.yaml            # (modify) v1.2.0 — add T-SST, T-DIFF rows
├── docs/
│   ├── A9_service_rubric.md          # A9 narrative + ratification record
│   ├── A10_selftest_spec.md          # A10 narrative
│   └── A11_privacy_protocol.md       # A11 threat model + sampled-audit protocol
├── src/cix/
│   ├── scrub.py                      # NEW — ingest scrub (R-PII)
│   ├── catalogue.py                  # NEW — swap_ref join + leverage grid + shelf
│   ├── priced.py                     # NEW — priced view assembly
│   ├── selftest.py                   # NEW — full-vs-10% harness
│   ├── differential.py               # NEW — perturbation ops + delta scorer
│   ├── rubric.py                     # (modify) add swap_ref? to RubricItem
│   ├── cli.py                        # (modify) scrub wiring + priced view (subcommand wiring deferred to G5)
│   ├── report.py                     # (modify) priced-play section
│   └── manifest.py                   # (modify) real privacy_gate + catalogue version
└── tests/
    ├── test_scrub.py
    ├── test_catalogue.py
    ├── test_priced.py
    ├── test_selftest.py
    ├── test_differential.py
    ├── test_swap_proofs.py           # AC-6 + AC-7
    └── test_runconfig.py             # (modify) T-SST, T-DIFF rows
```

## 7 · Sequencing summary

Phase 1 (scrub) → **Ckpt P (A11)** → Phase 2 (catalogue/priced) → Phase 3 (A9 + swaps) → **Ckpt A (A9 + A5)** → Phase 4 (self-test) + Phase 5 (differential) harnesses built against fixed fixtures → author A10 + differential design → **Ckpt B (freeze T-SST + T-DIFF)** → synthetic mechanism dry-runs → G4 exit doc pass.

**Next step after this spec is approved:** invoke the writing-plans skill to turn this into the executable, task-by-task G4 implementation plan.
