# G5 Rehearsal — Synthetic FS Corpus + CLI Glue: Design Spec

**Status:** 📝 designed — not yet implemented · **Date:** 2026-08-03 · **Owner:** PO
**Scope:** the thin post-G4 follow-on, run *ahead of* the real FS corpus · **Source of truth:** `docs/CIX_PRD_v1_2026-07-31.md` v1.2 — §2.1/§2.3 (outcome levels, synthetic = O1), §5 (G5 row + fallback), §6 (T-SST/T-DIFF already frozen), §7 (self-test), R-VAL-5/R-VAL-7, AC-16.
**Prior gate:** ✅ G4 (assembly) exited 2026-08-02 — scrub, catalogue/priced, A9 rubric, swap proofs, self-test + differential tooling all proven on synthetic data; **T-SST + T-DIFF frozen.**
**Roadmap logic of record:** `docs/superpowers/plans/ROADMAP.md` §G4 (the named "thin scrub+ingest / differential-construction follow-on") and §G5.

---

## 1 · Purpose and framing

G5 proper — the first real run — is blocked on the FS corpus landing (OD-1). This follow-on builds and proves **everything G5's execution path needs, on a high-fidelity *synthetic* service corpus**, so that when OD-1 resolves G5 is pure execution with zero first-times. It is a **path rehearsal, not the real run**: every artifact it produces is honestly labeled **O1** (synthetic → never O2/O3, PRD §2.3).

It closes the two carry-overs G4 explicitly deferred (G4 spec §4.1): the CLI glue that turns the `selftest.py` / `differential.py` modules into runnable commands, and the construction of differential variants + a self-test run on realistic (service-domain) language.

### 1.1 Scoping decisions (ratified in brainstorming, 2026-08-03)

Three decisions shape the whole plan:

1. **The synthetic FS corpus is high-fidelity, model-generated.** Not offline fixtures and not the existing sales calibration corpus — a service-domain corpus generated via the second lab, so the rehearsal exercises the A9 service rubric on service language. Total spend envelope for the follow-on: **~$25–80** (generation + base run + three full variant re-labels — R-IDX-5 keys labels by corpus hash, so each perturbed variant forces a fresh label pass; §9 discipline: PO accepts this envelope with this spec).
2. **`cix differential` re-runs the real instrument on each variant.** Observed readings come from `label → rubric hits → rollup` on each constructed variant (model calls), exactly as G5 will — not from recounting persisted hits. This also stress-tests detector stability on duplicated/spliced text.
3. **A separate `servicegen.py` module; `calgen.py` is untouched.** The calibration generator is permanent validation infrastructure (D§10) and stays frozen. Thread-aware, service-shaped generation lives in a new module that reuses calgen's *conventions* (firewall, truth registry, provenance) without importing its risk.

### 1.2 What this follow-on does **not** touch (YAGNI)

- **No re-calibration.** No new T-CAL / T-NULL on the service corpus — calibration already proved the instrument recovers planted truth (holdout 6/6, 0/100). Re-proving detection on synthetic data is not the goal.
- **No detection-accuracy scoring of the service corpus.** The truth registry exists only to *construct* a corpus that contains detectable instances of each differential-target item — not to grade recovery.
- **No threshold changes.** T-SST and T-DIFF are frozen (G4, R-VAL-6). This follow-on only *executes* against them and produces no new frozen numbers.
- **Not the real FS corpus.** OD-1 remains the standing top open item; the fallback path (PRD §5) is unchanged.

---

## 2 · Architecture and module map

Adds **one new source module** and **two new configs**, touches **`cli.py`** (three subcommands) and factors a detection helper out of `_cmd_run`. No changes to `selftest.py` or `differential.py` — their functions are already correct and unit-tested; this work only *wires* them.

### 2.1 New source module

| Module | Responsibility | Reuses (convention, not import) |
|---|---|---|
| `src/cix/servicegen.py` | Generate a synthetic FS-shaped service corpus: thread-aware slots (repeat-contact chains), single-pathology slots, clean slots; emit `corpus/`, `truth.json`, `provenance.yaml` | `calgen.py`'s firewall (item-id-only, R-VAL-2), truth/provenance shape, `ModelClient` protocol, `complete_json` |

### 2.2 New configs

| Config | Role |
|---|---|
| `configs/service_corpus_spec_v1.yaml` | Service-domain generation spec: pathologies mapping to **A9 item IDs only** (firewall), thread structure, service-register style guide, scale (~100 interactions) |
| `configs/selftest_spec_v1.yaml` (reused) | Frozen A10 — consumed unchanged |
| `configs/differential_design_v1.yaml` → **v1.0.1** | Frozen design, amended for machine-readability only: each variant gains a `target_item` field + selection params (delete count, splice copies). Tolerances, perturbations, and expected-delta semantics **unchanged** — a versioned register change with changelog line under R-VAL-6, PO-ratified. The alternative (hardcoding the target mapping in the CLI) would hide a frozen-artifact interpretation in code |

