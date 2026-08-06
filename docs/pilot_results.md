# CIX Pilot Results — Stakeholder Brief

*Internal, for project stakeholders. Last updated 2026-08-06.*

Two end-to-end runs of the CIX pipeline are now on the record: a **synthetic rehearsal**
(O1, illustrative only) and the **first live-data run** (O2, real CFPB complaints, Block vs
Bank of America). This brief summarizes what each showed and links every report. For *how*
the pipeline works and *why* its numbers are auditable, see [`method.md`](method.md); for the
honesty ladder (O1/O2/O3) and gate sequence, see the [PRD](CIX_PRD_v1_2026-07-31.md).

---

## TL;DR

- **The instrument runs end-to-end on real language, unattended, and its evidence gate stays clean.** Two 2,500-complaint runs completed with **zero evidence drops** — every published number recomputes from the store and every quote string-matches its source.
- **On the live CFPB pilot, the blind analysis pointed at the right company.** With the outcome labels sealed away, CIX independently flagged **Block** as the higher-harm operator — and the withheld ground truth confirms Block resolves complaints with monetary relief at **~1/189th** Bank of America's rate.
- **The magnitude is honestly compressed** — CIX gets the *direction* right but understates *how large* the gap is. That is exactly the signal the calibration step (which gates the full-scale run) exists to close. **This is a shakedown pilot, not a calibrated measurement.**
- **The whole-corpus thesis held on real data** — the self-test says analyzing the full corpus materially changes the answer versus a 10% sample, on both companies.

---

## Run 1 — Synthetic rehearsal (O1)

**What it is:** a synthetic, financial-services-shaped customer-service corpus (100 interactions),
run through the complete pipeline to prove every mechanism before touching real data. **O1 means
illustrative only** — these numbers describe made-up data and are never a real-world claim.

**What it showed:**
- Full path executed: ingest → classify → aggregate → synthesize → validate → report, plus the
  business briefing, the whole-corpus self-test, and the differential tooling.
- Headline: `avoidable_contact_rate` **33%** (33/100) — a third of contacts trace to avoidable drivers.
- **Self-test: material-advantage (fraction 1.0)** — full-corpus analysis differed from a 10% sample on every layer checked.
- Differential variants (delete / duplicate / splice) all behaved as predicted — detection responds correctly to controlled perturbations.

**Reports:**
- 📊 [Business briefing (PDF)](../runs/svc-run/briefing.pdf) · [HTML](../runs/svc-run/briefing.html)
- 📄 [Full technical report (PDF)](../runs/svc-run/report.pdf)
- 🔬 [Self-test](../runs/svc-run/selftest_report.json) · [Differential](../runs/svc-run/differential_report.json) · [Manifest](../runs/svc-run/manifest.json)

---

## Run 2 — CFPB live pilot (O2): Block, Inc. vs Bank of America

**What it is:** the first run on **real, public-domain data** — 2,500 CFPB complaint narratives per
company (2024+), scored blind against the complaint rubric. The disposition outcome
(`Company response to consumer`) was **sealed at ingest** and unsealed only after the run, for
validation. Substrate S2, internal O2 track, **complaint-rubric calibration pending**.

### The reveal — blind analysis vs. withheld truth

CIX never saw the outcome labels. It computed a language-based **`unremediated_loss_rate`**
(complaints describing a loss with no remedy). Afterward, the sealed truth was unsealed:

| | CIX blind read (`unremediated_loss_rate`) | Withheld truth (monetary-relief rate) |
|---|---|---|
| **Block, Inc.** | **2,211 (88% of complaints)** | 4 / 2,500 → **0.16%** |
| **Bank of America** | 1,745 (~70%) | 756 / 2,500 → **30.24%** |
| **Direction** | Block worse (ratio 1.26×) | Block worse (~**189×** gap) |

**Read:** blind to every outcome, the instrument ranked the right company as the higher-harm operator.
Block's complaint profile is dominated by **"fraud victims turned away" (68.9%, its #1 issue)** and
refused refunds — the loss-without-remedy signature — and the sealed data confirms Block almost never
pays monetary relief while BofA does so ~30% of the time.

**The honest caveat:** the blind metric separates the two by **1.26×**, while the real relief gap is
**~189×**. CIX gets the arrow right, not the scale — because `unremediated_loss_rate` measures what
complainants *describe*, not the disposition *outcome*. Closing that gap between direction and
magnitude is precisely the job of the calibration pass that gates the full-scale (63K-pair) run.

### Trust & validation (both runs)
- **0 evidence drops** on each side — no quote or statistic failed the integrity gate.
- Interaction coverage ~95% (Block 94.8%); residual complaints logged, excluded from denominators.
- Stability checks: split-half **stable**, second-lab audit seat **agrees**, drop-rate **passes**,
  self-agreement mostly agrees (one field flagged **unstable** — a calibration note, not a failure).
  Paraphrase audit **not run** (no paraphrase set bound to the complaint rubric yet).
- **Whole-corpus self-test: material-advantage** — Block 0.6, BofA 0.8.

**Reports:**
- ⭐ **[Comparative briefing + reveal (PDF)](../runs/cfpb-compare-pilot/compare.pdf)** · [HTML](../runs/cfpb-compare-pilot/compare.html) · [JSON](../runs/cfpb-compare-pilot/compare.json)
- Block: [briefing (PDF)](../runs/cfpb-block-pilot/briefing.pdf) · [report (PDF)](../runs/cfpb-block-pilot/report.pdf) · [self-test](../runs/cfpb-block-pilot/selftest_report.json) · [manifest](../runs/cfpb-block-pilot/manifest.json)
- Bank of America: [briefing (PDF)](../runs/cfpb-bofa-pilot/briefing.pdf) · [report (PDF)](../runs/cfpb-bofa-pilot/report.pdf) · [self-test](../runs/cfpb-bofa-pilot/selftest_report.json) · [manifest](../runs/cfpb-bofa-pilot/manifest.json)

---

## What this means for the project

- **G5 (first real run) has a genuine directional hit**, with a clean evidence gate and the whole-corpus advantage confirmed on real CFPB language — not synthetic.
- **This is not yet a calibrated measurement.** The complaint rubric is uncalibrated; treat magnitudes as directional. The next gate is the **calibration pass** that turns this shakedown into a measurement and licenses the full-scale pair run.
- **Reproducibility:** every claim in these reports resolves to its scrubbed source via `cix query`
  (`--item` walks a count back to source complaints; `--quote` matches a pasted line or fails closed).

*Method & guarantees: [`method.md`](method.md). Pilot procedure: [`cfpb_pilot_runbook.md`](cfpb_pilot_runbook.md). Design record: [`../runs/cfpb-compare-pilot/compare.json`](../runs/cfpb-compare-pilot/compare.json) carries the full machine-readable reveal, rank order, and divergence table.*
