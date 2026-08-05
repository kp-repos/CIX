# CFPB Comparative Briefing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the CIX pipeline on real CFPB complaint data (Block, Inc. vs Bank of America, 2024+, 2,500-narrative pilot per side) and render a comparative business briefing with a withheld-ground-truth reveal.

**Architecture:** A new CFPB ingest adapter converts CSV rows into the existing corpus contract (a directory of `InteractionUnit` JSON files) — the calibrated pipeline is untouched. The outcome label is diverted to a sidecar at ingest and never enters the store. A new model-free `cix compare` layer builds per-side briefings via the existing `build_briefing` and renders a side-by-side artifact whose closing block unseals the withheld label. Substrate-class governance (PRD patch v2.1, ratified 2026-08-05) is enforced via corpus-properties manifest fields, a `requires_speaker` skip rule, and a substrate-aware self-test outcome level.

**Tech Stack:** Python 3.12 · uv · pytest · pydantic v2 · PyYAML · SQLite · WeasyPrint (optional PDF)

**Spec:** `docs/superpowers/specs/2026-08-05-cfpb-comparative-briefing-design.md`

**Verified facts the plan relies on** (checked 2026-08-05):
- CSV: `~/corpora/open/cfpb/cfpb_narratives_filtered.csv`, columns include `Date received` (mixed `2025-07-15T12:57:20.000Z` and bare `2015-03-19` formats), `Consumer complaint narrative`, `Company`, `Company response to consumer`, `Complaint ID` (float-artifact strings like `21890776.0`).
- Exact company values: `Block, Inc.` (48,376 rows all-time) and `BANK OF AMERICA, NATIONAL ASSOCIATION` (58,442 rows all-time).
- Corpus contract: `load_corpus(dir)` globs `*.json` **non-recursively** and validates each file as an `InteractionUnit` — so sidecar/properties files must not sit in the units directory. Layout used here: `<out>/units/*.json` + `<out>/holdout_labels.json` + `<out>/corpus_properties.yaml`.
- `build_briefing(report, manifest, cfg, store)` hardcodes `cfg["headline_metrics"]["avoidable_contact_rate"]`; `_cmd_briefing` prints that key. Task 8 generalizes both while preserving the existing key and goldens.
- Presentation `requires.rubric_version` alone cannot distinguish two rubrics that both say `"1.0.0"` — Task 8 adds a `rubric_file` binding (same precedent as `load_paraphrase_set`).

---

## File structure

| File | Responsibility |
|---|---|
| `docs/reference/CIX_PRD_Patch_HANDOFF_2026-08-03.md` (new, vendored) | Ratified patch text — the governance source |
| `docs/reference/CIX_Corpus_Sourcing_Memo_2026-08-03.md` (new, vendored) | Corpus evidence base |
| `docs/CIX_PRD_v1_2026-07-31.md` (modify) | Patch v2.1 applied → PRD v1.3 |
| `docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md` (modify) | Design record rev 2.3 → 2.4 back-propagation |
| `src/cix/normalize.py` (modify) | + `load_corpus_properties()` |
| `src/cix/rubric.py` (modify) | + `requires_speaker` on `RubricItem` |
| `src/cix/cli.py` (modify) | corpus-fit skip rule, manifest fields, substrate-aware selftest note, `cfpb-ingest` + `compare` subcommands, briefing metric generalization |
| `src/cix/cfpb.py` (new) | CFPB CSV → corpus adapter (parse, filter, dedup, sample, write, withhold) |
| `src/cix/briefing.py` (modify) | generic headline-metric loop + `rubric_file` binding |
| `src/cix/compare.py` (new) | comparative briefing builder + HTML renderer |
| `configs/complaint_rubric_v1.yaml` (new) | Complaint-shaped rubric, 9 items |
| `configs/briefing_presentation_complaint_v1.yaml` (new) | Business labels + `unremediated_loss_rate` |
| `docs/cfpb_pilot_runbook.md` (new) | Operator commands for the live pilot |
| `tests/test_cfpb.py`, `tests/test_complaint_rubric.py`, `tests/test_compare.py`, `tests/test_corpus_fit.py` (new) | Task-level tests |

---

### Task 1: Governance — vendor the source docs, apply patch v2.1, back-propagate

Docs-only task; no code. The patch was ratified by KP on 2026-08-05 (spec §0). All paste-ready
markdown blocks live in the patch file itself — vendor it first so the repo stays self-contained.

**Files:**
- Create: `docs/reference/CIX_PRD_Patch_HANDOFF_2026-08-03.md` (copy)
- Create: `docs/reference/CIX_Corpus_Sourcing_Memo_2026-08-03.md` (copy)
- Modify: `docs/CIX_PRD_v1_2026-07-31.md`
- Modify: `docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md`
- Modify: `README.md`

- [ ] **Step 1: Vendor the two source documents**

```bash
cp "/Users/vajrapani/Library/Mobile Documents/com~apple~CloudDocs/Claude COWORK/CLAUDE OUTPUTS/agentic-build/cix/CIX_PRD_Patch_HANDOFF_2026-08-03.md" docs/reference/
cp "/Users/vajrapani/Library/Mobile Documents/com~apple~CloudDocs/Claude COWORK/CLAUDE OUTPUTS/agentic-build/cix/CIX_Corpus_Sourcing_Memo_2026-08-03.md" docs/reference/
```

Then edit the vendored patch header: change `**Status:** ⛔ **NOT YET RATIFIED BY KP.**` to
`**Status:** ✅ RATIFIED BY KP 2026-08-05 — applied to PRD v1.3 in the same pass.`

- [ ] **Step 2: Apply the five amendments to the PRD**

In `docs/CIX_PRD_v1_2026-07-31.md`:
1. **P1** — replace the §10 "Risk 2" clause with the P1 block from the vendored patch §B (fallback costs + corpus fit/no-fit gate + `D-11 corpus line: $0 for v1`).
2. **P2** — replace the D-1 open-register row with the RESOLVED row from patch §B/P2.
3. **P3** — insert the full `2.3-S · Substrate rule (normative)` block (substrate classes S1–S4, S2-serves-O3-for-corpus-level-items correction, licence-tier separation, corpus-property table) into §2.3, verbatim from patch §B/P3.
4. **P4** — insert the `R-SPK-1…3` requirement family (patch §B/P4) as a new requirement group; note the v1 ruling: `speaker_attribution: none` is the v1 path, inference deferred to v1.5.
5. **P5** — insert `R-IDX-8/9/10` (shadow files, dedup, redaction tokens) beside the existing R-IDX requirements.
6. Bump the PRD version line to **v1.3** and add a changelog entry:
   `2026-08-05 — Patch v2.1 applied (ratified by KP): substrate rule 2.3-S, R-SPK family, R-IDX-8..10, D-1 resolved, D-11 corpus line $0. §E rulings: speaker option (b) v1; NC route approved for internal O2/O3; Twitter CS acquisition confirmed; S2 serves O3 for corpus-level items only.`

- [ ] **Step 3: Back-propagate the design record**

In `docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md`: bump rev 2.3 → **rev 2.4**; amend D§10 with the
substrate taxonomy, licence/outcome separation, corpus-property gating and speaker-attribution
family (summarize the P3/P4 rulings, citing PRD v1.3 §2.3-S); record the D-1 resolution against the
acquired corpora; add a dated changelog entry. Note explicitly (patch §C): the "Author order ≠ run
order" ruling **survives unchanged**.

- [ ] **Step 4: De-stale the README**

In `README.md`, update the Status row and "Next action" section: G5 is no longer "gated only on the
FS corpus (OD-1)". New text for the gate sentence:

> Next gate: **G5 (first real run)** — three real corpora acquired (see
> `docs/reference/CIX_Corpus_Sourcing_Memo_2026-08-03.md`); first run is the CFPB pilot,
> Block, Inc. vs Bank of America 2024+, per
> `docs/superpowers/specs/2026-08-05-cfpb-comparative-briefing-design.md`.

- [ ] **Step 5: Commit**

```bash
git add docs/ README.md
git commit -m "docs(governance): apply ratified PRD patch v2.1 — substrate rule, R-SPK, R-IDX-8..10; design record rev 2.4"
```

---

### Task 2: Corpus properties loader + manifest fields

**Files:**
- Modify: `src/cix/normalize.py`
- Modify: `src/cix/cli.py` (in `_cmd_run`, manifest assembly around line 167)
- Test: `tests/test_corpus_fit.py` (new)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_corpus_fit.py
import yaml
from pathlib import Path
from cix.normalize import load_corpus_properties, DEFAULT_CORPUS_PROPERTIES

def test_default_properties_when_no_file(tmp_path):
    props = load_corpus_properties(tmp_path)
    assert props == DEFAULT_CORPUS_PROPERTIES
    assert props["substrate_class"] == "unspecified"

def test_properties_load_from_corpus_dir(tmp_path):
    (tmp_path / "corpus_properties.yaml").write_text(yaml.safe_dump({
        "substrate_class": "S2", "licence_tier": "public-domain",
        "speaker_attribution": "none", "economic_signal": "present",
        "ivr_structure": "absent"}), encoding="utf-8")
    props = load_corpus_properties(tmp_path)
    assert props["substrate_class"] == "S2"
    assert props["licence_tier"] == "public-domain"

