# CFPB Comparative Briefing — design spec

**Date:** 2026-08-05
**Status:** ratified (brainstorm), ready for implementation plan
**Depends on:** `CIX_PRD_Patch_HANDOFF_2026-08-03.md` v2.1 (**ratified by KP 2026-08-05**, applied in the
governance pass below), `CIX_Corpus_Sourcing_Memo_2026-08-03.md` v4, business-briefing layer
(`src/cix/briefing.py`, 2026-08-04 spec), persisted run store (R-IDX-5)
**Corpus:** CFPB Consumer Complaints, filtered — `~/corpora/open/cfpb/cfpb_narratives_filtered.csv`,
1,500,436 narratives, public domain, substrate class **S2**

## 0. Decision record (KP, 2026-08-05)

| Decision | Ruling |
|---|---|
| Demo audience | **Internal only** — tech-capability proof; O1 remains parked. All acquired corpora usable |
| First real corpus | **CFPB, Block Inc. vs Bank of America, 2024+** (the sourcing memo §0.1 first-run pair) |
| Scale | **Pilot slice first** — 2,500 narratives per side, deterministic stratified sample; the full ~63K pair follows once the shape is validated |
| Deliverable shape | **Comparative briefing** — a side-by-side artifact over the two operations, not two disconnected briefings |
| PRD patch v2.1 | **Ratified as drafted.** §E resolved: speaker option (b) for v1; NC route approved for internal O2/O3; Twitter CS acquisition confirmed (on disk); S2 serves O3 for corpus-level items only |
| Architecture | **Two runs + compare layer** — each operation is an ordinary run through the untouched calibrated pipeline; comparison is a new model-free presentation layer over two persisted runs |

## 1. Problem

The business briefing (`cix briefing`) is shipped and demo-ready, but everything it renders is synthetic —
every page carries the "O1 only — synthetic" banner. The goal is a business-user report with **real data**
as the key demo deliverable.

Three real corpora are acquired and profiled (sourcing memo §0). CFPB is the strongest: real customer
language, preserved dollar figures, a public-domain licence, and — uniquely — an outcome label the model
never sees. `Company response to consumer` yields a **270× measured difference** in monetary-relief rate
between Block, Inc. (0.11%) and Bank of America (29.64%), 2024+. That is semi-ground-truth for free: if
CIX's analysis of Block does not surface "customers don't get their money back" as a dominant pattern, the
pipeline is missing something a human spots in minutes; if it does, that is a hit against a label the model
never saw.

The demo moment is comparative: CIX briefs both operations blind, then the withheld label is unsealed
beside its findings.

## 2. Scope

**In scope:**
1. **Governance pass** — apply PRD patch v2.1; back-propagate the design record rev 2.3 → 2.4; close D-1;
   record the §E rulings; changelogs in both documents; fix the stale "G5 gated only on the FS corpus"
   language in README/roadmap.
2. **CFPB ingest adapter** — new corpus slot; no source-specific logic in any downstream stage.
3. **Complaint rubric + complaint presentation config** — new versioned knowledge artifacts.
4. **Two pilot runs** — `runs/cfpb-block-pilot`, `runs/cfpb-bofa-pilot`, standard pipeline end to end.
5. **Comparative briefing** — `cix compare <runA> <runB>`, model-free, over two persisted runs.
6. **Demo runbook update** — the comparative walkthrough including the reveal.

**Explicitly out of scope (deferred):**
- The full ~63K pair run (prerequisite: a calibration pass for the complaint rubric — see §5.3).
- Any change to the frozen instrument: synthesis prompts, evidence gate, aggregation, frozen thresholds.
- Any external-facing artifact (O1 parked; internal audience ruled).
- A complaint swap catalogue — plays/dollar-opportunity sections render their honest empty state.
- Speaker-attribution inference (moot for monologue; deferred to v1.5 per P4 regardless).

## 3. CFPB ingest adapter

A new ingest module (`src/cix/cfpb.py`) reading the filtered CSV. The corpus remains outside the repo;
the adapter takes the path from run config.

