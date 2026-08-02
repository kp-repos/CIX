# A9 — FS Service Rubric v1

**Owner:** PO · **Status:** pending ratification (Checkpoint A of the G4 plan)
**Config:** `configs/service_rubric_v1.yaml` · **Governs:** R-RUB-6, PRD §5 G4 row
**Spine:** CX-1–4 from `docs/reference/CIX_POC_B_Sniffer_Scope_v2.md`

## Framing — zero call resolution

First call resolution asks whether you solved it on the first contact. **Zero call resolution**
asks why the contact happened at all: an interaction the customer had to initiate is a service
failure that wasn't anticipated. The rubric hunts avoidable contacts and the manual work around
them, with two positive counter-patterns (first-contact resolution, clean self-service).

## Items (10: 8 negative, 2 positive)

Repeat contact · billing defect · deterministic request · manual after-call work · avoidable
transfer · knowledge inconsistency · inbound status chase · unanticipated failure · (positive)
first-contact resolution · (positive) clean self-service deflection.

## swap_ref crosswalk

Six negative items carry a `swap_ref` into the stand-in catalogue (A5); two negatives
(`knowledge_inconsistency`, `unanticipated_failure`) and both positives are shelf/observation
only. Dangling swap_refs are a test failure (`test_service_rubric.py`).

## Authored second, runs first (R-RUB-6)

Authored at G4 after the sales rubric; runs first on the real FS corpus at G5. Units are held
to occurrence/interaction because the calibration and early real corpora carry no account/chain
linkage metadata.