### 2.3 Touched existing module

| Module | Change |
|---|---|
| `src/cix/cli.py` | Add three subcommands (`generate-service-corpus`, `self-test`, `differential`); factor the Pass-A detection path (`label_corpus → run_rubric → rollup`) out of `_cmd_run` into a reusable helper so `_cmd_run` and `_cmd_differential` share one code path |

### 2.4 Design invariant carried forward

The self-test regenerates sample aggregation **from sample records only** (no full-corpus leakage — `selftest.py` docstring, §7.3). The CLI glue must not defeat this: `cix self-test` passes the full persisted hit list + all IDs to `self_test()`, which does the sampling internally. `cix differential` re-runs detection per variant against the same scrub+detect path `cix run` uses — no shortcut that would make the rehearsal dishonest.

---

## 3 · Components

### 3.1 `servicegen` — the synthetic FS corpus

- **Spec (`service_corpus_spec_v1.yaml`).** Pathologies each carry `maps_to_item` (an A9 item ID — never item text; firewall enforced by a `test_service_spec.py` disjointness test mirroring `test_calspec.py`), a firewall-safe `description`, and slot placement. A service-register `style_guide` (support/CX interactions — tickets, follow-ups, resolution/escalation — not sales). Scale: **~100 interactions** — at 60 the 10% self-test sample is 6 units and the layer comparisons go near-degenerate; ~100 gives a sample of 10, comfortably above the 40-interaction evaluable floor.
- **Differential-target coverage (hard requirement, not implication).** The spec MUST plant, and the truth registry MUST record: **≥6 `repeat_contact_unresolved` instances** (V1 needs a deletable known-labeled subset that leaves survivors), **≥2 genuine multi-interaction threads** (V2 duplicates one; a spare survives V1's deletions), and **≥3 `deterministic_request` instances** (V3 needs a flagged donor). Verified: the A9 rubric contains exactly these item IDs.
- **Thread-aware generation.** A new `thread` slot kind yields **N linked interactions** sharing one `thread_id`, generated with conversational continuity ("following up on my last call about…"), modeling repeat-contact chains. This is what `duplicate_chains` requires and what makes the corpus FS-shaped. Single-pathology and clean slots round out the mix.
- **Outputs (mirroring calgen).** `corpus/` (one JSON per `InteractionUnit`, `thread_id` set on chain members), `truth.json` (planted structure), `provenance.yaml` (generator lab/model, `gen_prompt_version`, prompt hash, spec version, firewall record).
- **CLI.** `cix generate-service-corpus --spec configs/service_corpus_spec_v1.yaml --out <dir>` — mirrors `generate-calibration`.

### 3.2 `cix self-test`

Mirrors `_cmd_calibrate`'s shape. **Inputs:** a **run dir** (output of `cix run` on the service corpus), `--spec configs/selftest_spec_v1.yaml`, and — to enable the `band_movement` layer — optional `--catalogue` + `--rubric` (supplying the `swap_ref` crosswalk). **Flow:** open the run store; read the hit list via `manifest["artifacts"]["hits"]`; gather all interaction IDs; call `self_test(all_ids, hits, spec, catalogue?, crosswalk?)`; write a `SELF-TEST` validation row into the store and `selftest_report.json`; print the state (`material-advantage` / `no-material-advantage` / `not-evaluable`) + `material_fraction` + `layers_compared`.

### 3.3 `cix differential`

**Inputs:** a **base run dir** (the service-corpus run), `--corpus <dir>` (the original corpus — the manifest records `corpus_hash` and `scrub_salt`, not a path, and the store does not hand back full `InteractionUnit`s), `--design configs/differential_design_v1.yaml` (v1.0.1, machine-readable targets), `--rubric`, optional `--catalogue`. For each of the 3 frozen variants (V1-delete, V2-duplicate, V3-splice):

0. **Reload + integrity-check.** Load the corpus dir, re-scrub with the manifest's persisted `scrub_salt` (pseudonyms reproduce deterministically), and **verify the recomputed `corpus_hash` matches the base run's manifest** — refuse to proceed otherwise. Guarantees the variants perturb exactly the corpus the base run saw.
1. **Select the target** using the design's `target_item` + selection params, from the base run's *actual persisted hits* ("known-labeled" = flagged by the instrument in the base run) and from `thread_id`: V1 = a subset of interactions the instrument flagged for the target item; V2 = a real repeat-contact thread; V3 = a flagged donor interaction.
2. **Construct the variant** via `delete_subset` / `duplicate_chains` / `splice_instances` (from `differential.py`), capturing the returned `expected` delta.
3. **Re-run the real instrument** on the variant via the shared detection helper (§2.3): `label_corpus → run_rubric → rollup` into a per-variant store under the output dir → observed count for the target item. Model calls; faithful to G5. (R-IDX-5: each variant's corpus hash differs, so each gets a fresh label artifact — this is the dominant spend, accepted in §1.1.)
4. **Score** `score_delta(expected, observed, tolerance)` against the variant's frozen `tolerance`; write a `T-DIFF` row per variant + `differential_report.json`.

### 3.4 The rehearsal run

Executed as the follow-on's proof (analogous to the G3 calibration runs), end to end:

```
cix generate-service-corpus --spec service_corpus_spec_v1 --out runs/svc
cix run runs/svc/corpus --rubric configs/service_rubric_v1.yaml --catalogue configs/catalogue_v0_1.yaml --out runs/svc-run --clearance "synthetic — O1 only"
cix self-test runs/svc-run --spec configs/selftest_spec_v1.yaml --catalogue configs/catalogue_v0_1.yaml --rubric configs/service_rubric_v1.yaml
cix differential runs/svc-run --corpus runs/svc/corpus --design configs/differential_design_v1.yaml --rubric configs/service_rubric_v1.yaml --catalogue configs/catalogue_v0_1.yaml
```

Manifest clearance records "synthetic"; the report and self-test/differential outputs say **O1-only, out loud**.

**Known un-rehearsed path (honest note).** The service corpus is second-lab generated, so `cix run`'s audit seat **recuses under F4** (`generator_lab == seat lab` — the correct behavior, and itself exercised here). The *live* second-lab seat on a full run therefore remains first-exercised at G5, where the real corpus's non-sibling provenance lets the seat proceed; that path is covered by offline tests today.

---

## 4 · Testing and honesty

- **`servicegen`** — offline `ScriptedClient` tests: thread structure (chain members share `thread_id`, continuity present), firewall disjointness (spec pathology text vs. A9 item text), truth registry shape, provenance fields. One **opt-in live** generation test (skips without an API key), matching the existing live-test convention.
- **CLI commands** — offline tests on persisted-shaped hits (the `test_g4_dryrun` pattern): `self-test` emits a valid `state` and includes `band_movement` when a catalogue+crosswalk are supplied; `differential` constructs each variant, re-runs a scripted detector through the shared helper, and scores each delta within tolerance.
- **Shared-helper refactor** — the existing e2e `cix run` tests stay green, proving the detection path factored out of `_cmd_run` is behavior-preserving.
- **Honesty gate** — every rehearsal artifact labels its outcome level O1. No path lets synthetic output be presented as O2/O3 (AC-17 discipline, applied early).
- Full suite stays green (171 → grows).

---

## 5 · Exit criteria

1. `cix generate-service-corpus`, `cix self-test`, `cix differential` exist, are tested, and are documented in `--help`.
2. `servicegen` produces a ~100-interaction service corpus meeting the §3.1 differential-target coverage minimums, with repeat-contact threads, a truth registry, and provenance; firewall disjointness test green.
2a. `differential_design_v1.yaml` v1.0.1 (machine-readable targets) ratified with a changelog line; tolerances and expected-delta semantics byte-identical to v1.0.0.
3. The end-to-end rehearsal run completes: `cix run` on the service corpus → gated report (O1-labeled) → `self-test` emits an evaluable state → `differential` scores all 3 variants against frozen T-DIFF.
4. No frozen threshold moved; T-SST / T-DIFF register unchanged.
5. Full test suite green; docs (README status line + ROADMAP §G5) note the rehearsal complete and G5 now blocked only on OD-1.

### 5.1 Still blocked after this follow-on (unchanged)

The **real** FS corpus (OD-1) and everything O2/O3 depends on. This rehearsal removes every *mechanism* first-time from G5; only the real corpus itself remains.

---

## 6 · File manifest (additions to the shipped tree)

```
src/cix/servicegen.py                         # new — thread-aware service corpus generator
configs/service_corpus_spec_v1.yaml           # new — A9-mapped service pathologies, threads, style guide
src/cix/cli.py                                 # +3 subcommands, detection helper extracted from _cmd_run
tests/test_servicegen.py                       # new — offline generation + firewall + threads
tests/test_service_spec.py                     # new — firewall disjointness (mirrors test_calspec)
tests/test_cli_selftest.py                     # new — cix self-test glue
tests/test_cli_differential.py                 # new — cix differential glue (re-run path)
docs/service_corpus_spec.md                    # new (optional) — narrative half of the service spec; rehearsal infra, not a PRD-normative A-artifact
```

---

## 7 · Sequencing summary

servicegen + spec (with firewall test) → detection-helper refactor (run tests stay green) → `self-test` glue → `differential` glue → the end-to-end rehearsal run → doc pass. Authoring the service pathology descriptions (which A9 items, what each plants) is drafted with the spec and refined against the A9 rubric during implementation — the same authoring motion as the calibration corpus spec.
