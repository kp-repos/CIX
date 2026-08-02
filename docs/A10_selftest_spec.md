# A10 — Whole-Corpus Self-Test Spec · v1

**Owner:** PO · **Status:** pending freeze (Checkpoint B) · **Config:** `configs/selftest_spec_v1.yaml`
**Governs:** R-VAL-5, PRD §7 · **Resolves:** OD-10 · **Threshold:** T-SST

## What it measures

Whether corpus access changed the *output*: does a 10% sample reproduce the full corpus's
decision-relevant distribution, ranking, opportunity bands, and highlighted actions? It does
**not** prove classification or causal correctness (§7.8).

## Protocol (§7)

1. Freeze eligibility, rubric, catalogue, thresholds, highlight rules, metrics before comparing.
2. Below `min_evaluable_interactions` -> `not-evaluable`.
3. For each of the 5 predeclared seeds, draw a 10% sample and regenerate aggregation, ranking,
   highlights, residuals, and bands **from that sample's records only** — no full-corpus leakage.
4. Compare across four separated layers: distribution distance · rank/top-k · band movement ·
   highlighted-action difference.
5. Report the **fraction of seeds** showing each material difference.
6. Output state: `material-advantage` (>= `material_seed_fraction` of seeds show a decision-relevant
   difference) · `no-material-advantage` (evaluable, sample reproduced all decision-relevant
   outputs) · `not-evaluable`.

## G4 scope

The G4 harness implements the **top-k rank** comparison — the layer that drives the leverage
grid ordering and highlighted actions — as the decision-relevant mechanism proof. The other
three §7 layers (distribution distance, opportunity-band movement, highlighted-action
difference) are reported but not gated at G4; they become gated comparisons at G5 on the real
run. `self_test(...)` returns `layers_compared` so the output never overclaims which layers ran.

`no-material-advantage` on an evaluable **real** run is an abandon-trigger-2 input (§8) — at G4
the harness only runs on synthetic data (mechanism proof).
