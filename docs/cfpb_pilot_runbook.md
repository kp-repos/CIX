# CFPB Pilot Runbook — Block, Inc. vs Bank of America (2024+)

Spec: `docs/superpowers/specs/2026-08-05-cfpb-comparative-briefing-design.md`.
Live model spend: operator (KP) go-ahead required before §3. Estimate before running:
5,000 narratives × (label + rubric passes + audit samples) on the pinned primary model —
record the actual figure in §5; it becomes the first empirical D-11 envelope number.

## 1 · Ingest (offline, deterministic)

    uv run cix cfpb-ingest ~/corpora/open/cfpb/cfpb_narratives_filtered.csv \
      --company "Block, Inc." --since 2024-01-01 --n 2500 --seed 20260805 \
      --out ~/corpora/open/cfpb/pilot-block
    uv run cix cfpb-ingest ~/corpora/open/cfpb/cfpb_narratives_filtered.csv \
      --company "BANK OF AMERICA, NATIONAL ASSOCIATION" --since 2024-01-01 --n 2500 --seed 20260805 \
      --out ~/corpora/open/cfpb/pilot-bofa

Check both summaries: `written: 2500`, duplicates and drops logged. The corpora stay
outside the repo (public domain, but they are data, not code).

## 2 · Sanity gates (offline)

    uv run pytest -x -q          # suite green before any spend

## 3 · Runs (LIVE SPEND — KP go-ahead)

    uv run cix run ~/corpora/open/cfpb/pilot-block/units \
      --rubric configs/complaint_rubric_v1.yaml \
      --out runs/cfpb-block-pilot \
      --clearance "CFPB public domain — internal O2 track; substrate S2; complaint rubric calibration PENDING (pilot = shakedown)"
    uv run cix run ~/corpora/open/cfpb/pilot-bofa/units \
      --rubric configs/complaint_rubric_v1.yaml \
      --out runs/cfpb-bofa-pilot \
      --clearance "CFPB public domain — internal O2 track; substrate S2; complaint rubric calibration PENDING (pilot = shakedown)"

No `--catalogue` (no complaint catalogue in v1 — plays render their honest empty state).
Verify each manifest: `substrate_class: "S2"`, `rubric_file: "complaint_rubric_v1.yaml"`.

## 4 · Per-run briefings + self-tests

    uv run cix briefing runs/cfpb-block-pilot --presentation configs/briefing_presentation_complaint_v1.yaml
    uv run cix briefing runs/cfpb-bofa-pilot  --presentation configs/briefing_presentation_complaint_v1.yaml
    uv run cix self-test runs/cfpb-block-pilot
    uv run cix self-test runs/cfpb-bofa-pilot

Self-test detail must read `outcome_level=O3-corpus-level-items-only` (substrate S2).

## 5 · Comparative briefing with the reveal

    cp ~/corpora/open/cfpb/pilot-block/holdout_labels.json runs/cfpb-block-pilot/
    cp ~/corpora/open/cfpb/pilot-bofa/holdout_labels.json  runs/cfpb-bofa-pilot/
    uv run cix compare runs/cfpb-block-pilot runs/cfpb-bofa-pilot \
      --presentation configs/briefing_presentation_complaint_v1.yaml \
      --name-a "Block, Inc." --name-b "Bank of America" \
      --out runs/cfpb-compare-pilot

The labels are copied only AFTER both runs complete — the sidecar never sits in a run
dir while the run executes. Record actual model spend here: ___ (D-11).

## 6 · Read the result honestly

The reveal states facts (per-side monetary-relief rates over the withheld labels).
Interpretation is human. The hoped-for hit: Block's rank order is dominated by
loss-without-remedy patterns and the ratio in `unremediated_loss_rate` points the same
direction as the withheld 270× relief-rate gap. A miss is a finding too — it feeds the
calibration pass that gates the full 63K pair run.