def test_properties_load_from_parent_dir(tmp_path):
    # units live in <out>/units; properties sit one level up (adapter layout)
    units = tmp_path / "units"
    units.mkdir()
    (tmp_path / "corpus_properties.yaml").write_text(yaml.safe_dump({
        "substrate_class": "S2", "licence_tier": "public-domain",
        "speaker_attribution": "none", "economic_signal": "present",
        "ivr_structure": "absent"}), encoding="utf-8")
    assert load_corpus_properties(units)["substrate_class"] == "S2"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_corpus_fit.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_corpus_properties'`

- [ ] **Step 3: Implement in `src/cix/normalize.py`**

Append:

```python
import yaml

# Recorded per PRD v1.3 §2.3-S. "unspecified" is the honest legacy default: it maps to
# the strictest posture downstream (no O3, O1-synthetic outcome level).
DEFAULT_CORPUS_PROPERTIES = {
    "substrate_class": "unspecified",
    "licence_tier": "unspecified",
    "speaker_attribution": "none",
    "economic_signal": "redacted",
    "ivr_structure": "absent",
}

def load_corpus_properties(corpus_dir: Path) -> dict:
    """PRD v1.3 §2.3-S corpus-property record. Looks in the corpus dir, then its parent
    (the adapter writes units to <out>/units with properties at <out>/). Absent file ->
    honest defaults, never an error."""
    for cand in (Path(corpus_dir) / "corpus_properties.yaml",
                 Path(corpus_dir).parent / "corpus_properties.yaml"):
        if cand.exists():
            loaded = yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
            return {**DEFAULT_CORPUS_PROPERTIES, **loaded}
    return dict(DEFAULT_CORPUS_PROPERTIES)
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_corpus_fit.py -v` — Expected: 3 PASS

- [ ] **Step 5: Record properties in the run manifest**

In `src/cix/cli.py` `_cmd_run`: import `load_corpus_properties` from `cix.normalize`; right after
`units = load_corpus(Path(args.corpus))` add:

```python
    corpus_props = load_corpus_properties(Path(args.corpus))
```

and in the `manifest.update({...})` call add two entries:

```python
                     "corpus_properties": corpus_props,
                     "substrate_class": corpus_props["substrate_class"],
```

Add a CLI-level test in `tests/test_corpus_fit.py` (reuse the fixture-corpus pattern from
`tests/test_cli.py` — copy its smallest end-to-end `cix run`/`cix index` fixture setup; if only
`cix index` is cheap enough offline, assert via a direct `build_manifest`+update path instead):

```python
def test_run_manifest_carries_substrate_class(tmp_path, monkeypatch):
    # Follow tests/test_cli.py's existing offline `cix run` fixture (ScriptedClient / monkeypatched
    # make_client). Point it at a corpus dir that has a corpus_properties.yaml with S2, run, then:
    #   manifest = json.loads((out / "manifest.json").read_text())
    #   assert manifest["substrate_class"] == "S2"
    #   assert manifest["corpus_properties"]["licence_tier"] == "public-domain"
    ...
```

(Write it against the real fixture pattern found in `tests/test_cli.py` — the test must actually
execute, not stay a stub.)

- [ ] **Step 6: Run full suite, commit**

Run: `uv run pytest -x -q` — Expected: all green.

```bash
git add src/cix/normalize.py src/cix/cli.py tests/test_corpus_fit.py
git commit -m "feat(substrate): corpus_properties.yaml loader + manifest substrate fields (PRD v1.3 §2.3-S)"
```

---

### Task 3: `requires_speaker` skip rule (R-SPK-3)

**Files:**
- Modify: `src/cix/rubric.py` (RubricItem)
- Modify: `src/cix/cli.py` (`_cmd_run`)
- Test: `tests/test_corpus_fit.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_corpus_fit.py
from cix.rubric import Rubric, RubricItem, split_by_corpus_fit

def _item(iid, requires_speaker=False):
    return RubricItem(id=iid, description="d", polarity="negative",
                      unit_of_count="interaction", criterion="c",
                      requires_speaker=requires_speaker)

def test_requires_speaker_defaults_false():
    assert _item("a").requires_speaker is False

def test_split_by_corpus_fit_skips_speaker_items_on_speakerless_corpus():
    r = Rubric(version="1.0.0", requires={}, items=[
        _item("plain"), _item("needs_spk", requires_speaker=True)])
    active, skipped = split_by_corpus_fit(r, {"speaker_attribution": "none"})
    assert [i.id for i in active.items] == ["plain"]
    assert [i.id for i in skipped] == ["needs_spk"]
    assert active.version == "1.0.0"

def test_split_by_corpus_fit_keeps_all_when_speakers_native():
    r = Rubric(version="1.0.0", requires={}, items=[
        _item("plain"), _item("needs_spk", requires_speaker=True)])
    active, skipped = split_by_corpus_fit(r, {"speaker_attribution": "native"})
    assert len(active.items) == 2 and skipped == []
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_corpus_fit.py -v` — Expected: FAIL (no `requires_speaker`, no `split_by_corpus_fit`)

- [ ] **Step 3: Implement**

In `src/cix/rubric.py`, add to `RubricItem`:

```python
    requires_speaker: bool = False   # R-SPK-3: skipped (and reported) on speakerless corpora
```

and add module function:

```python
def split_by_corpus_fit(rubric: Rubric, corpus_props: dict) -> tuple[Rubric, list[RubricItem]]:
    """R-SPK-3 / §2.3-S corpus-property gate: items whose declared dependencies the corpus
    lacks are skipped and reported — never evaluated against absent data. Coverage
    denominators exclude skipped items (they simply never reach detection)."""
    if corpus_props.get("speaker_attribution") != "none":
        return rubric, []
    active = [i for i in rubric.items if not i.requires_speaker]
    skipped = [i for i in rubric.items if i.requires_speaker]
    return Rubric(version=rubric.version, requires=rubric.requires, items=active), skipped
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_corpus_fit.py -v` — Expected: PASS

- [ ] **Step 5: Wire into `_cmd_run`**

In `src/cix/cli.py`, import `split_by_corpus_fit`; after the rubric loads (and after
`corpus_props` from Task 2), before any model call:

```python
    rubric, skipped_items = split_by_corpus_fit(rubric, corpus_props)
```

and after the store is opened (after `store = open_store(db)`):

```python
    for it in skipped_items:
        store.write_validation("CORPUS-FIT", it.id, "skipped",
                               f"requires_speaker=true but corpus speaker_attribution="
                               f"{corpus_props['speaker_attribution']} — skipped per §2.3-S, "
                               "excluded from coverage denominators")
```

Add manifest entry inside the existing `manifest.update({...})`:

```python
                     "skipped_items": [i.id for i in skipped_items],
```

- [ ] **Step 6: Run full suite, commit**

Run: `uv run pytest -x -q` — Expected: green (existing rubrics have no `requires_speaker` keys → default False, nothing skips).

```bash
git add src/cix/rubric.py src/cix/cli.py tests/test_corpus_fit.py
git commit -m "feat(substrate): requires_speaker skip-and-report gate (R-SPK-3)"
```

---

### Task 4: Substrate-aware self-test outcome level

**Files:**
- Modify: `src/cix/cli.py` (`_cmd_selftest`, the hardcoded `outcome_level=O1-synthetic-until-real-corpus`)
- Test: `tests/test_cli_selftest.py` (extend)

- [ ] **Step 1: Write the failing test**

Find the existing selftest CLI test in `tests/test_cli_selftest.py` and its run-dir fixture. Add:

```python
def test_selftest_outcome_level_follows_substrate_class(...):
    # Reuse the existing fixture run dir; edit its manifest.json to set
    # "substrate_class": "S2" before invoking `cix self-test`.
    # Assert the T-SST validation detail contains
    # "outcome_level=O3-corpus-level-items-only" (not O1-synthetic).
    ...
```

Also assert the legacy case: manifest without `substrate_class` → detail contains
`outcome_level=O1-synthetic`. (Write both as real executable tests against the existing fixture.)

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli_selftest.py -v` — Expected: new tests FAIL

- [ ] **Step 3: Implement**

In `_cmd_selftest`, replace the hardcoded string. Above the `store.write_validation("T-SST", ...)`
call add:

```python
    outcome_level = {"S1": "O3-eligible",
                     "S2": "O3-corpus-level-items-only"}.get(
        manifest.get("substrate_class"), "O1-synthetic")
```

and use `f"... spec={spec.version} outcome_level={outcome_level}"` in the detail string.

- [ ] **Step 4: Run to verify pass, commit**

Run: `uv run pytest tests/test_cli_selftest.py -q` then `uv run pytest -x -q` — Expected: green.

```bash
git add src/cix/cli.py tests/test_cli_selftest.py
git commit -m "feat(substrate): self-test outcome level derived from manifest substrate_class"
```

---

### Task 5: CFPB adapter — date parsing, filtering, dedup, sampling

**Files:**
- Create: `src/cix/cfpb.py`
- Test: `tests/test_cfpb.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cfpb.py
import csv
from pathlib import Path
import pytest
from cix.cfpb import (parse_received, read_filtered, dedup_rows, sample_stratified)

