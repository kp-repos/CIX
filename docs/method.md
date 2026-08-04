# How CIX works, and why you can trust it

*A one-page method note for a non-technical reader. Everything here is sourced from
the PRD (`CIX_PRD_v1_2026-07-31.md`) and the design record
(`CIX_BRAINSTORM_OUTPUT_2026-07-31.md`); section references are given so any claim can
be checked. The per-run audit trail lives in each report's own Method section.*

## What it does

CIX reads a corpus of customer interactions and produces one report — six sections in
attention order: Highlights, What's working, Leverage grid (+ shelf), Priced plays, Full
distribution + coverage, and Open flags + method (PRD §4.8, R-OUT-1). Every number in
that report is traceable back to the exact scrubbed source text behind it.

## The pipeline

The run is a fixed sequence, ingest to report (PRD §2–4):

**label → rubric hits → rollup → synthesis → report**

- **Label** — each interaction is classified on a fixed schema.
- **Rubric hits** — a frozen rubric marks where each item occurs, recording the exact
  snippet ID(s) it saw.
- **Rollup** — hits are counted and shared against named denominators; units never
  cross-sum (PRD §4.6, R-EVD-2).
- **Synthesis** — a model writes each finding's narrative from the cited evidence only.
- **Report** — rendered from the persisted run, never from live model output, so the PDF
  and the store name the same manifest.

## The one hard gate: evidence integrity

There is exactly one mechanical gate, and it is unforgiving (PRD §4.6):

- **R-EVD-1 Citation integrity** — every published quote must string-match stored scrubbed
  content exactly.
- **R-EVD-2 Quantitative integrity** — every count, share, and rank must recompute from
  persisted rows.
- **R-EVD-3 Join/manifest integrity** — versions, units, and manifests must all resolve.

The rule is **drop, don't flag**: a claim that fails the gate is removed from the report
and written to the drop log — it never ships with a warning label. A fabricated-evidence
drop is release-blocking for the whole run.

You can watch this live. `cix query <run> --item <finding>` resolves a finding's count to
the actual source interactions behind it; `cix query <run> --quote "<text>"` does the
reverse, and a quote that isn't in the corpus verbatim says so and fails closed. This is
the R-OUT-2 promise: a live evidence query resolves any claim to its scrubbed source in
under a minute.

## Why a clean report isn't self-serving

The evidence gate cannot catch six failure modes — biased classification, genre
hallucination, right-count/wrong-mechanism, noise promoted to pattern, false completeness,
and decision-irrelevant results (design record §7.1). So CIX runs six independent
validation tiers that each raise a *different* failure signal (design record §7.2):

| Tier | What it catches |
|---|---|
| **Calibration** | Gross mechanics; hallucination baseline; sensitivity floor |
| **Differential** | Magnitude miscalibration on real language (inject known deltas, readings must track) |
| **Stability** | Artifact findings; brittle judgment (split-half + paraphrase invariance) |
| **Self-consistency** | Filter blindness; label noise; silent recall loss |
| **Adjudication** | Shared-prior bias — a second frontier model from a different lab audits a sample |
| **Honesty** | False completeness — coverage, residuals, and saturation are headlined, not hidden |

No single tier proves truth; together they make unresolved uncertainty visible. On
mechanism specifically, synthesis may never print an unqualified causal claim: each finding
states its proposed mechanism, the strongest alternative, and whether the discriminating
evidence was found — absent, it ships marked **undischarged** (design record §7.4).

## Calibrated before it was scored

Every threshold freezes **before its first non-development observed result**, with the
freeze commit as a git ancestor of every number it governs — the ordering is auditable
(PRD R-VAL-6). On the calibration corpus the instrument passed **6/6 pathologies (T-CAL)**
and produced **0/100 false reports on null controls (T-NULL)**, against a pre-registered
floor of 4/100 (PRD changelog, G3 exit 2026-08-01).

## The honesty ladder

Three outcomes, never blended (PRD §2.3):

- **O1 — Pipeline demo-ready.** End-to-end run; an external party finds the artifact
  credible and traceable. **Synthetic data can satisfy O1, when labeled as such.**
- **O2 — Real-run release-ready.** The real corpus produces a fully gated artifact.
  Synthetic data cannot satisfy this.
- **O3 — v1 hypothesis test.** The real run's self-test emits a material-advantage verdict
  under the §7 protocol. Synthetic data cannot satisfy this.

A synthetic-corpus demo preserves O1 only and is never presented as O2 or O3.
