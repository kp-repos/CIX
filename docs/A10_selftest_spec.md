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

The G4 harness implements all four §7 layers as gated comparisons: distribution distance
(total-variation over item count-shares), top-k rank (leverage-grid ordering), highlighted-action
set membership, and opportunity-band movement (priced ranking). A seed is material if any layer
differs; the state is driven by the fraction of material seeds, and per-layer fractions are
reported (§7.6). `band_movement` is compared only when a catalogue + crosswalk are supplied — the
real G5 run and the G4 synthetic dry-run both provide one. `self_test(...)` returns
`layers_compared` and `per_layer_fraction` so the output never overclaims which layers ran.