def test_parse_received_handles_both_formats():
    assert parse_received("2025-07-15T12:57:20.000Z") == "2025-07-15"
    assert parse_received("2015-03-19") == "2015-03-19"

def test_parse_received_rejects_garbage():
    with pytest.raises(ValueError):
        parse_received("07/15/2025")

FIELDS = ["Date received", "Product", "Sub-product", "Issue", "Sub-issue",
          "Consumer complaint narrative", "Company public response", "Company",
          "State", "ZIP code", "Tags", "Submitted via", "Date sent to company",
          "Company response to consumer", "Timely response?", "Complaint ID"]

def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**{k: "" for k in FIELDS}, **r})

def _row(cid, company="Block, Inc.", date="2024-06-01T10:00:00.000Z",
         narrative="I was charged twice and nobody replied.",
         response="Closed with explanation"):
    return {"Complaint ID": cid, "Company": company, "Date received": date,
            "Consumer complaint narrative": narrative,
            "Company response to consumer": response}

def test_read_filtered_by_company_and_date_with_drop_counts(tmp_path):
    p = tmp_path / "c.csv"
    _write_csv(p, [
        _row("1.0"),
        _row("2.0", company="Other Co"),                       # wrong company
        _row("3.0", date="2023-12-31"),                        # before window
        _row("4.0", narrative=""),                             # no narrative
        _row("5.0", date="not-a-date"),                        # unparseable
    ])
    rows, drops = read_filtered(p, company="Block, Inc.", since="2024-01-01")
    assert [r["complaint_id"] for r in rows] == ["1"]          # '.0' artifact stripped
    assert drops == {"wrong_company": 1, "before_window": 1,
                     "empty_narrative": 1, "bad_date": 1}
    assert rows[0]["date"] == "2024-06-01"
    assert rows[0]["outcome"] == "Closed with explanation"

def test_dedup_rows_collapses_identical_narratives():
    rows = [
        {"complaint_id": "1", "narrative": "same text", "date": "2024-01-05"},
        {"complaint_id": "2", "narrative": "same text", "date": "2024-01-06"},
        {"complaint_id": "3", "narrative": "different", "date": "2024-01-07"},
    ]
    kept, n_dupes = dedup_rows(rows)
    assert [r["complaint_id"] for r in kept] == ["1", "3"]     # first id wins
    assert n_dupes == 1

def test_sample_stratified_is_deterministic_and_month_proportional():
    rows = ([{"complaint_id": str(i), "date": "2024-01-15", "narrative": f"a{i}"} for i in range(80)]
            + [{"complaint_id": str(100 + i), "date": "2024-02-15", "narrative": f"b{i}"} for i in range(20)])
    s1 = sample_stratified(rows, n=10, seed=42)
    s2 = sample_stratified(rows, n=10, seed=42)
    assert s1 == s2                                            # same seed, same slice
    months = [r["date"][:7] for r in s1]
    assert months.count("2024-01") == 8 and months.count("2024-02") == 2
    assert sample_stratified(rows, n=10, seed=43) != s1        # seed matters

def test_sample_stratified_returns_all_when_n_exceeds_population():
    rows = [{"complaint_id": "1", "date": "2024-01-15", "narrative": "x"}]
    assert len(sample_stratified(rows, n=10, seed=1)) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cfpb.py -v` — Expected: FAIL — `ModuleNotFoundError: cix.cfpb`

- [ ] **Step 3: Implement `src/cix/cfpb.py` (adapter core)**

```python
"""CFPB Consumer Complaints -> CIX corpus adapter (spec 2026-08-05 §3).

Converts filtered-CSV rows into the standard corpus contract (a directory of
InteractionUnit JSON files) so the calibrated pipeline stays untouched. The outcome
label `Company response to consumer` is semi-ground-truth: it is diverted to a sealed
sidecar at ingest and never enters any unit file, store, or model context (§3.2).
"""
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
import yaml

# Full ISO-8601 timestamp on recent rows, bare date on older ones (memo §4): both are
# accepted explicitly; anything else is a counted drop, never a silent NaT (R-IDX class).
_ISO_TS = re.compile(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}")
_BARE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")

def parse_received(s: str) -> str:
    for rx in (_ISO_TS, _BARE):
        m = rx.match(s or "")
        if m:
            return m.group(1)
    raise ValueError(f"unparseable Date received: {s!r}")

def _norm_id(cid: str) -> str:
    return cid[:-2] if cid.endswith(".0") else cid   # float-artifact IDs like '21890776.0'

def read_filtered(csv_path: Path, company: str, since: str) -> tuple[list[dict], dict]:
    """Rows for one company from `since` (YYYY-MM-DD), with per-reason drop counts."""
    rows, drops = [], Counter()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Company"] != company:
                drops["wrong_company"] += 1
                continue
            narrative = (r["Consumer complaint narrative"] or "").strip()
            if not narrative:
                drops["empty_narrative"] += 1
                continue
            try:
                date = parse_received(r["Date received"])
            except ValueError:
                drops["bad_date"] += 1
                continue
            if date < since:
                drops["before_window"] += 1
                continue
            rows.append({"complaint_id": _norm_id(r["Complaint ID"]), "date": date,
                         "narrative": narrative, "product": r.get("Product", ""),
                         "issue": r.get("Issue", ""),
                         "outcome": r["Company response to consumer"]})
    rows.sort(key=lambda r: r["complaint_id"])
    return rows, dict(drops)