### 3.1 Filtering and sampling

- **Filter:** company ∈ {Block, Inc., Bank of America} (exact source-column values verified at build
  time), `Date received` ≥ 2024-01-01, narrative non-empty.
- **Date hazard (P5 class):** `Date received` is mixed-format — full ISO 8601 timestamps on recent rows,
  bare dates on older. Parsing must handle both explicitly; a parse failure is a counted, logged drop,
  never a silent NaT.
- **Pilot sampler:** deterministic and seeded, stratified by calendar month across the window, 2,500 per
  side. Seed, strata, and per-stratum counts recorded in the manifest; the same seed reproduces the same
  slice byte-for-byte.

### 3.2 Outcome-label withholding (honesty-critical)

`Company response to consumer` is the semi-ground-truth. It must be **withheld by construction**:

- The column never enters the run store, any model context, any prompt, or any pipeline artifact.
- At ingest it is diverted to a sealed sidecar — `runs/<run>/holdout_labels.json`, keyed by source
  complaint ID — read **only** by the compare layer's reveal block, post-run.
- A test asserts the label string values (e.g. "Closed with monetary relief") appear nowhere in the store
  or persisted payloads.

### 3.3 Manifest fields (per ratified patch P3/P4)

`substrate_class: S2` · `licence_tier: public-domain` · `speaker_attribution: none` ·
`economic_signal: present` · `ivr_structure: absent`.

Enforced in code, not convention: an S2 run emits O3 only for corpus-level items; rubric items declaring a
dependency on a property the corpus lacks (speakers, turn structure, IVR) are **skipped and reported as
skipped**, excluded from coverage denominators.

### 3.4 Ingest hardening (P5)

- **Dedup (R-IDX-9):** content-hash every narrative; identical hashes collapse to one, duplicate count
  logged in the manifest.
- **Redaction awareness (R-IDX-10):** CFPB masks PII as `XXXX`/`XX/XX/XXXX` — these are redaction tokens,
  not vocabulary, and never render in evidence excerpts as content. **Exception:** `{$250.00}`-notation
  dollar tokens are *content* — parsed and retained as amounts. This is what preserves the economic signal.

## 4. Complaint rubric + presentation config

### 4.1 `configs/complaint_rubric_v1.yaml`

8–12 complaint-shaped items, every item `requires_speaker: false`, each declaring unit
(interaction/occurrence) and level (interaction/corpus). Candidate item families (final set authored at
implementation, reviewed by KP):

remediation denied / no refund · funds frozen or held · account lockout · fraud victim redirected without
help · unresponsive support / no reply · repeat complaint unresolved · fee dispute · misapplied payment.

**Blindness rule:** items describe generic complaint pathology, present in any financial-services
complaint stream. The rubric does not encode the withheld label or anything derived from it. The reveal
tests whether Block's **rates and rank order** diverge — not whether an item exists.

### 4.2 `configs/briefing_presentation_complaint_v1.yaml`

Business labels + glosses per rubric item; a complaint-shaped headline metric —
`unremediated_loss_rate`: distinct narratives matching ≥1 member of the loss-without-remedy item set,
union over hits, interaction-unit only — same unit-safety and union-not-sum rules as
`avoidable_contact_rate`, resolvable via `cix query --metric`.

### 4.3 Calibration honesty

The complaint rubric will not have passed a G3-style calibration when the pilot runs. **The pilot is the
rubric shakedown and every artifact says so** (a `calibration: pending` note in manifest and briefing
trust block). A calibration pass (synthetic complaint corpus with planted pathologies, T-CAL/T-NULL
analogues) is the documented prerequisite for the full 63K run — not for the pilot.

## 5. Pilot runs

`runs/cfpb-block-pilot` and `runs/cfpb-bofa-pilot`, each an ordinary
`ingest → normalize → index → classify → aggregate → synthesize → validate → report` run with the
complaint rubric. The single-run `cix briefing` works on each with the complaint presentation config.

- **Spend recording:** actual model spend per run is recorded in the manifest and becomes the first
  empirical D-11 cost-envelope figure.
