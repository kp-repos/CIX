# G3 Calibration — Operations Guide

**Purpose:** the durable, re-runnable record of the calibration gate — the decisions of record, the configuration surface (every knob and when it is safe to turn), and the procedure to run it again. The calibration corpus is **permanent validation infrastructure** (design record D§10): run it first at G3, and re-run it **after any material detector change** — i.e. on build iterations that touch the rubric, the label schema, the tag vocabulary, or either model. This guide is how you do that repeatably without re-deriving the discipline each time.

**Governing sources (do not restate here, defer to them):** PRD `docs/CIX_PRD_v1_2026-07-31.md` §5 (gates), §6 (threshold protocol), §7 (self-test), §8 (abandon triggers); design record §7.3 (calibration); the executable plan `docs/superpowers/plans/2026-08-01-g3-calibration.md`.

---

## 1. Decisions of record

| Decision | Ratified | Where it lives |
|---|---|---|
| **OD-2** — second lab = **OpenAI (GPT-5.x)**; roles: calibration-corpus **generator** + sampled **audit seat**; **F4** = the seat recuses in code on corpora its sibling generated | 2026-08-01 | PRD §13, `configs/second_lab_config_v1.yaml` |
| **Checkpoint A** — A8 sales rubric v1 (10 items) + A7 calibration spec ratified as authored | 2026-08-01 | `PO-RATIFIED` headers in `configs/sales_rubric_v1.yaml`, `configs/calibration_spec_v1.yaml`, `docs/A7_calibration_corpus_spec.md` |
| **Checkpoint B** — T-CAL / T-NULL / T-PARA / T-ITER values frozen; exact second-lab model snapshot pinned | _pending — see §4 Phase 2_ | `configs/thresholds_v1.yaml`, `configs/second_lab_config_v1.yaml` |

Two limitations accepted at ratification (both intended, neither a defect):
1. **T-NULL scope** — the null gate counts false reports only for the six *planted* pathology items; the two unplanted negative items (`unowned_follow_up`, `missited_work_allocation`) are not exercised by T-NULL.
2. **Positive items ungated** — `clean_handoff_execution` and `single_touch_completion` are measured but not planted or gated in G3.

---

## 2. Configuration surface — the knobs

Every tunable input to calibration and what it controls. **Current value** columns let you scan and adjust.

### Detector side (what the instrument hunts)
| File | Knob | Current | Change means |
|---|---|---|---|
| `configs/sales_rubric_v1.yaml` (A8) | 10 items · criteria · prefilters · units | v1.0.0 | **Detector change.** Bump `version` (e.g. 1.0.1). Consumes a **T-ITER dev cycle**. Re-run the rubric-hit pass + re-calibrate. |
| `configs/paraphrases_v1.yaml` | one paraphrase per item (T-PARA instrument) | v1.0.0, `rubric_version: 1.0.0` | Keep `rubric_version` in lockstep with the rubric. A paraphrase must stay meaning-equivalent but lexically distinct. |
| `configs/label_schema_v1.yaml` (A2) | core label fields | v1.0.0 | Upstream artifact; rarely changes at G3. A change re-runs the label pass and invalidates persisted labels. |
| `configs/tag_vocabulary_v1.yaml` (A1) | lexical/structural tags (prefilter targets) | v1.0.0 | Changing a prefilter tag ripples into the rubric's `requires` + re-index. |

### Generation side (the known-truth corpus)
| File | Knob | Current | Change means |
|---|---|---|---|
| `configs/calibration_spec_v1.yaml` (A7) | `style_guide`, plant `description` wording | — | **Generation-side only.** Regenerate the corpus. Does **NOT** consume a T-ITER cycle (it is not a detector change). Wording must stay 5-token-disjoint from rubric text (firewall — `tests/test_calspec.py`). |
| " | `pathologies` (keys, `maps_to_item` crosswalk, `embeds_per_interaction`, `source_type`) | 6 pathologies P1–P6 | New corpus + new truth registry. Crosswalk targets must be real rubric item ids. |
| " | `splits` (`instances_per_cell`, `clean_interactions`, `interactions`, `seed`) | dev 60 / holdout 60 / null 50; seeds 20260801/02/03 | Changes corpus size/composition. Different seed → different (still deterministic) corpus. |