def dedup_rows(rows: list[dict]) -> tuple[list[dict], int]:
    """R-IDX-9: content-hash dedup before anything counts. First complaint_id wins."""
    seen, kept = set(), []
    for r in sorted(rows, key=lambda r: r["complaint_id"]):
        h = hashlib.sha256(r["narrative"].encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        kept.append(r)
    return kept, len(rows) - len(kept)

def sample_stratified(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Deterministic month-stratified sample: proportional allocation (largest remainder),
    seeded draw within each stratum, output sorted by complaint_id."""
    if n >= len(rows):
        return sorted(rows, key=lambda r: r["complaint_id"])
    strata: dict[str, list[dict]] = {}
    for r in rows:
        strata.setdefault(r["date"][:7], []).append(r)
    total = len(rows)
    quotas = {m: (n * len(v)) / total for m, v in strata.items()}
    alloc = {m: int(q) for m, q in quotas.items()}
    remainder = n - sum(alloc.values())
    for m in sorted(strata, key=lambda m: (-(quotas[m] - alloc[m]), m))[:remainder]:
        alloc[m] += 1
    rng = random.Random(seed)
    out = []
    for m in sorted(strata):
        pool = sorted(strata[m], key=lambda r: r["complaint_id"])
        out.extend(rng.sample(pool, min(alloc[m], len(pool))))
    return sorted(out, key=lambda r: r["complaint_id"])
```

- [ ] **Step 4: Run to verify pass, commit**

Run: `uv run pytest tests/test_cfpb.py -v` — Expected: PASS

```bash
git add src/cix/cfpb.py tests/test_cfpb.py
git commit -m "feat(cfpb): adapter core — mixed-format dates, company/window filter, dedup, stratified sampler"
```

---

### Task 6: CFPB adapter — corpus writer with label withholding

**Files:**
- Modify: `src/cix/cfpb.py`
- Test: `tests/test_cfpb.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_cfpb.py
import yaml
from cix.cfpb import write_corpus
from cix.normalize import load_corpus, load_corpus_properties

def _sample_rows():
    return [
        {"complaint_id": "101", "date": "2024-03-01", "narrative": "Charged twice, refund refused.",
         "product": "Money transfer", "issue": "Fraud or scam",
         "outcome": "Closed with monetary relief"},
        {"complaint_id": "102", "date": "2024-04-02", "narrative": "Account frozen for weeks.",
         "product": "Checking account", "issue": "Managing an account",
         "outcome": "Closed with explanation"},
    ]

def test_write_corpus_layout_and_units_validate(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="cfpb_narratives_filtered.csv")
    units = load_corpus(out / "units")                 # validates the corpus contract
    assert [u.id for u in units] == ["cfpb-101", "cfpb-102"]
    assert units[0].source_type == "note"
    assert units[0].segments[0].text == "Charged twice, refund refused."
    assert units[0].date == "2024-03-01"

def test_write_corpus_withholds_outcome_label(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    for p in (out / "units").glob("*.json"):
        text = p.read_text(encoding="utf-8")
        assert "monetary relief" not in text            # label never in a unit file
        assert "Company response" not in text
    labels = json.loads((out / "holdout_labels.json").read_text(encoding="utf-8"))
    assert labels["cfpb-101"] == "Closed with monetary relief"
    assert labels["cfpb-102"] == "Closed with explanation"

def test_write_corpus_writes_s2_properties(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    props = load_corpus_properties(out / "units")       # parent lookup
    assert props["substrate_class"] == "S2"
    assert props["licence_tier"] == "public-domain"
    assert props["speaker_attribution"] == "none"
    raw = yaml.safe_load((out / "corpus_properties.yaml").read_text(encoding="utf-8"))
    assert raw["sampling"]["seed"] == 42 and raw["sampling"]["company"] == "Block, Inc."
```

Note `json` is already imported at the top of the test file? If not, add `import json`.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cfpb.py -v` — Expected: FAIL — no `write_corpus`

- [ ] **Step 3: Implement `write_corpus` in `src/cix/cfpb.py`**

```python
def write_corpus(rows: list[dict], out_dir: Path, company: str, since: str,
                 seed: int, source_csv: str) -> dict:
    """Write the standard corpus layout:
        <out>/units/cfpb-<id>.json      InteractionUnit files (the ONLY thing the pipeline reads)
        <out>/holdout_labels.json       withheld outcome label, sealed sidecar (§3.2)
        <out>/corpus_properties.yaml    §2.3-S record + sampling provenance
    The units dir holds nothing but unit JSON — load_corpus globs *.json in that dir."""
    units_dir = Path(out_dir) / "units"
    units_dir.mkdir(parents=True, exist_ok=False)   # refuse to clobber an existing corpus
    labels = {}
    for r in rows:
        uid = f"cfpb-{r['complaint_id']}"
        labels[uid] = r["outcome"]
        unit = {"id": uid, "source_type": "note", "participants": [],
                "date": r["date"], "account_id": None, "thread_id": None,
                "segments": [{"speaker": None, "ts": None, "text": r["narrative"]}]}
        (units_dir / f"{uid}.json").write_text(
            json.dumps(unit, indent=2, ensure_ascii=False), encoding="utf-8")
    (Path(out_dir) / "holdout_labels.json").write_text(
        json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")
    props = {"substrate_class": "S2", "licence_tier": "public-domain",
             "speaker_attribution": "none", "economic_signal": "present",
             "ivr_structure": "absent",
             "source": {"dataset": "CFPB Consumer Complaint Database (filtered)",
                        "csv": source_csv},
             "sampling": {"company": company, "since": since, "seed": seed,
                          "n": len(rows)}}
    (Path(out_dir) / "corpus_properties.yaml").write_text(
        yaml.safe_dump(props, sort_keys=False), encoding="utf-8")
    return {"units": len(rows), "out": str(out_dir)}
```

- [ ] **Step 4: Run to verify pass, commit**

Run: `uv run pytest tests/test_cfpb.py -v` — Expected: PASS

```bash
git add src/cix/cfpb.py tests/test_cfpb.py
git commit -m "feat(cfpb): corpus writer — units/ layout, sealed holdout_labels sidecar, S2 properties"
```

---

### Task 7: `cix cfpb-ingest` CLI + store-level withholding guard

**Files:**
- Modify: `src/cix/cli.py`
- Test: `tests/test_cfpb.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_cfpb.py
from cix.cli import main as cli_main
from cix.store import build_store

def test_cfpb_ingest_cli_end_to_end(tmp_path, capsys):
    p = tmp_path / "c.csv"
    _write_csv(p, [_row(str(i) + ".0", narrative=f"Complaint number {i} about a fee.")
                   for i in range(1, 8)])
    out = tmp_path / "corpus"
    rc = cli_main(["cfpb-ingest", str(p), "--company", "Block, Inc.",
                   "--since", "2024-01-01", "--n", "5", "--seed", "7",
                   "--out", str(out)])
    assert rc == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["written"] == 5
    assert summary["drops"] == {}                      # every fixture row is eligible
    assert len(list((out / "units").glob("*.json"))) == 5

def test_outcome_label_never_reaches_the_store(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    units = load_corpus(out / "units")
    db = tmp_path / "run.db"
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    blob = db.read_bytes()
    assert b"monetary relief" not in blob
    assert b"Closed with explanation" not in blob
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cfpb.py -v` — Expected: FAIL — cfpb-ingest is not a known subcommand

- [ ] **Step 3: Implement the subcommand in `src/cix/cli.py`**

Add the handler (near `_cmd_index`):

```python
def _cmd_cfpb_ingest(args) -> int:
    """CFPB CSV -> corpus adapter (spec 2026-08-05 §3). Writes <out>/units + sealed
    holdout_labels.json + corpus_properties.yaml. The outcome label never enters units."""
    from cix.cfpb import read_filtered, dedup_rows, sample_stratified, write_corpus
    rows, drops = read_filtered(Path(args.csv), company=args.company, since=args.since)
    rows, n_dupes = dedup_rows(rows)
    picked = sample_stratified(rows, n=args.n, seed=args.seed)
    try:
        res = write_corpus(picked, Path(args.out), company=args.company,
                           since=args.since, seed=args.seed, source_csv=str(args.csv))
    except FileExistsError:
        print(f"ingest aborted: {args.out} already contains a corpus (use a fresh --out)",
              file=sys.stderr)
        return 3
    print(json.dumps({"written": res["units"], "eligible": len(rows),
                      "duplicates_collapsed": n_dupes, "drops": drops,
                      "out": res["out"]}))
    return 0
```

Register in `main()` beside the other subparsers:

```python
    p_cfpb = sub.add_parser("cfpb-ingest",
                            help="CFPB filtered CSV -> corpus dir (units/ + sealed labels + S2 properties)")
    p_cfpb.add_argument("csv")
    p_cfpb.add_argument("--company", required=True, help='exact CSV value, e.g. "Block, Inc."')
    p_cfpb.add_argument("--since", required=True, help="YYYY-MM-DD window start")
    p_cfpb.add_argument("--n", type=int, required=True, help="sample size")
    p_cfpb.add_argument("--seed", type=int, required=True)
    p_cfpb.add_argument("--out", required=True)
    p_cfpb.set_defaults(fn=_cmd_cfpb_ingest)
```

- [ ] **Step 4: Run to verify pass; full suite; commit**

Run: `uv run pytest tests/test_cfpb.py -v` then `uv run pytest -x -q` — Expected: green

```bash
git add src/cix/cli.py tests/test_cfpb.py
git commit -m "feat(cfpb): cix cfpb-ingest CLI + store-level label-withholding guard"
```

---

### Task 8: Briefing generalization — metric loop + `rubric_file` binding

Two integrity gaps block a second presentation config: (a) `build_briefing`/renderer/CLI hardcode
`avoidable_contact_rate`; (b) `requires.rubric_version` alone cannot tell two rubrics apart when both
say `"1.0.0"`. Fix both **without changing `configs/briefing_presentation_v1.yaml` or any golden
number**.

**Files:**
- Modify: `src/cix/briefing.py`
- Modify: `src/cix/cli.py` (`_cmd_run` manifest, `_cmd_briefing` print)
- Test: `tests/test_briefing.py` (extend)

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_briefing.py
def test_build_briefing_supports_arbitrary_headline_metric_names():
    # Same fixture payload the existing build_briefing tests use, but a presentation
    # config whose metric is named unremediated_loss_rate with a custom statement.
    cfg = {
        "version": "1.0.0",
        "requires": {"rubric_version": "1.0.0"},
        "items": {"billing_defect_driver": {"business_label": "B", "gloss": "g",
                                            "polarity": "negative"}},
        "headline_metrics": {
            "unremediated_loss_rate": {
                "members": ["billing_defect_driver"],
                "statement": "complaints described losing money or access without remedy"}},
    }
    rows = [{"item_id": "billing_defect_driver", "interaction_id": "i1", "unit": "interaction"}]
    report, manifest = _minimal_report_and_manifest()   # reuse/extract the fixture builder
    b = build_briefing(report, manifest, cfg, _FakeStore(rows))
    m = b["headline"]["unremediated_loss_rate"]
    assert m["value"] == 1
    assert m["query"] == "cix query <run_dir> --metric unremediated_loss_rate"
    assert m["statement"] == "complaints described losing money or access without remedy"
    assert "automatable_opportunity" in b["headline"]

def test_briefing_html_renders_named_metric_statement():
    ...  # render_briefing_html over the briefing above; assert the statement text and
         # "1 / <eligible>" appear; assert it does NOT contain "avoidable pattern"

def test_presentation_rubric_file_binding_fails_closed():
    # cfg requires {"rubric_version": "1.0.0", "rubric_file": "complaint_rubric_v1.yaml"};
    # manifest carries rubric_version "1.0.0" and rubric_file "service_rubric_v1.yaml"
    # -> build_briefing raises ValueError mentioning rubric_file.
    ...

def test_presentation_without_rubric_file_still_loads_legacy_manifests():
    # cfg has no requires.rubric_file; manifest has no rubric_file key -> builds fine.
    ...
```

If the existing tests build report/manifest fixtures inline, extract a module-level helper
`_minimal_report_and_manifest()` so the new tests reuse it (pure refactor, keep old tests passing).
Write the two `...` tests out fully against that helper — no stubs left.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_briefing.py -v` — Expected: new tests FAIL

- [ ] **Step 3: Implement in `src/cix/briefing.py`**

In `build_briefing`, replace the version check and hardcoded metric block:

```python
    required = cfg.get("requires", {}).get("rubric_version")
    actual = manifest.get("rubric_version")
    if required != actual:
        raise ValueError(f"presentation config rubric version {required!r} != run rubric version {actual!r}")
    # Version strings alone cannot distinguish two rubrics that both say "1.0.0" — bind by
    # filename too when both sides declare it (same precedent as load_paraphrase_set).
    bound = cfg.get("requires", {}).get("rubric_file")
    run_file = manifest.get("rubric_file")
    if bound is not None and run_file is not None and bound != run_file:
        raise ValueError(f"presentation config is bound to rubric_file {bound!r} "
                         f"but the run used {run_file!r}")
```

and compute every configured metric (all are interaction-union metrics):

```python
    eligible = sections["distribution"]["eligible_interactions"]
    hits_artifact = manifest["artifacts"]["hits"]
    headline = {}
    for name, spec in cfg["headline_metrics"].items():
        members = spec["members"]
        for m in members:
            unit = dist_items.get(m, {}).get("unit")
            if unit is not None and unit != "interaction":
                raise ValueError(f"{name} member {m!r} is not interaction-unit ({unit})")
        rate = avoidable_contact_rate(store, hits_artifact, members, eligible)
        rate["query"] = f"cix query <run_dir> --metric {name}"
        rate["statement"] = spec.get("statement",
                                     "contacts matched at least one avoidable pattern")
        rate["honesty"] = manifest.get("corpus_clearance")
        headline[name] = rate
    headline["automatable_opportunity"] = automatable_opportunity(
        sections["leverage"]["grid"], sections["priced_plays"])
```

Return `"headline": headline` (drop the old two-key literal). Keep the
`avoidable_contact_rate(...)` function itself unchanged (it is the generic union computation; its
name is historical — add a comment saying so).

In `render_briefing_html`, replace the single hardcoded headline block with a loop:

```python
    opp = b["headline"].get("automatable_opportunity")
    out.append("<h2>The one thing to know</h2>")
    out.append("<div class='headline'>")
    for name, rate in b["headline"].items():
        if name == "automatable_opportunity":
            continue
        out.append(f"<div class='big'>{rate['value']} / {rate['denominator']} "
                   f"{_esc(rate['statement'])}</div>")
        out.append(f"<div class='muted'>{_esc(rate['method'])} · resolve with "
                   f"<span class='tag'>{_esc(rate['query'])}</span></div>")
    if opp:
        ...  # existing two opp lines unchanged
    out.append("</div>")
```

The v1 config carries no `statement`, so the default keeps today's exact sentence — the committed
`runs/svc-run/briefing.html` text does not change.

In `src/cix/cli.py`:
- `_cmd_run` manifest update gains: `"rubric_file": Path(args.rubric).name,`
- `_cmd_briefing` final print becomes metric-name agnostic:

```python
    metrics = {k: v["value"] for k, v in briefing["headline"].items()
               if isinstance(v, dict) and "value" in v and k != "automatable_opportunity"}
    print(json.dumps({"run": str(run), "headline": metrics, "pdf": (not args.no_pdf)}))
```

Check `tests/test_briefing.py` / `tests/test_cli.py` for assertions on the old print shape
(`avoidable_contact_rate` key) and update them to the new `headline` dict shape.

- [ ] **Step 4: Regenerate nothing — verify goldens still pass**

Run: `uv run pytest tests/test_briefing.py -v` then `uv run pytest -x -q`
Expected: all green. If a golden compares `briefing.json` byte-for-byte and now differs only by the
added `statement`/`query` fields, re-render the committed demo artifact:
`uv run cix briefing runs/svc-run --no-pdf` (model-free, deterministic), inspect the diff is only
those fields, commit it together with the code.

- [ ] **Step 5: Commit**

```bash
git add src/cix/briefing.py src/cix/cli.py tests/ runs/svc-run/
git commit -m "refactor(briefing): generic headline metrics + rubric_file binding (fail-closed across rubrics)"
```

---

### Task 9: Complaint rubric + complaint presentation config

**Files:**
- Create: `configs/complaint_rubric_v1.yaml`
- Create: `configs/briefing_presentation_complaint_v1.yaml`
- Test: `tests/test_complaint_rubric.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_complaint_rubric.py
from pathlib import Path
import yaml
from cix.rubric import load_rubric
from cix.briefing import load_presentation

RUBRIC = Path("configs/complaint_rubric_v1.yaml")
PRESENTATION = Path("configs/briefing_presentation_complaint_v1.yaml")

def test_complaint_rubric_loads_and_is_speaker_agnostic():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    assert r.version == "1.0.0"
    assert len(r.items) == 9
    assert all(i.requires_speaker is False for i in r.items)
    assert all(i.unit_of_count == "interaction" for i in r.items)
    assert len({i.id for i in r.items}) == 9

def test_complaint_rubric_polarity_split():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    positives = [i.id for i in r.items if i.polarity == "positive"]
    assert positives == ["resolution_acknowledged"]

def test_complaint_rubric_has_no_catalogue_refs_yet():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    assert all(i.swap_ref is None for i in r.items)    # honest empty plays state

def test_complaint_presentation_binds_to_complaint_rubric_file():
    cfg = load_presentation(PRESENTATION)
    assert cfg["requires"]["rubric_version"] == "1.0.0"
    assert cfg["requires"]["rubric_file"] == "complaint_rubric_v1.yaml"

def test_presentation_covers_every_rubric_item_and_metric_members_exist():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    cfg = load_presentation(PRESENTATION)
    ids = {i.id for i in r.items}
    assert set(cfg["items"]) == ids
    m = cfg["headline_metrics"]["unremediated_loss_rate"]
    assert set(m["members"]) <= ids
    assert m["statement"]
    for iid, item in cfg["items"].items():
        rub = next(i for i in r.items if i.id == iid)
        assert item["polarity"] == rub.polarity        # polarity mirrors the rubric
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_complaint_rubric.py -v` — Expected: FAIL (files missing)

- [ ] **Step 3: Write `configs/complaint_rubric_v1.yaml`**

```yaml
# Complaint rubric v1 — CFPB-class real complaint narratives (substrate S2, monologue).
# Spec: docs/superpowers/specs/2026-08-05-cfpb-comparative-briefing-design.md §4.
# BLINDNESS RULE (spec §4.1): items describe generic complaint pathology present in any
# financial-services complaint stream. Nothing here encodes or derives from the withheld
# outcome label (`Company response to consumer`); the reveal tests rates and rank order.
# All items are speaker-agnostic (monologue) and interaction-unit (one narrative = one
# interaction; occurrence counting inside a monologue would double-count rhetoric).
# swap_ref: null throughout — no complaint swap catalogue in v1 (honest empty plays).
# CALIBRATION: pending — the pilot run is the shakedown; a G3-style calibration pass is
# the prerequisite for the full-pair run, not the pilot (spec §4.3).
version: "1.0.0"
requires:
  label_schema_version: "1.0.0"
  tag_vocab_version: "1.0.0"
items:
  - id: remediation_denied
    description: "Refund, reversal, or compensation explicitly requested and refused"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative states that the complainant asked the company for a refund, reversal, or compensation for a concrete loss and the company refused, declined, or failed to provide it."
    exemplars: ["They admitted the charge was wrong but refused to give my money back."]
    swap_ref: null
  - id: funds_frozen_or_held
    description: "Money or account access frozen, held, or blocked by the provider"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative describes the provider freezing, holding, or blocking the complainant's funds or account so they could not access their own money for some period."
    exemplars: ["My account was frozen with my paycheck inside and nobody could tell me why."]
    swap_ref: null
  - id: account_lockout
    description: "Locked out of the account or service without a working recovery path"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative describes being locked out of an account or app and unable to regain access through the provider's recovery process."
    exemplars: ["The app logged me out and every identity check fails, so I simply cannot get in."]
    swap_ref: null
  - id: fraud_victim_redirected
    description: "A fraud or scam victim seeking help is turned away or redirected"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The complainant reports being a victim of fraud, a scam, or an unauthorized transaction, and the provider declined responsibility, denied the claim, or redirected them elsewhere instead of resolving it."
    exemplars: ["I reported the scam the same day and they said there was nothing they could do."]
    swap_ref: null
  - id: unresponsive_support
    description: "Support unreachable, unresponsive, or replying only with form answers"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative describes being unable to reach a human, receiving no reply, or receiving only automated or templated responses that did not address the issue."
    exemplars: ["Every email gets the same canned reply and there is no phone number that reaches a person."]
    swap_ref: null
  - id: repeat_complaint_unresolved
    description: "The complainant has raised this same issue before without resolution"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative states that this issue was already raised with the company (or a prior complaint filed) and remains unresolved — a repeat contact the first response should have prevented."
    exemplars: ["This is my third complaint about the same duplicate charge."]
    swap_ref: null
  - id: fee_dispute
    description: "A fee or charge the complainant disputes as wrongly levied"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative disputes a specific fee or charge as incorrect, undisclosed, or wrongly applied — separate from fraud by a third party."
    exemplars: ["They charged a maintenance fee on an account that was advertised as free."]
    swap_ref: null
  - id: misapplied_payment
    description: "A payment made but not credited or applied correctly"
    polarity: negative
    unit_of_count: interaction
    prefilter: null
    criterion: "The narrative describes a payment that was made but not credited, applied to the wrong account or balance, or lost in processing."
    exemplars: ["I paid the balance in full and they applied it to someone else's loan."]
    swap_ref: null
  - id: resolution_acknowledged
    description: "The narrative acknowledges the company fixed the issue"
    polarity: positive
    unit_of_count: interaction
    prefilter: null
    criterion: "The complainant acknowledges that the company ultimately corrected the problem — refunded, restored access, or fixed the error — even if they remain unhappy about the process."
    exemplars: ["They did eventually refund the charge after I complained."]
    swap_ref: null
```

- [ ] **Step 4: Write `configs/briefing_presentation_complaint_v1.yaml`**

```yaml
# Complaint-corpus presentation layer v1 — maps complaint_rubric_v1 items to business
# language. Bound to the rubric by BOTH version and filename (rubric_file) so a
# same-version service rubric can never satisfy this config (fail-closed integrity).
version: "1.0.0"
requires:
  rubric_version: "1.0.0"
  rubric_file: complaint_rubric_v1.yaml
items:
  remediation_denied:
    business_label: "Refunds refused"
    gloss: "Customers who asked for their money back for a concrete loss and did not get it."
    polarity: negative
  funds_frozen_or_held:
    business_label: "Frozen funds and blocked accounts"
    gloss: "Customers cut off from their own money by a provider-side freeze or hold."
    polarity: negative
  account_lockout:
    business_label: "Lockouts with no recovery path"
    gloss: "Customers locked out of the account and unable to get back in through the provider's own process."
    polarity: negative
  fraud_victim_redirected:
    business_label: "Fraud victims turned away"
    gloss: "Scam and fraud victims whose claims were denied or redirected instead of resolved."
    polarity: negative
  unresponsive_support:
    business_label: "Support that doesn't answer"
    gloss: "No human reachable, no reply, or only templated answers that don't address the issue."
    polarity: negative
  repeat_complaint_unresolved:
    business_label: "Repeat complaints on unresolved issues"
    gloss: "The same issue raised before and still unresolved — the first response should have prevented this contact."
    polarity: negative
  fee_dispute:
    business_label: "Disputed fees"
    gloss: "Fees or charges customers say were incorrect, undisclosed, or wrongly applied."
    polarity: negative
  misapplied_payment:
    business_label: "Payments not credited"
    gloss: "Payments made but not applied — wrong account, wrong balance, or lost in processing."
    polarity: negative
  resolution_acknowledged:
    business_label: "Issues the company did fix"
    gloss: "The healthy counter-pattern — the narrative acknowledges the problem was ultimately corrected."
    polarity: positive
headline_metrics:
  unremediated_loss_rate:
    members:
      - remediation_denied
      - funds_frozen_or_held
      - fraud_victim_redirected
      - misapplied_payment
    statement: "complaints described losing money or access without remedy"
```

- [ ] **Step 5: Run to verify pass; full suite; commit**

Run: `uv run pytest tests/test_complaint_rubric.py -v && uv run pytest -x -q` — Expected: green

```bash
git add configs/complaint_rubric_v1.yaml configs/briefing_presentation_complaint_v1.yaml tests/test_complaint_rubric.py
git commit -m "feat(complaint): complaint rubric v1 (9 items, blind to outcome label) + presentation config"
```

---

### Task 10: Compare builder (`src/cix/compare.py`)

**Files:**
- Create: `src/cix/compare.py`
- Test: `tests/test_compare.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_compare.py
import pytest
from cix.compare import build_compare, reveal_block, render_compare_html

class _FakeStore:
    def __init__(self, rows):
        self._rows = rows
    def hits_for(self, artifact_id):
        return list(self._rows)

def _cfg():
    return {"version": "1.0.0", "requires": {"rubric_version": "1.0.0"},
            "items": {"remediation_denied": {"business_label": "Refunds refused",
                                             "gloss": "g", "polarity": "negative"},
                      "fee_dispute": {"business_label": "Disputed fees",
                                      "gloss": "g", "polarity": "negative"}},
            "headline_metrics": {"unremediated_loss_rate": {
                "members": ["remediation_denied"],
                "statement": "complaints described losing money without remedy"}}}

def _report(eligible, items):
    # items: {item_id: (count, share)}
    dist = {i: {"count": c, "share": s, "unit": "interaction",
                "denominator": eligible} for i, (c, s) in items.items()}
    return {"sections": {
        "distribution": {"items": dist, "eligible_interactions": eligible,
                         "interaction_coverage": 1.0, "residual_interactions": 0},
        "leverage": {"grid": [], "shelf": [], "class_d": [], "note": ""},
        "priced_plays": {"plays": [], "note": "no catalogue"},
        "method": {"validations": [], "drop_summary": {}},
        "highlights": [], "whats_working": []}}

def _manifest(name):
    return {"rubric_version": "1.0.0", "rubric_file": "complaint_rubric_v1.yaml",
            "corpus_clearance": f"CFPB public domain — internal O2 track ({name})",
            "corpus_hash": f"hash-{name}", "catalogue_version": None,
            "substrate_class": "S2", "artifacts": {"hits": "ha"}}

def _side(name, eligible, items, hit_rows):
    return {"name": name, "report": _report(eligible, items),
            "manifest": _manifest(name), "store": _FakeStore(hit_rows)}

def _two_sides():
    a = _side("Block, Inc.", 100,
              {"remediation_denied": (40, 0.40), "fee_dispute": (10, 0.10)},
              [{"item_id": "remediation_denied", "interaction_id": f"i{k}",
                "unit": "interaction"} for k in range(40)])
    b = _side("Bank of America", 100,
              {"remediation_denied": (5, 0.05), "fee_dispute": (20, 0.20)},
              [{"item_id": "remediation_denied", "interaction_id": f"j{k}",
                "unit": "interaction"} for k in range(5)])
    return a, b

def test_build_compare_headline_and_ratio():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    m = c["headline"]["unremediated_loss_rate"]
    assert m["a"]["value"] == 40 and m["b"]["value"] == 5
    assert m["ratio"] == 8.0                      # a.share / b.share
    assert c["meta"]["a"]["name"] == "Block, Inc."
    assert c["meta"]["substrate_class"] == "S2"

def test_build_compare_rank_order_and_divergence():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    ranks_a = [r["item_id"] for r in c["rank_order"]["a"]]
    ranks_b = [r["item_id"] for r in c["rank_order"]["b"]]
    assert ranks_a == ["remediation_denied", "fee_dispute"]
    assert ranks_b == ["fee_dispute", "remediation_denied"]
    top = c["divergence"][0]
    assert top["item_id"] == "remediation_denied"
    assert top["share_a"] == 0.40 and top["share_b"] == 0.05

def test_build_compare_fails_closed_on_rubric_mismatch():
    a, b = _two_sides()
    b["manifest"]["rubric_version"] = "2.0.0"
    with pytest.raises(ValueError, match="rubric"):
        build_compare(a, b, _cfg())

def test_driver_rates_exclude_unit_mismatch_with_note():
    a, b = _two_sides()
    b["report"]["sections"]["distribution"]["items"]["fee_dispute"]["unit"] = "occurrence"
    c = build_compare(a, b, _cfg())
    ids = [r["item_id"] for r in c["driver_rates"]["rows"]]
    assert "fee_dispute" not in ids
    assert any("fee_dispute" in n for n in c["driver_rates"]["excluded"])

def test_reveal_block_computes_relief_rates_and_banner():
    labels_a = {"i1": "Closed with monetary relief", "i2": "Closed with explanation",
                "i3": "Closed with explanation", "i4": "Closed with explanation"}
    labels_b = {"j1": "Closed with monetary relief", "j2": "Closed with monetary relief"}
    r = reveal_block(labels_a, labels_b)
    assert r["a"]["monetary_relief_rate"] == 0.25
    assert r["b"]["monetary_relief_rate"] == 1.0
    assert "never seen by the model" in r["banner"]
    assert r["a"]["n"] == 4 and r["a"]["responses"]["Closed with explanation"] == 3

def test_render_compare_html_contains_banner_names_and_reveal():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    c["reveal"] = reveal_block({"i1": "Closed with monetary relief"},
                               {"j1": "Closed with explanation"})
    html = render_compare_html(c)
    assert "Block, Inc." in html and "Bank of America" in html
    assert "never seen by the model" in html
    assert "S2" in html                            # substrate banner

def test_render_compare_html_without_reveal_states_absence():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())                # no reveal key set
    html = render_compare_html(c)
    assert "reveal not run" in html.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_compare.py -v` — Expected: FAIL — no `cix.compare`

- [ ] **Step 3: Implement `src/cix/compare.py`**

```python
"""Comparative briefing (model-free): side-by-side rendering of two persisted runs of
the SAME rubric over two operations, with an optional withheld-ground-truth reveal.

Same contract as briefing.py: reads persisted artifacts + read-only stores, never calls
a model, never mutates anything, fails closed. Spec 2026-08-05 §6.
"""
from cix.briefing import build_briefing, _esc

RELIEF = "Closed with monetary relief"

def _check_comparable(ma: dict, mb: dict) -> None:
    for key in ("rubric_version", "rubric_file", "substrate_class"):
        if ma.get(key) != mb.get(key):
            raise ValueError(f"runs are not comparable: {key} differs "
                             f"({ma.get(key)!r} vs {mb.get(key)!r})")

def _neg_rank(report: dict, cfg: dict) -> list[dict]:
    dist = report["sections"]["distribution"]["items"]
    rows = [{"item_id": i, "share": d.get("share"), "count": d.get("count"),
             "unit": d.get("unit")}
            for i, d in dist.items()
            if cfg["items"].get(i, {}).get("polarity") == "negative"]
    rows.sort(key=lambda r: (-(r["share"] or 0), r["item_id"]))
    for rank, r in enumerate(rows, start=1):
        r["rank"] = rank
    return rows

def build_compare(side_a: dict, side_b: dict, cfg: dict) -> dict:
    """side = {name, report, manifest, store}. Builds each side's briefing via the same
    builder the single-run artifact uses (consistency by construction), then compares."""
    ma, mb = side_a["manifest"], side_b["manifest"]
    _check_comparable(ma, mb)
    brief_a = build_briefing(side_a["report"], ma, cfg, side_a["store"])
    brief_b = build_briefing(side_b["report"], mb, cfg, side_b["store"])
    headline = {}
    for name in cfg["headline_metrics"]:
        a, b = brief_a["headline"][name], brief_b["headline"][name]
        ratio = (round(a["share"] / b["share"], 2)
                 if a.get("share") and b.get("share") else None)
        headline[name] = {"a": a, "b": b, "ratio": ratio,
                          "statement": a.get("statement")}
    rank_a, rank_b = _neg_rank(side_a["report"], cfg), _neg_rank(side_b["report"], cfg)
    pos_b = {r["item_id"]: r for r in rank_b}
    rows, excluded, divergence = [], [], []
    for r in rank_a:
        o = pos_b.get(r["item_id"])
        if o is None:
            excluded.append(f"{r['item_id']}: absent from run B distribution")
            continue
        if r["unit"] != o["unit"]:
            excluded.append(f"{r['item_id']}: unit mismatch ({r['unit']} vs {o['unit']})")
            continue
        sa, sb = r["share"] or 0.0, o["share"] or 0.0
        rows.append({"item_id": r["item_id"],
                     "label": cfg["items"].get(r["item_id"], {}).get("business_label",
                                                                     r["item_id"]),
                     "share_a": sa, "share_b": sb, "count_a": r["count"],
                     "count_b": o["count"], "unit": r["unit"],
                     "ratio": round(sa / sb, 2) if sb else None,
                     "rank_a": r["rank"], "rank_b": o["rank"]})
        divergence.append({"item_id": r["item_id"], "share_a": sa, "share_b": sb,
                           "abs_gap": round(abs(sa - sb), 4)})
    divergence.sort(key=lambda d: (-d["abs_gap"], d["item_id"]))
    return {
        "meta": {"a": {"name": side_a["name"], "corpus_hash": ma.get("corpus_hash"),
                       "clearance": ma.get("corpus_clearance"),
                       "eligible": side_a["report"]["sections"]["distribution"]["eligible_interactions"]},
                 "b": {"name": side_b["name"], "corpus_hash": mb.get("corpus_hash"),
                       "clearance": mb.get("corpus_clearance"),
                       "eligible": side_b["report"]["sections"]["distribution"]["eligible_interactions"]},
                 "rubric_version": ma.get("rubric_version"),
                 "rubric_file": ma.get("rubric_file"),
                 "substrate_class": ma.get("substrate_class")},
        "headline": headline,
        "rank_order": {"a": rank_a, "b": rank_b},
        "driver_rates": {"rows": rows, "excluded": excluded},
        "divergence": divergence[:5],
        "trust": {"a": brief_a["trust"], "b": brief_b["trust"]},
    }

def reveal_block(labels_a: dict, labels_b: dict) -> dict:
    """Unseal the withheld outcome label. Facts only — rates and response distributions;
    interpretation stays human (spec §6)."""
    def side(labels: dict) -> dict:
        n = len(labels)
        responses: dict[str, int] = {}
        for v in labels.values():
            responses[v] = responses.get(v, 0) + 1
        relief = responses.get(RELIEF, 0)
        return {"n": n, "responses": dict(sorted(responses.items())),
                "monetary_relief_rate": round(relief / n, 4) if n else None}
    return {"banner": ("WITHHELD GROUND TRUTH — never seen by the model. "
                       "`Company response to consumer` was diverted to a sealed sidecar "
                       "at ingest and is unsealed here, post-run, for validation only."),
            "a": side(labels_a), "b": side(labels_b)}

_CSS = """
body{font-family:Helvetica,Arial,sans-serif;color:#1a1a1a;max-width:960px;margin:2rem auto;line-height:1.5}
h1{font-size:1.6rem;margin-bottom:.2rem}
.banner{background:#fef3c7;border:1px solid #f59e0b;padding:.5rem .8rem;border-radius:6px;font-size:.85rem;margin:.6rem 0}
.reveal{background:#fee2e2;border:1px solid #ef4444;padding:.6rem .9rem;border-radius:6px;margin:.8rem 0}
h2{font-size:1.15rem;border-bottom:2px solid #e5e7eb;padding-bottom:.2rem;margin-top:1.6rem}
.headline{background:#f0f9ff;border:1px solid #bae6fd;padding:.8rem 1rem;border-radius:8px;margin:.8rem 0}
.big{font-size:1.3rem;font-weight:700}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid #e5e7eb;vertical-align:top}
.muted{color:#6b7280;font-size:.85rem}
"""

def _pct(x) -> str:
    return "—" if x is None else f"{round(x * 100, 1)}%"

def render_compare_html(c: dict) -> str:
    a, b = c["meta"]["a"], c["meta"]["b"]
    out = ["<!DOCTYPE html>", "<html><head><meta charset='utf-8'>",
           f"<style>{_CSS}</style></head><body>"]
    out.append(f"<h1>Comparative Review — {_esc(a['name'])} vs {_esc(b['name'])}</h1>")
    out.append(f"<div class='banner'>Substrate class {_esc(c['meta']['substrate_class'])} · "
               f"rubric {_esc(c['meta']['rubric_file'])} v{_esc(c['meta']['rubric_version'])} · "
               f"A: {_esc(a['clearance'])} · B: {_esc(b['clearance'])}</div>")
    out.append("<h2>Headline</h2><div class='headline'>")
    for name, m in c["headline"].items():
        ra, rb = m["a"], m["b"]
        ratio = f" — {m['ratio']}× apart" if m.get("ratio") else ""
        out.append(f"<div class='big'>{_esc(a['name'])}: {ra['value']}/{ra['denominator']} · "
                   f"{_esc(b['name'])}: {rb['value']}/{rb['denominator']}{ratio}</div>")
        out.append(f"<div class='muted'>{_esc(m.get('statement'))} · {_esc(ra['method'])} · "
                   f"resolve per run with {_esc(ra['query'])}</div>")
    out.append("</div>")
    out.append("<h2>Pattern rank order</h2><table>")
    out.append(f"<tr><th>Pattern</th><th>{_esc(a['name'])} rank · share</th>"
               f"<th>{_esc(b['name'])} rank · share</th><th>Ratio</th></tr>")
    for r in c["driver_rates"]["rows"]:
        ratio = f"{r['ratio']}×" if r["ratio"] is not None else "—"
        out.append(f"<tr><td><b>{_esc(r['label'])}</b></td>"
                   f"<td>#{r['rank_a']} · {_pct(r['share_a'])} ({r['count_a']})</td>"
                   f"<td>#{r['rank_b']} · {_pct(r['share_b'])} ({r['count_b']})</td>"
                   f"<td>{ratio}</td></tr>")
    out.append("</table>")
    for note in c["driver_rates"]["excluded"]:
        out.append(f"<p class='muted'>excluded from comparison — {_esc(note)}</p>")
    out.append("<h2>Where the operations diverge most</h2><ul>")
    for d in c["divergence"]:
        out.append(f"<li><b>{_esc(d['item_id'])}</b> — {_pct(d['share_a'])} vs "
                   f"{_pct(d['share_b'])} (gap {_pct(d['abs_gap'])})</li>")
    out.append("</ul>")
    out.append("<h2>The reveal</h2>")
    rev = c.get("reveal")
    if rev:
        out.append(f"<div class='reveal'><b>{_esc(rev['banner'])}</b>")
        for key, side_meta in (("a", a), ("b", b)):
            s = rev[key]
            out.append(f"<p><b>{_esc(side_meta['name'])}</b>: monetary-relief rate "
                       f"{_pct(s['monetary_relief_rate'])} over n={s['n']} withheld labels.</p>")
        out.append("</div>")
    else:
        out.append("<p class='muted'>Reveal not run — no sealed sidecar was supplied "
                   "(--no-reveal or labels absent).</p>")
    out.append("<h2>Trust</h2>")
    for key, side_meta in (("a", a), ("b", b)):
        t = c["trust"][key]
        cov = t["coverage"]
        out.append(f"<p class='muted'><b>{_esc(side_meta['name'])}</b>: "
                   f"{round((cov['interaction_coverage'] or 0) * 100)}% of "
                   f"{cov['eligible_interactions']} eligible interactions read; "
                   f"honesty: {_esc(t['honesty_ladder'])}</p>")
        if t.get("evidence_note"):
            out.append(f"<p class='muted'>{_esc(t['evidence_note'])}</p>")
    out.append("</body></html>")
    return "\n".join(out)
```

- [ ] **Step 4: Run to verify pass, commit**

Run: `uv run pytest tests/test_compare.py -v` — Expected: PASS

```bash
git add src/cix/compare.py tests/test_compare.py
git commit -m "feat(compare): model-free comparative briefing builder + HTML renderer with reveal block"
```

---

### Task 11: `cix compare` CLI

**Files:**
- Modify: `src/cix/cli.py`
- Test: `tests/test_compare.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_compare.py
import json as _json
import sqlite3
from pathlib import Path
from cix.cli import main as cli_main

def test_compare_cli_on_committed_run_no_reveal(tmp_path, capsys):
    # runs/svc-run compared with itself: versions trivially match; --no-reveal because
    # no sidecar exists; --no-pdf keeps it WeasyPrint-free. Read-only guarantee checked
    # via the drop_log row count.
    db = Path("runs/svc-run/run.db")
    before = sqlite3.connect(db).execute("select count(*) from drop_log").fetchone()[0]
    out = tmp_path / "cmp"
    rc = cli_main(["compare", "runs/svc-run", "runs/svc-run",
                   "--presentation", "configs/briefing_presentation_v1.yaml",
                   "--name-a", "Op A", "--name-b", "Op B",
                   "--out", str(out), "--no-reveal", "--no-pdf"])
    assert rc == 0
    after = sqlite3.connect(db).execute("select count(*) from drop_log").fetchone()[0]
    assert before == after
    c = _json.loads((out / "compare.json").read_text(encoding="utf-8"))
    assert c["meta"]["a"]["name"] == "Op A"
    html = (out / "compare.html").read_text(encoding="utf-8")
    assert "Op A" in html and "reveal not run" in html.lower()

def test_compare_cli_fails_closed_without_sidecar_when_reveal_expected(tmp_path, capsys):
    rc = cli_main(["compare", "runs/svc-run", "runs/svc-run",
                   "--presentation", "configs/briefing_presentation_v1.yaml",
                   "--name-a", "A", "--name-b", "B",
                   "--out", str(tmp_path / "cmp2"), "--no-pdf"])
    assert rc == 1
    assert "holdout_labels.json" in capsys.readouterr().out
```

Check the actual drop-log table name first (`sqlite3 runs/svc-run/run.db ".tables"`) and use the
real name in the test — `tests/test_briefing.py` already asserts the same read-only guarantee;
copy its exact mechanism.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_compare.py -v` — Expected: new tests FAIL (no subcommand)

- [ ] **Step 3: Implement `_cmd_compare` in `src/cix/cli.py`**

```python
def _cmd_compare(args) -> int:
    """Comparative briefing over two persisted runs (model-free, read-only). Emits
    compare.json + compare.html (+ compare.pdf unless --no-pdf) into --out."""
    from cix.compare import build_compare, reveal_block, render_compare_html
    from cix.briefing import render_briefing_pdf
    sides = []
    for run_arg, name in ((args.run_a, args.name_a), (args.run_b, args.name_b)):
        run = Path(run_arg)
        for req in ("run.db", "report.json", "manifest.json"):
            if not (run / req).exists():
                print(f"compare failed closed: missing persisted artifact {run / req}")
                return 1
        sides.append({"name": name, "run": run,
                      "store": open_store(run / "run.db", read_only=True)})
    cfg = load_presentation(Path(args.presentation))
    labels = []
    if not args.no_reveal:
        for s in sides:
            lp = s["run"] / "holdout_labels.json"
            if not lp.exists():
                print(f"compare failed closed: reveal expected but {lp} is absent — "
                      "copy the corpus sidecar into the run dir, or pass --no-reveal")
                return 1
            labels.append(json.loads(lp.read_text(encoding="utf-8")))
    try:
        for s in sides:
            s["report"] = json.loads((s["run"] / "report.json").read_text(encoding="utf-8"))
            s["manifest"] = json.loads((s["run"] / "manifest.json").read_text(encoding="utf-8"))
        comparison = build_compare(sides[0], sides[1], cfg)
        if labels:
            comparison["reveal"] = reveal_block(labels[0], labels[1])
    except (ValueError, KeyError) as e:
        print(f"compare failed closed: {e}")
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "compare.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    html = render_compare_html(comparison)
    (out / "compare.html").write_text(html, encoding="utf-8")
    if not args.no_pdf:
        try:
            render_briefing_pdf(html, out / "compare.pdf")
        except (OSError, ImportError) as e:
            print(f"compare failed closed: PDF render unavailable ({e}); "
                  "compare.json + compare.html written — re-run with --no-pdf")
            return 1
    print(json.dumps({"out": str(out),
                      "reveal": bool(labels),
                      "headline": {k: {"a": v["a"]["value"], "b": v["b"]["value"],
                                       "ratio": v["ratio"]}
                                   for k, v in comparison["headline"].items()}}))
    return 0
```

Register in `main()`:

```python
    p_cmp = sub.add_parser("compare",
                           help="comparative briefing over two persisted runs (read-only)")
    p_cmp.add_argument("run_a")
    p_cmp.add_argument("run_b")
    p_cmp.add_argument("--presentation", required=True)
    p_cmp.add_argument("--name-a", required=True, help="display name for run A's operation")
    p_cmp.add_argument("--name-b", required=True, help="display name for run B's operation")
    p_cmp.add_argument("--out", required=True)
    p_cmp.add_argument("--no-reveal", action="store_true",
                       help="skip the withheld-label reveal (no sidecar needed)")
    p_cmp.add_argument("--no-pdf", action="store_true")
    p_cmp.set_defaults(fn=_cmd_compare)
```

- [ ] **Step 4: Run to verify pass; full suite; commit**

Run: `uv run pytest tests/test_compare.py -v && uv run pytest -x -q` — Expected: green

```bash
git add src/cix/cli.py tests/test_compare.py
git commit -m "feat(compare): cix compare CLI — fail-closed reveal, read-only, PDF via shared renderer"
```

---

### Task 12: Pilot runbook + README

**Files:**
- Create: `docs/cfpb_pilot_runbook.md`
- Modify: `README.md` (documents table + status)

- [ ] **Step 1: Write `docs/cfpb_pilot_runbook.md`**

```markdown
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
```

- [ ] **Step 2: Add to README documents table**

Row: `| docs/cfpb_pilot_runbook.md | CFPB pilot runbook — first real-data run (Block vs BofA), ingest → runs → comparative briefing with the withheld-label reveal |`

- [ ] **Step 3: Commit**

```bash
git add docs/cfpb_pilot_runbook.md README.md
git commit -m "docs(cfpb): pilot runbook — ingest, runs, comparative briefing, reveal protocol"
```

---

### Task 13: Execute the pilot (OPERATOR GATE — live spend)

**Not autonomous.** Requires KP's explicit go-ahead on spend (spec §5, D-11). When given:

- [ ] **Step 1:** Run runbook §1–§2 (offline ingest + suite). Verify both corpora: 2,500 units each,
  `corpus_properties.yaml` says S2, `holdout_labels.json` present at corpus level.
- [ ] **Step 2:** Run runbook §3 (two live runs). On any failure, stop and diagnose — do not re-run
  blindly (each attempt is spend).
- [ ] **Step 3:** Run runbook §4–§5. Confirm: briefings render with the complaint labels; self-test
  says `O3-corpus-level-items-only`; `compare.json/html/pdf` produced; reveal block present with both
  rates and the withheld-ground-truth banner.
- [ ] **Step 4:** Record actual spend in the runbook §5 blank and in a manifest note; commit the run
  artifacts that belong in the repo (follow the `runs/svc-run` precedent for what gets committed).
- [ ] **Step 5:** Update README status: G5 first real run executed as CFPB pilot; comparative
  briefing is the demo deliverable; full-pair run gated on complaint-rubric calibration.

```bash
git add runs/ docs/cfpb_pilot_runbook.md README.md
git commit -m "feat(g5): CFPB pilot executed — Block vs BofA comparative briefing with reveal"
```

---

## Self-review (done at plan time)

- **Spec coverage:** §0 decision record → Task 1 (ratification applied); §3 adapter (filter, sampler,
  withholding, properties, hardening) → Tasks 5–7; §4 rubric + presentation + calibration honesty →
  Task 9 (+ pending-note in runbook + clearance string); §5 pilot runs + spend → Tasks 12–13; §6
  compare blocks + honesty rules → Tasks 10–11; §7 testing matrix → distributed per task (dates 5,
  sampler 5, withholding 6/7, substrate 2–4, compare 10–11, read-only 11, reveal 10/11); §8
  sequencing → task order; §9 acceptance → Tasks 11–13.
- **Known deviation from spec:** spec §7.6 named a "golden render" over committed fixture runs;
  covered instead by deterministic builder/renderer assertions (Task 10) plus the self-compare CLI
  test (Task 11) — a committed golden of a synthetic compare would freeze presentation text during
  a phase where it will iterate. Revisit after the pilot artifact exists.
- **Type consistency:** `side` dicts (`name/report/manifest/store`) consistent across Tasks 10–11;
  `read_filtered → dedup_rows → sample_stratified → write_corpus` row shape
  (`complaint_id/date/narrative/product/issue/outcome`) consistent across Tasks 5–7;
  `load_corpus_properties` parent-lookup contract (Task 2) matches the `<out>/units` layout (Task 6);
  `requires_speaker` default False (Task 3) keeps existing rubrics loading unchanged.
- **Placeholders:** Tasks 2/4/8 direct the engineer to write named tests against existing fixtures
  they must locate in the named test files — each states the exact assertion; no TBDs remain.
