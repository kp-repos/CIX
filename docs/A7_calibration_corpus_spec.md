# A7 — Calibration Corpus Specification · v1

**Owner:** PO · **Status:** pending ratification (Checkpoint A of the G3 plan)
**Machine-readable half:** `configs/calibration_spec_v1.yaml` (pathologies, loudness, splits, crosswalk)
**Governs:** R-VAL-2, PRD §5 G3 row · **Generator:** second-lab model (OD-2: OpenAI GPT-5.x)

## Purpose

Manufacture a corpus where the truth is known, so the instrument's recovered counts can
be scored against planted magnitudes (T-CAL), its silence scored against a held-out null
set (T-NULL), and its sensitivity reported by loudness level — before it ever touches
real data.

## Design

- **Six pathologies** (P1–P6), each mapped to one negative sales-rubric item via the
  crosswalk in the YAML spec. The two positive rubric items are not planted; they are
  measured opportunistically and carry no calibration gate in G3.
- **Three loudness levels** — loud (stated explicitly, dwelt on), moderate (plainly
  present once), camouflaged (implied, never named). T-CAL gates on loud+moderate
  pooled; camouflaged yields a sensitivity row, never a gate (D§7.3: a curve, not
  pass/fail).
- **Splits:** dev 60 (36 planted = 6×3×2, 24 clean) · holdout 60 (same shape, different
  seed) · null 50 (zero target pathologies). Dev and holdout are separately generated;
  revisions see dev only; one predeclared holdout evaluation (T-ITER).
- **Expected magnitudes:** occurrence-unit pathologies plant 1–3 embeds per interaction
  (deterministic cycle); interaction-unit pathologies plant once. The truth registry
  (`truth.json`, outside the corpus directory) records pathology, loudness, and expected
  occurrences per interaction.
- **T-NULL scope (a known limitation, stated for ratification):** the null gate counts a
  false report only for the six *planted-pathology* items (the crosswalk targets). The two
  negative rubric items with no planted pathology (`unowned_follow_up`, `missited_work_allocation`)
  are not exercised by T-NULL — a false positive on them in the null set is invisible to the gate.
  This matches the frozen T-NULL rule ("any planted-pathology item hit"); it is a scope boundary,
  not a defect.

## Collusion breaks (non-circularity, D§7.3)

1. **Different lab:** generator is the second-lab model; the detector never generates.
2. **Description firewall:** the generator sees pathology descriptions only — never
   rubric criteria, exemplars, or paraphrases. Enforced two ways in code: the generator
   module must not reference rubric machinery (structural test), and no pathology
   description may share a 5-token n-gram with any rubric text (lexical test).
3. **F4:** the audit seat never adjudicates this corpus — the seat's sibling generated
   it. `cix run` reads the corpus provenance record and writes a `recused_f4` validation
   row instead of a seat verdict.

## Realism (PO ruling, 2026-08-01)

Style is carried by the distilled guide in the YAML spec — register, transcription
artifacts, generic tool names, concrete mundane detail. No verbatim reuse of any public
transcript; no public dataset is quoted or few-shotted. (CFPB narratives remain the
*service-side* donor for G4; this is the sales-side answer to design-record open item 13.)

## Provenance and honesty

Every generated split carries `provenance.yaml` (generator lab, model, prompt version,
spec version, timestamp). The corpus is synthetic and is only ever presented as O1
material (PRD §2.3).