### Gates (the numbers that can kill the project)
| File | Knob | Current | Change means |
|---|---|---|---|
| `configs/thresholds_v1.yaml` | **T-CAL** rel-err / abs-err / attribution floor | 0.25 / 2 / 0.80 | **Gate change → RE-FREEZE.** Must be committed **before** the first non-dev result it governs (R-VAL-6). Bump the file `version`; the git history is the register audit trail. |
| " | **T-NULL** false reports per 100 / min nulls | 4 / 40 | " (pre-registered absolute floor) |
| " | **T-PARA** disagreement floor / sample | 0.20 / top-2 + rare-2, 6 judgments | " |
| " | **T-ITER** dev cycles / holdout evals | 3 / 1 | " (the revision budget) |

### Models
| File | Knob | Current | Change means |
|---|---|---|---|
| `configs/second_lab_config_v1.yaml` | `model` (exact snapshot), `audit_sample_hits`, `agreement_floor` | `gpt-5.2` (pin exact), 8, 0.8 | **Model change → re-run.** Calibration is per model snapshot. Pin the exact dated id at Checkpoint B. |
| `configs/run_config_v1.yaml` | primary `model`, `temperature`, `seed` | `claude-fable-5`, 0, seed 20260731 | Primary-detector model change → re-calibrate. Seed governs all sampling reproducibility. |

---

## 3. Change taxonomy — the reusable mental model

When you adjust something before re-running, classify it — this determines cost and cycle accounting:

- **Generation-side** (style guide, plant wording): regenerate the corpus. **No T-ITER cycle consumed.** The instrument didn't change; only the test material did.
- **Detector-side** (rubric wording, prefilter, label schema): bump the rubric version, re-run detection. **Consumes one T-ITER dev cycle** (budget 3).
- **Threshold** (any gate value): **re-freeze** — commit the new value *before* the next non-dev result, bump `thresholds_v1.yaml` version, note the rationale. The freeze-before-results ordering (R-VAL-6) is the entire integrity claim; the git timestamp is the proof.
- **Model** (either lab): re-pin, re-run in full. Calibration numbers are only valid for the pinned snapshots.

---

## 4. Re-run procedure (each build iteration)

The full step-by-step with exact commands is the executable plan: **`docs/superpowers/plans/2026-08-01-g3-calibration.md` (Task 11)**. Condensed phase order:

1. **Checkpoint A** — review/ratify A8 + A7 (flip `PO-RATIFIED` headers), commit.
2. **Checkpoint B (the freeze)** — review threshold values, pin the exact model snapshot, commit. **This commit must predate every command below** (R-VAL-6).
3. **Verify model reachable** — `cix`-adjacent one-liner lists OpenAI models and checks the pin.
4. **Generate splits** — `cix generate-calibration --split {dev,holdout,null}`; spot-check; commit corpus.
5. **Dev cycles (≤3)** — `cix run <dev/corpus> --rubric …` then `cix calibrate … --split dev`; revise rubric wording on failure (each is a cycle); never open holdout.
6. **Null run** — `cix calibrate … --split null`; T-NULL breach = stop, don't tune.
7. **Holdout (one shot)** — `cix calibrate … --split holdout --final`; these are the exit numbers.
8. **Record exit** — commit runs + fixtures; update PRD changelog + README.

**Ordering is auditable:** after a run, `git log --oneline` must show freeze (B) → generate → score commits in that order.

---

## 5. Stop conditions (abandon-trigger-1, PRD §8)

The gate is built to make these verdicts unavoidable; recording them is success even when the news is bad:
1. **T-NULL breach** on the null set.
2. **Holdout T-CAL fail** after the T-ITER budget.
3. **T-ITER exhausted, still failing** (3 dev cycles used, holdout out of tolerance).

Do not tune against the null set or the holdout. The honest outcome is a recorded stop/continue decision.

---

## 6. Artifacts produced (where the evidence lives)

| Artifact | Path | Role |
|---|---|---|
| Generated corpora | `tests/fixtures/calibration/{dev,holdout,null}/corpus/` | The known-truth interactions |
| Truth registries | `…/{split}/truth.json` | Planted pathology + loudness + expected count per interaction (outside the corpus dir so the loader never sees it) |
| Provenance | `…/{split}/provenance.yaml` | Generator lab/model/prompt hash — drives F4 recusal |
| Cycle log | `tests/fixtures/calibration/cycles.json` | T-ITER register history (append-only) |
| Holdout marker | `…/holdout/.evaluated` | One-shot guard; claimed at guard time |
| Calibration report | `runs/cal-*/calibration_report.json` | Per-pathology T-CAL rows, loudness sensitivity, T-NULL rate |
| Run stores | `runs/cal-*/run.db` + `manifest.json` | The gated run; manifest records artifact ids + frozen thresholds version |