- **O-level:** runs are internal O2-track; O3 emission limited to corpus-level items per S2 ruling.

## 6. Comparative briefing (`cix compare`)

`src/cix/compare.py` + CLI `cix compare <runA> <runB> [--no-pdf]`. Same architecture contract as
`briefing.py`: **model-free**, read-only over persisted runs, fail-closed, deterministic renders. Emits
`compare.json` / `compare.html` / `compare.pdf` (WeasyPrint path shared with briefing).

| Block | Content |
|---|---|
| `meta` | both manifests, substrate/O-level banner, n per side, rubric + presentation versions |
| `headline` | side-by-side headline metrics, divergence ratio |
| `rank_order` | per-operation pattern rank, rank shifts highlighted |
| `driver_rates` | per-item rates and ratios, `cix query` handles for both runs |
| `divergence` | top divergent items, deterministic so-what composition (no model) |
| `reveal` | withheld label unsealed from the sidecars: monetary-relief rate per operation, banner **"withheld ground truth — never seen by the model"**, set beside CIX's ranked findings. Facts only; interpretation stays human for the pilot |
| `trust` | both validation summaries, drop logs, S2 skip lists, spend, `calibration: pending` note |

**Fail closed on:** rubric version mismatch between the runs, presentation version mismatch, missing
persisted payloads, corrupt artifacts, missing sidecar when the reveal is requested.

**Honesty rules (builder-enforced, tested):**
1. Comparative claims computed only where both runs measured the same item in the same unit — enforced
   structurally, like the existing unit-safety guard.
2. Union-not-sum for any rate; every number carries formula + query handle.
3. O-level/substrate banner mandatory on every artifact.
4. Honest empty states (no catalogue → no dollar-opportunity section, said in place).
5. The reveal renders only from the sealed sidecar and always carries the withheld-ground-truth banner.

## 7. Testing (TDD, existing suite style)

1. **Ingest:** both date formats parse; parse failures are logged drops; filter correctness on a fixture
   CSV; sampler determinism (same seed → same IDs); dedup collapses known duplicates; redaction tokens
   excluded from vocabulary while `{$…}` amounts parse; **label-withholding assertion** (outcome strings
   absent from store and payloads; present in sidecar).
2. **Substrate enforcement:** S2 manifest fields set; conversation-dependent items skip-and-report;
   coverage denominators exclude skips; O3 restricted to corpus-level items.
3. **Rubric/config validation:** version pinning, unknown-item references fail closed.
4. **Compare builder:** rank/ratio correctness on fixture runs; same-item-same-unit guard; version
   mismatch fails closed; read-only guarantee (drop_log unchanged after `cix compare`); no model client
   constructed.
5. **Reveal:** renders only when sidecars exist; carries the banner; absent sidecar fails closed with a
   clear message.
6. **Golden render:** compare over two fixture runs matches committed golden JSON; HTML carries banner,
   both headline metrics, rank table, reveal block.

## 8. Sequencing

1. **Governance PR** — patch applied, design record rev 2.4, README/roadmap de-staled.
2. **Ingest + rubric PR** — CFPB adapter, complaint rubric + presentation config, tests.
3. **Pilot runs** — Block + BofA, 2,500/side; per-run briefings rendered.
4. **Compare layer PR** — `cix compare`, comparative artifact over the two pilot runs.
5. **Demo runbook update** — comparative walkthrough with the reveal as the closing beat.

## 9. Acceptance

- PRD carries patch v2.1; design record at rev 2.4; both changelogged.
- `cix compare runs/cfpb-block-pilot runs/cfpb-bofa-pilot` produces `compare.json/html/pdf`.
- The outcome label appears nowhere in either run store or payload; the reveal renders it from the
  sidecar with the withheld-ground-truth banner.
- Headline metrics resolve via `cix query --metric` on each run; every comparative number carries its
  formula and query handles.
- S2 skip lists visible in trust; `calibration: pending` stated; spend recorded in both manifests.
- Full test suite green; `--no-pdf` works without WeasyPrint.
