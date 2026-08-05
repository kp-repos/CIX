# Business Briefing Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a model-free `cix briefing` deliverable that re-renders any persisted run as a business-facing briefing (`briefing.json` + self-contained `briefing.html` + `briefing.pdf`), with two rigorously-defined, `cix query`-resolvable headline metrics, without touching the frozen instrument.

**Architecture:** A pure presentation layer. `src/cix/briefing.py` reads the already-persisted `report.json` + `manifest.json` + run store (read-only, exactly as `query.py` does) plus a new versioned presentation config, and builds a business structure enforcing honesty rules (no unit cross-summing; the avoidable-contact rate is a distinct-interaction *union* over the `hits` table, not a sum). A renderer turns that into one self-contained HTML string and prints the same HTML/CSS to PDF via WeasyPrint. A small `--metric` extension to `cix query` makes each headline number traceable to its source interaction set. Synthesis, the evidence gate, and every frozen threshold are untouched.

**Tech Stack:** Python 3.12 · uv · pytest · PyYAML · SQLite (via `cix.store`) · WeasyPrint (optional extra) · existing `cix.query` / `cix.report` patterns.

**Spec:** `docs/superpowers/specs/2026-08-04-business-briefing-report-design.md`

---

## File Structure

- **Create** `configs/briefing_presentation_v1.yaml` — versioned presentation config: `item_id → {business_label, gloss, polarity}` for the 10 service-rubric items + `headline_metrics.avoidable_contact_rate.members`.
- **Create** `src/cix/briefing.py` — `load_presentation`, `build_briefing` (+ private block builders and the two metric helpers), `render_briefing_html`, `render_briefing_pdf`.
- **Modify** `src/cix/query.py` — add `resolve_metric(store, manifest, presentation, metric_name, eligible)`.
- **Modify** `src/cix/cli.py` — add `_cmd_briefing` + subparser; extend `_cmd_query` + query subparser with `--metric`.
- **Modify** `pyproject.toml` — add a `pdf` optional-dependency extra (`weasyprint`).
- **Create** `tests/test_briefing.py` — builder, metrics, honesty, config-validation, HTML, `--no-pdf`, golden-on-`runs/svc-run`.
- **Modify** `tests/test_query.py` — `--metric` resolution test.

All persisted-data shapes below are taken from a real run (`runs/svc-run/report.json`): `sections.highlights[]` carry `{item_id, count, share, unit, evidence}`; `sections.whats_working[]` list positives; `sections.leverage` has `{grid[], shelf[], class_d[], note}` where each `grid` cell is `{item_id, effort, outcome, count, remedy_class}`; `sections.priced_plays.plays[]` carry `{item_id, count, unit, band, alternatives:[{swap_ref, substitute, remedy_class, ...}]}`; `sections.distribution` has `{items{id:{unit,count,share,denominator}}, interaction_coverage, residual_interactions, eligible_interactions}`; `manifest` carries `{artifacts:{hits}, corpus_clearance, rubric_version, catalogue_version, corpus_hash}`.

---

## Task 1: Presentation config + loader

**Files:**
- Create: `configs/briefing_presentation_v1.yaml`
- Create: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the config file**

Create `configs/briefing_presentation_v1.yaml`:

```yaml
# Business Briefing presentation layer v1 — maps A9 service-rubric item IDs to
# business language and declares headline-metric membership. Model-free, versioned,
# reviewable (peer to the rubric). Monday-action text is NOT here — it comes from the
# swap catalogue via report.json priced_plays[].alternatives[].substitute.
version: "1.0.0"
requires:
  rubric_version: "1.0.0"
# polarity mirrors the rubric so watch-list routing never depends on synthesis output.
items:
  repeat_contact_unresolved:
    business_label: "Repeat contacts on unresolved issues"
    gloss: "Customers coming back because the first contact did not resolve the problem."
    polarity: negative
  billing_defect_driver:
    business_label: "Contacts caused by billing errors"
    gloss: "Calls driven by a billing, invoice, or charge error the customer should not have had to make."
    polarity: negative
  deterministic_request:
    business_label: "Rote requests a person handled"
    gloss: "Fully deterministic asks (resets, address changes) a self-service path resolves without an agent."
    polarity: negative
  manual_after_call_work:
    business_label: "Manual after-call admin"
    gloss: "Agents doing record-keeping by hand after the call that a capture-at-source step removes."
    polarity: negative
  avoidable_transfer:
    business_label: "Avoidable transfers"
    gloss: "Contacts transferred or escalated for want of first-line capability."
    polarity: negative
  knowledge_inconsistency:
    business_label: "Inconsistent answers across contacts"
    gloss: "The same question answered differently on different contacts."
    polarity: negative
  status_chase_inbound:
    business_label: "Status-chase calls"
    gloss: "Contacts whose sole purpose is to chase the status of something already in progress."
    polarity: negative
  unanticipated_failure:
    business_label: "Avoidable provider-side failures"
    gloss: "Contacts that exist because of a provider-side failure that could have been anticipated."
    polarity: negative
  first_contact_resolution:
    business_label: "Issues resolved on first contact"
    gloss: "The healthy counter-pattern — resolved in one interaction, no follow-up needed."
    polarity: positive
  clean_self_service_deflection:
    business_label: "Clean self-service deflection"
    gloss: "A deterministic need met through self-service without consuming agent time."
    polarity: positive
headline_metrics:
  avoidable_contact_rate:
    members:
      - repeat_contact_unresolved
      - billing_defect_driver
      - status_chase_inbound
      - unanticipated_failure
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_briefing.py`:

```python
import json
from pathlib import Path
import pytest
from cix.briefing import load_presentation

PRESENTATION = Path("configs/briefing_presentation_v1.yaml")

def test_load_presentation_has_versions_items_and_metric_members():
    cfg = load_presentation(PRESENTATION)
    assert cfg["version"] == "1.0.0"
    assert cfg["requires"]["rubric_version"] == "1.0.0"
    assert cfg["items"]["manual_after_call_work"]["business_label"] == "Manual after-call admin"
    assert cfg["items"]["manual_after_call_work"]["polarity"] == "negative"
    assert cfg["items"]["first_contact_resolution"]["polarity"] == "positive"
    assert cfg["headline_metrics"]["avoidable_contact_rate"]["members"] == [
        "repeat_contact_unresolved", "billing_defect_driver",
        "status_chase_inbound", "unanticipated_failure",
    ]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py::test_load_presentation_has_versions_items_and_metric_members -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cix.briefing'`

- [ ] **Step 4: Write minimal implementation**

Create `src/cix/briefing.py`:

```python
"""Business Briefing presentation layer (model-free): re-render a persisted run for a
commercial reader. Reads report.json + manifest.json + the run store (read-only),
enforces honesty rules, and emits briefing.json + self-contained HTML + PDF.

Nothing here calls a model or mutates the store — the instrument stays frozen.
"""
from pathlib import Path
import yaml

def load_presentation(path: Path) -> dict:
    """Load the versioned presentation config (labels/glosses + headline-metric membership)."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add configs/briefing_presentation_v1.yaml src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): presentation config + loader (business labels, metric membership)"
```

---

## Task 2: Headline metric ① — avoidable-contact rate (union over hits)

**Files:**
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py` (top imports become `from cix.briefing import load_presentation, avoidable_contact_rate`):

```python
class _FakeStore:
    """Minimal stand-in for cix.store.Store.hits_for."""
    def __init__(self, rows):
        self._rows = rows  # list of {"item_id":..., "interaction_id":..., "unit":...}
    def hits_for(self, artifact_id):
        return list(self._rows)

def test_avoidable_contact_rate_is_a_distinct_union_not_a_sum():
    # Overlap: int-1 matches TWO members; naive sum=3, distinct union=2.
    rows = [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "status_chase_inbound", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "repeat_contact_unresolved", "interaction_id": "int-2", "unit": "interaction"},
    ]
    members = ["repeat_contact_unresolved", "billing_defect_driver",
               "status_chase_inbound", "unanticipated_failure"]
    m = avoidable_contact_rate(_FakeStore(rows), "ha", members, eligible=100)
    assert m["value"] == 2                     # union, not 3
    assert m["denominator"] == 100
    assert m["share"] == 0.02
    assert m["members"] == members

def test_avoidable_contact_rate_ignores_non_member_and_non_interaction_hits():
    rows = [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "manual_after_call_work", "interaction_id": "int-9", "unit": "occurrence"},   # not a member
        {"item_id": "unanticipated_failure", "interaction_id": "int-3", "unit": "occurrence"},    # member but occurrence-unit row -> structurally excluded
    ]
    members = ["repeat_contact_unresolved", "billing_defect_driver",
               "status_chase_inbound", "unanticipated_failure"]
    m = avoidable_contact_rate(_FakeStore(rows), "ha", members, eligible=100)
    assert m["value"] == 1
    assert sorted(m["interaction_ids"]) == ["int-1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k avoidable_contact_rate -v`
Expected: FAIL with `ImportError: cannot import name 'avoidable_contact_rate'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/cix/briefing.py`:

```python
def avoidable_contact_rate(store, hits_artifact: str, members: list[str], eligible: int) -> dict:
    """Distinct interactions matching >=1 negative interaction-unit member, as a UNION
    over the hits table (never a sum — overlapping interactions must not double-count).
    Occurrence-unit rows are structurally excluded (spec §5.1): counts never cross units."""
    member_set = set(members)
    ids = {h["interaction_id"] for h in store.hits_for(hits_artifact)
           if h["item_id"] in member_set and h.get("unit") == "interaction"}
    value = len(ids)
    return {
        "value": value,
        "denominator": eligible,
        "share": round(value / eligible, 2) if eligible else None,
        "members": list(members),
        "interaction_ids": sorted(ids),
        "method": ("distinct interactions matching >=1 member pattern "
                   "(union over hits), interaction-unit only"),
        "query": "cix query <run_dir> --metric avoidable_contact_rate",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k avoidable_contact_rate -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): avoidable-contact rate as a distinct-interaction union"
```

---

## Task 3: Headline metric ② — indicative automatable opportunity (dollar sum, gated + caveated)

**Files:**
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py` (import `automatable_opportunity`):

```python
def _leverage_grid():
    return [
        {"item_id": "manual_after_call_work", "effort": "low", "outcome": "large", "count": 87, "remedy_class": "A"},
        {"item_id": "deterministic_request", "effort": "medium", "outcome": "medium", "count": 19, "remedy_class": "A"},
        {"item_id": "avoidable_transfer", "effort": "medium", "outcome": "medium", "count": 9, "remedy_class": "A"},
        {"item_id": "billing_defect_driver", "effort": "high", "outcome": "large", "count": 19, "remedy_class": "D"},
    ]

def _priced_plays():
    return {"plays": [
        {"item_id": "manual_after_call_work", "band": {"low": 3480.0, "high": 10440.0},
         "alternatives": [{"swap_ref": "SW-ADMIN-CAPTURE",
                           "substitute": "Capture at the interaction -> structured extraction"}]},
        {"item_id": "deterministic_request", "band": {"low": 380.0, "high": 1140.0},
         "alternatives": [{"swap_ref": "SW-STATUS-SELFSERVE",
                           "substitute": "Self-service status + automated routing"}]},
        {"item_id": "avoidable_transfer", "band": {"low": 180.0, "high": 540.0},
         "alternatives": [{"swap_ref": "SW-STATUS-SELFSERVE",
                           "substitute": "Self-service status + automated routing"}]},
    ]}

def test_automatable_opportunity_sums_class_a_bands_with_caveats():
    m = automatable_opportunity(_leverage_grid(), _priced_plays())
    assert m["band"] == {"low": 4040.0, "high": 12120.0}
    assert m["inferred"] is True
    assert m["evidence_tier"] == "candidate"
    # Two class-A plays share SW-STATUS-SELFSERVE -> shared-remedy note present.
    assert "SW-STATUS-SELFSERVE" in m["shared_remedy_note"]

def test_automatable_opportunity_absent_without_catalogue():
    assert automatable_opportunity(_leverage_grid(), {"plays": []}) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k automatable_opportunity -v`
Expected: FAIL with `ImportError: cannot import name 'automatable_opportunity'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/cix/briefing.py`:

```python
def automatable_opportunity(leverage_grid: list[dict], priced_plays: dict) -> dict | None:
    """Sum of Class-A priced bands (dollars are unit-compatible, so summing is legal).
    Returns None when no catalogue is loaded (no priced plays) — honest empty state."""
    plays = priced_plays.get("plays") or []
    if not plays:
        return None
    class_a = [c["item_id"] for c in leverage_grid if c.get("remedy_class") == "A"]
    by_id = {p["item_id"]: p for p in plays}
    banded = [by_id[i] for i in class_a if i in by_id and by_id[i].get("band")]
    if not banded:
        return None
    low = sum(p["band"]["low"] for p in banded)
    high = sum(p["band"]["high"] for p in banded)
    swaps = [p["alternatives"][0]["swap_ref"] for p in banded
             if p.get("alternatives")]
    shared = sorted({s for s in swaps if swaps.count(s) > 1})
    note = ("indicative and inferred, not operator-confirmed; "
            "value is additive across distinct occurrences")
    if shared:
        note += f"; remedies shared across plays: {', '.join(shared)} (implementation effort is shared)"
    return {
        "band": {"low": low, "high": high},
        "currency": "USD",
        "horizon": "per year",
        "members": [p["item_id"] for p in banded],
        "method": "sum of Class-A priced bands (dollar, additive across distinct occurrences)",
        "evidence_tier": "candidate",
        "inferred": True,
        "shared_remedy_note": note,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k automatable_opportunity -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): indicative automatable-opportunity metric (gated, caveated)"
```

---

## Task 4: `build_briefing` — assemble blocks + honesty rules

**Files:**
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py` (import `build_briefing`):

```python
def _sections():
    return {
        "highlights": [
            {"item_id": "manual_after_call_work", "count": 87, "share": None, "unit": "occurrence", "evidence": []},
            {"item_id": "first_contact_resolution", "count": 82, "share": 0.82, "unit": "interaction", "evidence": []},
            {"item_id": "billing_defect_driver", "count": 19, "share": 0.19, "unit": "interaction", "evidence": []},
        ],
        "whats_working": [{"item_id": "first_contact_resolution", "narrative": "Resolved in one contact."}],
        "leverage": {
            "grid": _leverage_grid(),
            "shelf": [
                {"item_id": "first_contact_resolution", "count": 82, "unit": "interaction"},
                {"item_id": "unanticipated_failure", "count": 11, "unit": "interaction"},
                {"item_id": "status_chase_inbound", "count": 6, "unit": "interaction"},
            ],
            "class_d": [c for c in _leverage_grid() if c["remedy_class"] == "D"],
            "note": "catalogue 0.1.0",
        },
        "priced_plays": _priced_plays(),
        "distribution": {
            "items": {
                "manual_after_call_work": {"unit": "occurrence", "count": 87, "share": None},
                "first_contact_resolution": {"unit": "interaction", "count": 82, "share": 0.82},
                "billing_defect_driver": {"unit": "interaction", "count": 19, "share": 0.19},
                "deterministic_request": {"unit": "occurrence", "count": 19, "share": None},
                "avoidable_transfer": {"unit": "occurrence", "count": 9, "share": None},
                "unanticipated_failure": {"unit": "interaction", "count": 11, "share": 0.11},
                "status_chase_inbound": {"unit": "interaction", "count": 6, "share": 0.06},
            },
            "interaction_coverage": 1.0, "residual_interactions": 0, "eligible_interactions": 100,
        },
        "method": {
            "validations": [{"check": "T-DROP", "status": "pass"}, {"check": "T-PARA", "status": "not_run"}],
            "drop_summary": {"candidate_claims": 9, "quote_drops": 0, "stat_drops": 0},
        },
    }

def _manifest():
    return {"artifacts": {"hits": "ha"}, "rubric_version": "1.0.0", "catalogue_version": "0.1.0",
            "corpus_clearance": "synthetic service rehearsal corpus — O1 only, never O2/O3 (PRD §2.3)",
            "corpus_hash": "abc123"}

def _hits_rows():
    return [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "status_chase_inbound", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "unanticipated_failure", "interaction_id": "int-2", "unit": "interaction"},
    ]

def test_build_briefing_blocks_route_correctly():
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    # meta banner
    assert "O1" in b["meta"]["corpus_clearance"]
    # headline metric ①: union of {int-1, int-2} = 2
    assert b["headline"]["avoidable_contact_rate"]["value"] == 2
    # headline metric ②: class-A band sum
    assert b["headline"]["automatable_opportunity"]["band"] == {"low": 4040.0, "high": 12120.0}
    # plays: class-A only, effort-ranked (low-effort first), with Monday action
    play_ids = [p["item_id"] for p in b["plays"]]
    assert play_ids == ["manual_after_call_work", "deterministic_request", "avoidable_transfer"]
    assert b["plays"][0]["label"] == "Manual after-call admin"
    assert b["plays"][0]["monday_action"] == "Capture at the interaction -> structured extraction"
    # upstream: class-D
    assert [u["item_id"] for u in b["upstream"]] == ["billing_defect_driver"]
    # watch_list: negative-polarity shelf only (config polarity) — positive first_contact_resolution excluded
    watch_ids = [w["item_id"] for w in b["watch_list"]]
    assert "first_contact_resolution" not in watch_ids
    assert set(watch_ids) == {"unanticipated_failure", "status_chase_inbound"}
    # whats_working: the positive
    assert b["whats_working"][0]["item_id"] == "first_contact_resolution"
    # trust: coverage + evidence-gap note (all highlights carry empty evidence)
    assert b["trust"]["coverage"]["interaction_coverage"] == 1.0
    assert "pending" in b["trust"]["evidence_note"].lower()

def test_build_briefing_unit_safety_guard_rejects_occurrence_member():
    cfg = load_presentation(PRESENTATION)
    sections = _sections()
    # Corrupt a member to an occurrence unit -> the interaction-only rate must refuse.
    sections["distribution"]["items"]["billing_defect_driver"]["unit"] = "occurrence"
    with pytest.raises(ValueError, match="interaction-unit"):
        build_briefing({"sections": sections}, _manifest(), cfg, _FakeStore(_hits_rows()))

def test_build_briefing_fails_closed_on_missing_swap_ref():
    cfg = load_presentation(PRESENTATION)
    sections = _sections()
    # A priced class-A play with no catalogue alternative -> the briefing must refuse,
    # not render a play without a Monday action (spec §3.3: missing swap fails closed).
    sections["priced_plays"]["plays"][0]["alternatives"] = []
    with pytest.raises(ValueError, match="swap"):
        build_briefing({"sections": sections}, _manifest(), cfg, _FakeStore(_hits_rows()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k build_briefing -v`
Expected: FAIL with `ImportError: cannot import name 'build_briefing'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/cix/briefing.py` (module-level rank maps + helpers + `build_briefing`):

```python
_EFFORT_ORDER = {"low": 0, "medium": 1, "high": 2}
_OUTCOME_ORDER = {"large": 0, "medium": 1, "small": 2}

def _label(cfg: dict, item_id: str) -> str:
    return cfg["items"].get(item_id, {}).get("business_label", item_id)

def _gloss(cfg: dict, item_id: str) -> str:
    return cfg["items"].get(item_id, {}).get("gloss", "")

def _plays(sections: dict, cfg: dict) -> list[dict]:
    grid = sections["leverage"]["grid"]
    dist = sections["distribution"]["items"]
    priced = {p["item_id"]: p for p in sections["priced_plays"].get("plays", [])}
    cells = [c for c in grid if c.get("remedy_class") == "A"]
    # Tie-break on count (desc) then item_id so the ranking never depends on grid order.
    cells.sort(key=lambda c: (_EFFORT_ORDER.get(c["effort"], 9), _OUTCOME_ORDER.get(c["outcome"], 9),
                              -c.get("count", 0), c["item_id"]))
    rows = []
    for rank, c in enumerate(cells, start=1):
        pid = c["item_id"]
        play = priced.get(pid)
        alt = (play.get("alternatives") or [{}])[0] if play else {}
        if play is not None and not alt.get("substitute"):
            raise ValueError(f"class-A play {pid!r} is priced but has no swap in the catalogue "
                             "(missing alternatives/substitute)")
        rows.append({
            "rank": rank, "item_id": pid, "label": _label(cfg, pid), "gloss": _gloss(cfg, pid),
            "count": c["count"], "unit": dist.get(pid, {}).get("unit"),
            "effort": c["effort"], "outcome": c["outcome"],
            "band": play.get("band") if play else None,
            "monday_action": alt.get("substitute"), "swap_ref": alt.get("swap_ref"),
        })
    return rows

def _upstream(sections: dict, cfg: dict) -> list[dict]:
    dist = sections["distribution"]["items"]
    rows = []
    for c in sections["leverage"].get("class_d", []):
        pid = c["item_id"]
        d = dist.get(pid, {})
        rows.append({"item_id": pid, "label": _label(cfg, pid), "gloss": _gloss(cfg, pid),
                     "count": c["count"], "unit": d.get("unit"), "share": d.get("share")})
    return rows

def _watch_list(sections: dict, cfg: dict) -> list[dict]:
    dist = sections["distribution"]["items"]
    rows = []
    for s in sections["leverage"].get("shelf", []):
        pid = s["item_id"]
        # Route by config polarity (spec §4): positives always go to whats_working,
        # never the watch list — independent of what synthesis emitted.
        if cfg["items"].get(pid, {}).get("polarity") == "positive":
            continue
        d = dist.get(pid, {})
        rows.append({"item_id": pid, "label": _label(cfg, pid), "gloss": _gloss(cfg, pid),
                     "count": s["count"], "unit": s.get("unit"), "share": d.get("share")})
    return rows

def _whats_working(sections: dict, cfg: dict) -> list[dict]:
    dist = sections["distribution"]["items"]
    rows = []
    for f in sections.get("whats_working", []):
        pid = f["item_id"]
        d = dist.get(pid, {})
        rows.append({"item_id": pid, "label": _label(cfg, pid), "gloss": _gloss(cfg, pid),
                     "count": d.get("count"), "share": d.get("share"), "narrative": f.get("narrative")})
    return rows

def _trust(sections: dict, manifest: dict) -> dict:
    dist = sections["distribution"]
    method = sections.get("method", {})
    highlights = sections.get("highlights", [])
    has_quotes = any(f.get("evidence") for f in highlights)
    evidence_note = ("" if has_quotes
                     else "Quote-level evidence pending (next run) — findings currently carry counts only.")
    return {
        "coverage": {"interaction_coverage": dist.get("interaction_coverage"),
                     "eligible_interactions": dist.get("eligible_interactions"),
                     "residual_interactions": dist.get("residual_interactions")},
        "validations": [{"check": v.get("check"), "status": v.get("status")}
                        for v in method.get("validations", [])],
        "drop_summary": method.get("drop_summary", {}),
        "evidence_note": evidence_note,
        "honesty_ladder": manifest.get("corpus_clearance"),
        "manifest_ref": {"corpus_hash": manifest.get("corpus_hash"),
                         "rubric_version": manifest.get("rubric_version"),
                         "catalogue_version": manifest.get("catalogue_version")},
    }

def build_briefing(report: dict, manifest: dict, cfg: dict, store) -> dict:
    """Assemble the business briefing from persisted report sections + manifest + read-only store.
    Model-free; enforces the honesty rules in the spec (§6)."""
    sections = report["sections"]
    dist_items = sections["distribution"]["items"]
    members = cfg["headline_metrics"]["avoidable_contact_rate"]["members"]
    # Honesty rule: the avoidable-contact rate is interaction-unit only. Guard against a member
    # whose unit is anything else so counts can never cross units.
    for m in members:
        unit = dist_items.get(m, {}).get("unit")
        if unit is not None and unit != "interaction":
            raise ValueError(f"avoidable_contact_rate member {m!r} is not interaction-unit ({unit})")
    eligible = sections["distribution"]["eligible_interactions"]
    hits_artifact = manifest["artifacts"]["hits"]
    rate = avoidable_contact_rate(store, hits_artifact, members, eligible)
    rate["honesty"] = manifest.get("corpus_clearance")
    opportunity = automatable_opportunity(sections["leverage"]["grid"], sections["priced_plays"])
    return {
        "meta": {"corpus_clearance": manifest.get("corpus_clearance"),
                 "rubric_version": manifest.get("rubric_version"),
                 "catalogue_version": manifest.get("catalogue_version"),
                 "corpus_hash": manifest.get("corpus_hash")},
        "headline": {"avoidable_contact_rate": rate, "automatable_opportunity": opportunity},
        "whats_working": _whats_working(sections, cfg),
        "plays": _plays(sections, cfg),
        "upstream": _upstream(sections, cfg),
        "watch_list": _watch_list(sections, cfg),
        "trust": _trust(sections, manifest),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k build_briefing -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): assemble briefing blocks with honesty rules + unit-safety guard"
```

---

## Task 5: Config↔rubric version check (fail closed)

**Files:**
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py`:

```python
def test_build_briefing_rejects_rubric_version_mismatch():
    cfg = load_presentation(PRESENTATION)
    manifest = _manifest()
    manifest["rubric_version"] = "2.0.0"  # config requires 1.0.0
    with pytest.raises(ValueError, match="rubric version"):
        build_briefing({"sections": _sections()}, manifest, cfg, _FakeStore(_hits_rows()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k rubric_version_mismatch -v`
Expected: FAIL (no exception raised — test expects `ValueError`)

- [ ] **Step 3: Write minimal implementation**

In `src/cix/briefing.py`, add this guard as the first lines inside `build_briefing` (before `sections = report["sections"]`):

```python
    required = cfg.get("requires", {}).get("rubric_version")
    actual = manifest.get("rubric_version")
    if required != actual:
        raise ValueError(f"presentation config rubric version {required!r} != run rubric version {actual!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -v`
Expected: PASS (all briefing tests)

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): fail closed on config/rubric version mismatch"
```

---

## Task 6: `render_briefing_html` — self-contained HTML

**Files:**
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py` (import `render_briefing_html`):

```python
def test_render_html_is_self_contained_and_shows_key_facts():
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    html = render_briefing_html(b)
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in html and "http://" not in html and "https://" not in html  # self-contained, no external assets
    assert "O1" in html                                   # honesty banner
    assert "Manual after-call admin" in html              # business label
    assert "Capture at the interaction" in html           # Monday action
    assert "2 / 100" in html or "2/100" in html           # avoidable-contact rate value
    assert "4,040" in html and "12,120" in html           # opportunity band, formatted
    assert "pending" in html.lower()                      # evidence-gap note
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k render_html -v`
Expected: FAIL with `ImportError: cannot import name 'render_briefing_html'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/cix/briefing.py`:

```python
def _money(n) -> str:
    return f"{n:,.0f}"

def _esc(s) -> str:
    s = "" if s is None else str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_CSS = """
body{font-family:Helvetica,Arial,sans-serif;color:#1a1a1a;max-width:820px;margin:2rem auto;line-height:1.5}
h1{font-size:1.6rem;margin-bottom:.2rem}.banner{background:#fef3c7;border:1px solid #f59e0b;padding:.5rem .8rem;border-radius:6px;font-size:.85rem;margin:.6rem 0}
h2{font-size:1.15rem;border-bottom:2px solid #e5e7eb;padding-bottom:.2rem;margin-top:1.6rem}
.headline{background:#f0f9ff;border:1px solid #bae6fd;padding:.8rem 1rem;border-radius:8px;margin:.8rem 0}
.big{font-size:1.4rem;font-weight:700}table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid #e5e7eb;vertical-align:top}
.muted{color:#6b7280;font-size:.85rem}.tag{display:inline-block;background:#f3f4f6;border-radius:4px;padding:0 .35rem;font-size:.8rem}
"""

def render_briefing_html(b: dict) -> str:
    """One self-contained HTML string (inline CSS, no external assets)."""
    rate = b["headline"]["avoidable_contact_rate"]
    opp = b["headline"]["automatable_opportunity"]
    out = ["<!DOCTYPE html>", "<html><head><meta charset='utf-8'>",
           f"<style>{_CSS}</style></head><body>"]
    out.append("<h1>Customer Interaction Review</h1>")
    out.append(f"<div class='banner'>{_esc(b['meta']['corpus_clearance'])}</div>")
    # Headline
    out.append("<h2>The one thing to know</h2>")
    out.append("<div class='headline'>")
    out.append(f"<div class='big'>{rate['value']} / {rate['denominator']} contacts matched at least one avoidable pattern</div>")
    out.append(f"<div class='muted'>{_esc(rate['method'])} · resolve with <span class='tag'>{_esc(rate['query'])}</span></div>")
    if opp:
        out.append(f"<div class='big'>${_money(opp['band']['low'])}&ndash;${_money(opp['band']['high'])} / yr indicative automatable opportunity</div>")
        out.append(f"<div class='muted'>{_esc(opp['shared_remedy_note'])}</div>")
    out.append("</div>")
    # What's working
    if b["whats_working"]:
        out.append("<h2>What's working</h2><ul>")
        for w in b["whats_working"]:
            share = f" ({round(w['share']*100)}% of eligible)" if w.get("share") else ""
            out.append(f"<li><b>{_esc(w['label'])}</b> — {w.get('count')}{share}. {_esc(w['gloss'])}</li>")
        out.append("</ul>")
    # Plays
    out.append("<h2>Where the leverage is</h2><table>")
    out.append("<tr><th>#</th><th>What's happening</th><th>How often</th><th>Effort / payoff</th><th>Est. value / yr</th><th>Monday action</th></tr>")
    for p in b["plays"]:
        band = f"${_money(p['band']['low'])}&ndash;${_money(p['band']['high'])}" if p.get("band") else "&mdash;"
        out.append(f"<tr><td>{p['rank']}</td><td><b>{_esc(p['label'])}</b><br><span class='muted'>{_esc(p['gloss'])}</span></td>"
                   f"<td>{p['count']} {_esc(p['unit'])}</td><td>{_esc(p['effort'])} / {_esc(p['outcome'])}</td>"
                   f"<td>{band}</td><td>{_esc(p.get('monday_action'))} <span class='tag'>{_esc(p.get('swap_ref'))}</span></td></tr>")
    out.append("</table>")
    # Upstream
    if b["upstream"]:
        out.append("<h2>Upstream problems worth fixing</h2><ul>")
        for u in b["upstream"]:
            share = f" ({round(u['share']*100)}% of contacts)" if u.get("share") else ""
            out.append(f"<li><b>{_esc(u['label'])}</b> — {u['count']}{share}. {_esc(u['gloss'])}</li>")
        out.append("</ul>")
    # Watch list
    if b["watch_list"]:
        out.append("<h2>Watch list — real, no off-the-shelf remedy yet</h2><ul>")
        for w in b["watch_list"]:
            out.append(f"<li><b>{_esc(w['label'])}</b> — {w['count']} {_esc(w.get('unit'))}. {_esc(w['gloss'])}</li>")
        out.append("</ul>")
    # Trust
    t = b["trust"]
    out.append("<h2>Why you can trust these numbers</h2>")
    cov = t["coverage"]
    out.append(f"<p class='muted'>{round((cov['interaction_coverage'] or 0)*100)}% of {cov['eligible_interactions']} eligible interactions read "
               f"({cov['residual_interactions']} residual). Drops: {t['drop_summary']}.</p>")
    if t["evidence_note"]:
        out.append(f"<p class='muted'>{_esc(t['evidence_note'])}</p>")
    out.append("</body></html>")
    return "\n".join(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k render_html -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): self-contained HTML renderer"
```

---

## Task 7: `render_briefing_pdf` + WeasyPrint optional extra + `--no-pdf`

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/cix/briefing.py`
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Add the optional dependency**

In `pyproject.toml`, add after the `[dependency-groups]` block:

```toml
[project.optional-dependencies]
pdf = ["weasyprint>=62"]
```

Then install it into the dev environment:

Run: `uv sync --extra pdf`
Expected: resolves and installs weasyprint (and its Python deps). If system libs (pango/cairo) are missing, the import test in Step 4 documents the `--no-pdf` fallback path.

- [ ] **Step 2: Write the failing test**

Add to `tests/test_briefing.py` (import `render_briefing_pdf`):

```python
def test_render_pdf_writes_a_pdf_file(tmp_path):
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    html = render_briefing_html(b)
    out = tmp_path / "briefing.pdf"
    try:
        # render_briefing_pdf sets the macOS DYLD shim itself before importing weasyprint,
        # so this genuinely renders where the libs exist; skip only on true absence.
        render_briefing_pdf(html, out)
    except (OSError, ImportError) as e:
        import pytest
        pytest.skip(f"weasyprint/system libs unavailable: {e}")
    assert out.exists() and out.read_bytes()[:5] == b"%PDF-"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k render_pdf -v`
Expected: collection/import error `cannot import name 'render_briefing_pdf'` (the function doesn't exist yet)

- [ ] **Step 4: Write minimal implementation**

Add to `src/cix/briefing.py`:

```python
def render_briefing_pdf(html: str, out_path) -> None:
    """Print the same HTML/CSS to PDF (a faithful 'screenshot-type' view). Imports
    WeasyPrint lazily so core cix installs and runs without it (see --no-pdf).

    macOS: WeasyPrint's cffi dlopen cannot find Homebrew's gobject/pango/cairo unless
    DYLD_FALLBACK_LIBRARY_PATH includes the Homebrew lib dir. find_library re-reads the
    env at call time, so setting it in-process here (before the import) is honored and the
    user needs no env-var wrapper."""
    import os, sys
    if sys.platform == "darwin":
        for libdir in ("/opt/homebrew/lib", "/usr/local/lib"):
            if os.path.isdir(libdir):
                cur = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
                if libdir not in cur.split(":"):
                    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (cur + ":" + libdir).lstrip(":")
    from weasyprint import HTML
    HTML(string=html).write_pdf(str(out_path))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k render_pdf -v`
Expected: PASS on this machine (Homebrew pango/cairo/gdk-pixbuf present; the DYLD shim finds them). SKIP only where the system libs are genuinely absent.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/cix/briefing.py tests/test_briefing.py
git commit -m "feat(briefing): PDF renderer via WeasyPrint (optional 'pdf' extra)"
```

---

## Task 8: `cix query --metric` — resolve a headline metric to its interaction set

**Files:**
- Modify: `src/cix/query.py`
- Modify: `src/cix/cli.py:226-255` (`_cmd_query`) and `src/cix/cli.py:490-495` (query subparser)
- Test: `tests/test_query.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_query.py` (extend imports: `from cix.query import resolve_item, find_quote, resolve_metric`):

```python
def test_resolve_metric_lists_union_interactions(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path)
    # Add a second member hit on a different interaction so the union is 2.
    ha = manifest["artifacts"]["hits"]
    store.write_hit(ha, "status_chase_inbound", "int-002", "interaction", "int-002:0000")
    presentation = {"headline_metrics": {"avoidable_contact_rate":
                    {"members": ["billing_defect_driver", "status_chase_inbound",
                                 "repeat_contact_unresolved", "unanticipated_failure"]}}}
    res = resolve_metric(store, manifest, presentation, "avoidable_contact_rate", eligible=100)
    assert res["found"] is True
    assert res["value"] == 2
    assert sorted(res["interaction_ids"]) == ["int-001", "int-002"]

def test_resolve_metric_unknown_name_fails_closed(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path)
    presentation = {"headline_metrics": {}}
    assert resolve_metric(store, manifest, presentation, "no_such_metric", eligible=100)["found"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_query.py -k resolve_metric -v`
Expected: FAIL with `ImportError: cannot import name 'resolve_metric'`

- [ ] **Step 3: Write minimal implementation**

Add to `src/cix/query.py`:

```python
def resolve_metric(store: Store, manifest: dict, presentation: dict, metric_name: str, eligible: int) -> dict:
    """Resolve a named headline metric to its underlying interaction set (read-only).
    Returns {"found": False} for an unknown metric so the CLI can fail closed."""
    spec = presentation.get("headline_metrics", {}).get(metric_name)
    if spec is None:
        return {"found": False, "metric": metric_name}
    members = set(spec["members"])
    ha = manifest["artifacts"]["hits"]
    # Same union as briefing.avoidable_contact_rate: interaction-unit rows only.
    ids = sorted({h["interaction_id"] for h in store.hits_for(ha)
                  if h["item_id"] in members and h.get("unit") == "interaction"})
    return {"found": True, "metric": metric_name, "value": len(ids),
            "denominator": eligible, "interaction_ids": ids, "members": spec["members"]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_query.py -k resolve_metric -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Wire the CLI**

In `src/cix/cli.py`, update the imports from `cix.query` (currently `from cix.query import resolve_item, find_quote`) to also import `resolve_metric` and `load_presentation`:

```python
from cix.query import resolve_item, find_quote, resolve_metric
from cix.briefing import load_presentation
```

In `_cmd_query` (`src/cix/cli.py:226`), add this branch immediately after the `if args.quote is not None:` block returns and before `report = json.loads(...)`:

```python
    if getattr(args, "metric", None) is not None:
        report = json.loads((run / "report.json").read_text(encoding="utf-8"))
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        eligible = report["sections"]["distribution"]["eligible_interactions"]
        presentation = load_presentation(Path(args.presentation))
        res = resolve_metric(store, manifest, presentation, args.metric, eligible)
        if not res["found"]:
            print(f'metric "{args.metric}" does NOT resolve — unknown headline metric')
            return 1
        print(f"{res['metric']}: {res['value']} / {res['denominator']} "
              f"(members: {', '.join(res['members'])})")
        for iid in res["interaction_ids"]:
            print(f"  {iid}")
        return 0
```

In the query subparser (`src/cix/cli.py:490-495`), add a `--metric` option to the mutually-exclusive group `q_grp`, plus a `--presentation` option on `p_query` itself (not in the group) so `--metric` works outside the repo root:

```python
    q_grp.add_argument("--metric", help="headline metric name: list the interaction set behind it")
    p_query.add_argument("--presentation", default="configs/briefing_presentation_v1.yaml",
                         help="presentation config used by --metric (declares metric membership)")
```

- [ ] **Step 6: Run the CLI end-to-end**

Run: `uv run cix query runs/svc-run --metric avoidable_contact_rate | head -5`
Expected: first line `avoidable_contact_rate: 33 / 100 (members: repeat_contact_unresolved, billing_defect_driver, status_chase_inbound, unanticipated_failure)`, then 33 interaction IDs.

- [ ] **Step 7: Commit**

```bash
git add src/cix/query.py src/cix/cli.py tests/test_query.py
git commit -m "feat(query): --metric resolves a headline metric to its interaction set (R-OUT-2)"
```

---

## Task 9: `cix briefing` CLI + golden + read-only guarantee

**Files:**
- Modify: `src/cix/cli.py` (new `_cmd_briefing` + subparser in `main`)
- Test: `tests/test_briefing.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_briefing.py` (top of file add `import sqlite3` and `from cix.cli import main`):

```python
def test_cli_briefing_on_svc_run_golden(tmp_path):
    # Copy the persisted svc-run into a temp dir so we don't write into the repo fixture.
    import shutil
    src = Path("runs/svc-run")
    run = tmp_path / "svc-run"
    shutil.copytree(src, run)
    drops_before = sqlite3.connect(f"file:{run/'run.db'}?mode=ro", uri=True).execute(
        "SELECT count(*) FROM drop_log").fetchone()[0]

    rc = main(["briefing", str(run), "--no-pdf"])
    assert rc == 0

    briefing = json.loads((run / "briefing.json").read_text(encoding="utf-8"))
    assert briefing["headline"]["avoidable_contact_rate"]["value"] == 33
    assert briefing["headline"]["automatable_opportunity"]["band"] == {"low": 4040.0, "high": 12120.0}
    assert [p["item_id"] for p in briefing["plays"]] == [
        "manual_after_call_work", "deterministic_request", "avoidable_transfer"]
    assert "O1" in briefing["meta"]["corpus_clearance"]

    html = (run / "briefing.html").read_text(encoding="utf-8")
    assert "Manual after-call admin" in html and "33 / 100" in html

    # Read-only guarantee: drop_log unchanged.
    drops_after = sqlite3.connect(f"file:{run/'run.db'}?mode=ro", uri=True).execute(
        "SELECT count(*) FROM drop_log").fetchone()[0]
    assert drops_after == drops_before

def test_cli_briefing_no_pdf_skips_pdf(tmp_path):
    import shutil
    run = tmp_path / "svc-run"
    shutil.copytree(Path("runs/svc-run"), run)
    assert main(["briefing", str(run), "--no-pdf"]) == 0
    assert not (run / "briefing.pdf").exists()

def test_cli_briefing_missing_artifacts_fail_closed(tmp_path):
    # Spec §3.3: a dir without persisted artifacts fails closed with a message, no traceback.
    empty = tmp_path / "not-a-run"
    empty.mkdir()
    assert main(["briefing", str(empty), "--no-pdf"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_briefing.py -k cli_briefing -v`
Expected: FAIL with `SystemExit: 2` / `invalid choice: 'briefing'`

- [ ] **Step 3: Write the CLI command**

In `src/cix/cli.py`, add `_cmd_briefing` next to `_cmd_query` (after line 255). It reads persisted artifacts read-only (like `_cmd_query`) and writes the three files:

```python
def _cmd_briefing(args) -> int:
    """Business briefing (model-free presentation layer). Read-only over a persisted run:
    build briefing.json + briefing.html (+ briefing.pdf unless --no-pdf)."""
    from cix.briefing import build_briefing, render_briefing_html, render_briefing_pdf
    run = Path(args.run)
    for req in ("run.db", "report.json", "manifest.json"):
        if not (run / req).exists():
            print(f"briefing failed closed: missing persisted artifact {run / req}")
            return 1
    store = open_store(run / "run.db", read_only=True)  # writes impossible, not merely avoided
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    cfg = load_presentation(Path(args.presentation))
    try:
        briefing = build_briefing(report, manifest, cfg, store)
    except ValueError as e:
        print(f"briefing failed closed: {e}")
        return 1
    (run / "briefing.json").write_text(json.dumps(briefing, indent=2, ensure_ascii=False), encoding="utf-8")
    html = render_briefing_html(briefing)
    (run / "briefing.html").write_text(html, encoding="utf-8")
    if not args.no_pdf:
        render_briefing_pdf(html, run / "briefing.pdf")
    print(json.dumps({"run": str(run), "avoidable_contact_rate": briefing["headline"]["avoidable_contact_rate"]["value"],
                      "pdf": (not args.no_pdf)}))
    return 0
```

- [ ] **Step 4: Register the subparser**

In `main` (`src/cix/cli.py`), add after the `p_query` block (line ~495):

```python
    p_brief = sub.add_parser("briefing", help="render a business-facing briefing from a persisted run (read-only)")
    p_brief.add_argument("run")
    p_brief.add_argument("--presentation", default="configs/briefing_presentation_v1.yaml")
    p_brief.add_argument("--no-pdf", action="store_true", help="skip the PDF (no WeasyPrint needed)")
    p_brief.set_defaults(fn=_cmd_briefing)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_briefing.py -k cli_briefing -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Run the full suite + a live PDF render**

Run: `uv run pytest -q`
Expected: all pass (PDF test may SKIP if weasyprint/system-libs unavailable).

Run: `uv run cix briefing runs/svc-run && ls runs/svc-run/briefing.*`
Expected: prints the JSON summary and lists `briefing.html`, `briefing.json`, `briefing.pdf` (if weasyprint installed). Open `runs/svc-run/briefing.html` to eyeball it.

- [ ] **Step 7: Commit**

```bash
git add src/cix/cli.py tests/test_briefing.py
git commit -m "feat(briefing): cix briefing CLI — briefing.json + HTML + PDF from a persisted run"
```

---

## Task 10: Docs — wire the briefing into README + demo runbook

**Files:**
- Modify: `README.md`
- Modify: `docs/demo_runbook.md`

- [ ] **Step 1: Update the demo runbook**

In `docs/demo_runbook.md`, add a new section after §2 (the count-resolves-to-source moment):

```markdown
## 2b. The business briefing — same run, commercial view

```
uv run cix briefing runs/svc-run
```

Opens `runs/svc-run/briefing.html` (and `briefing.pdf`): one headline number — **33 of 100
contacts matched at least one avoidable pattern** (a distinct-interaction union, resolvable
with `cix query runs/svc-run --metric avoidable_contact_rate`), the three low-effort automatable
plays with an indicative **$4,040–$12,120/yr** band (inferred, not operator-confirmed), and the
same O1 honesty banner. The technical `report.pdf` remains the audit deliverable; this is the
first-engagement view rendered from the same persisted run.
```

- [ ] **Step 2: Update the README status/next-action**

In `README.md`, add a bullet to the Pipeline/Status area noting the new deliverable. Under the `## Documents` table add a row:

```markdown
| [`docs/superpowers/specs/2026-08-04-business-briefing-report-design.md`](docs/superpowers/specs/2026-08-04-business-briefing-report-design.md) | **Business briefing design** — model-free presentation layer (`cix briefing`) rendering a persisted run for a commercial reader |
```

- [ ] **Step 3: Verify the runbook command block is accurate**

Run: `uv run cix briefing runs/svc-run && uv run cix query runs/svc-run --metric avoidable_contact_rate | head -1`
Expected: briefing writes (append `--no-pdf` if WeasyPrint's system libs are absent); the metric line reads `avoidable_contact_rate: 33 / 100 (...)`.

`runs/svc-run` is a git-tracked fixture, so the generated `briefing.*` files are committed as demo assets in Step 4 (the runbook links `briefing.html` directly) rather than left untracked.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/demo_runbook.md runs/svc-run/briefing.*
git commit -m "docs(briefing): add cix briefing to README + runbook; commit demo briefing artifacts"
```

---

## Self-Review notes (for the implementer)

- **Spec coverage:** config artifact incl. polarity (T1) · metric ① union, unit-filtered (T2) · metric ② gated dollar (T3) · block assembly + honesty rules + unit-safety + missing-swap-ref fail-closed (T4) · version fail-closed (T5) · HTML (T6) · PDF-from-HTML + optional dep + `--no-pdf` (T7) · `cix query --metric` (T8) · `cix briefing` CLI + golden + read-only + missing-artifact fail-closed (T9) · docs + committed demo artifacts (T10). Every spec §4–§9 item maps to a task.
- **Honesty rules (spec §6):** no cross-sum → `unit == "interaction"` filter inside the union itself (T2) + config-level member guard (T4); union-not-sum → T2; formula+query handle on every headline number → T2/T3 fields + T8; O-level banner → T4/T6; honest empty state → T3 (no catalogue); evidence-gap note → T4/T6. §6.5's all-zero-member omission is consciously deferred: the v1 config always declares four members, and a zero-valued union renders honestly as `0 / N` with its formula and query handle.
- **Polarity routing:** the watch list excludes positives via the config's `polarity` field (T1/T4), never via `whats_working` membership — presentation does not depend on synthesis output.
- **`--metric` read-only (spec §9.6):** guaranteed structurally — `_cmd_query` opens the store `mode=ro`, so any write raises; no separate drop_log test needed.
- **Type consistency:** `avoidable_contact_rate(store, hits_artifact, members, eligible)`, `automatable_opportunity(leverage_grid, priced_plays)`, `build_briefing(report, manifest, cfg, store)`, `render_briefing_html(briefing)`, `render_briefing_pdf(html, out_path)`, `resolve_metric(store, manifest, presentation, metric_name, eligible)` — signatures are stable across the tasks that call them.
- **Frozen instrument:** no task touches synthesis, aggregation, the evidence gate, thresholds, or `report.*` rendering. `report.json`/`report.pdf` are read, never rewritten.
