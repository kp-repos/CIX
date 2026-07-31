# G1 Deterministic Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build CIX's deterministic spine — ingest → normalize → index (snippets + tags) → SQLite store → canonical hash → evidence-gate mechanics → drop log → manifest — on synthetic transcripts, with zero model calls, passing the G1 exit criteria (PRD §5): logical-content equality property test and evidence-gate component tests (AC-1, AC-3a, AC-4a).

**Architecture:** A `cix` Python package. Every stage is a pure function over explicit data; the only state is one SQLite file per run. Determinism rules: inputs sorted before processing, inserts in sorted order, the canonical hash covers logical content only (never timestamps or file paths). Configs (tag vocabulary, label schema) are versioned YAML — plain-language artifacts per the design record. No LLM anywhere in this plan.

**Tech Stack:** Python 3.12 · uv · pytest · pydantic v2 · PyYAML · stdlib `sqlite3`, `hashlib`, `argparse`, `json`, `re`.

**Spec:** `docs/CIX_PRD_v1_2026-07-31.md` (RATIFIED v1.2) — requirements R-IDX-1…7, R-EVD-1…3 (component level), R-RUN-1 (config validation), R-ARCH-3 (configs as versioned YAML). Gate: G1.

**Not in this plan (later gates):** model calls, label/rubric passes, scrub pipeline (fixtures are synthetic — the privacy gate records `synthetic-fixture`), aggregation/synthesis/report, thresholds.

---

## G0 checklist (human, not code — KP; may run in parallel with any task)

- [ ] OD-1: FS corpus phone call — volume, format, date range; fit/no-fit call; fallback path chosen
- [ ] Second-lab provider account + billing stood up
- [ ] Cost envelope (PRD §9) accepted; Sunsama tracking started
- [ ] PRD ratified — **done 2026-07-31**

## File structure

```
CIX/
├── pyproject.toml                  # uv project; pytest config
├── README.md                       # (exists)
├── configs/
│   ├── tag_vocabulary_v1.yaml      # A1 — published tag vocabulary (versioned)
│   └── label_schema_v1.yaml        # A2 — core label schema (authored here; consumed at G2)
├── docs/
│   ├── A3_run_manifest_schema.md   # manifest field definitions
│   └── A12_input_data_contract.md  # accepted corpus format
├── src/cix/
│   ├── __init__.py                 # version
│   ├── contracts.py                # pydantic: Segment, InteractionUnit
│   ├── normalize.py                # corpus dir → sorted, validated InteractionUnits
│   ├── chunker.py                  # unit → snippets (speaker-turn rule, positional IDs, content hashes)
│   ├── tags.py                     # vocabulary loader + deterministic taggers (4 families)
│   ├── store.py                    # SQLite schema, sorted writes, bidirectional queries, drop log
│   ├── canonical.py                # logical-content canonical hash
│   ├── evidence.py                 # quote gate + stat recompute harness → drop log
│   ├── manifest.py                 # run manifest build/write
│   └── cli.py                      # cix index | hash | verify
└── tests/
    ├── fixtures/
    │   ├── corpus/                 # 3 synthetic transcript JSONs
    │   └── claims.json             # good+bad quote, good+bad stat
    ├── test_contracts.py
    ├── test_normalize.py
    ├── test_chunker.py
    ├── test_tags.py
    ├── test_store.py
    ├── test_canonical.py
    ├── test_evidence.py
    ├── test_manifest.py
    └── test_cli.py
```

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`, `src/cix/__init__.py`, `tests/test_scaffold.py`

- [ ] **Step 1: Initialize the uv project**

```bash
cd /Users/vajrapani/Projects_gh/CIX
uv init --name cix --package --python 3.12
uv add pydantic pyyaml
uv add --dev pytest
```

- [ ] **Step 2: Set pyproject contents**

Replace generated `pyproject.toml` with:

```toml
[project]
name = "cix"
version = "0.1.0"
description = "CIX customer intelligence module — deterministic spine"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.7", "pyyaml>=6.0"]

[dependency-groups]
dev = ["pytest>=8.0"]

[project.scripts]
cix = "cix.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Set `src/cix/__init__.py`:

```python
__version__ = "0.1.0"
INDEX_VERSION = "1.0.0"
```

- [ ] **Step 3: Write smoke test**

`tests/test_scaffold.py`:

```python
import cix

def test_package_imports():
    assert cix.__version__ == "0.1.0"
    assert cix.INDEX_VERSION == "1.0.0"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest -q`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/ tests/ .python-version .gitignore
git commit -m "feat: scaffold cix package (uv, pytest, pydantic)"
```

---

### Task 2: Contracts — Segment and InteractionUnit

**Files:**
- Create: `src/cix/contracts.py`, `tests/test_contracts.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_contracts.py`:

```python
import pytest
from pydantic import ValidationError
from cix.contracts import InteractionUnit, Segment

def test_valid_unit_parses():
    u = InteractionUnit(
        id="int-001", source_type="transcript",
        participants=["agent", "customer"], date="2026-05-01",
        account_id="acct-9", thread_id=None,
        segments=[{"speaker": "customer", "text": "My card was charged twice."}],
    )
    assert u.segments[0].speaker == "customer"
    assert u.thread_id is None

def test_source_type_restricted():
    with pytest.raises(ValidationError):
        InteractionUnit(id="x", source_type="carrier-pigeon", segments=[{"text": "hi"}])

def test_empty_segments_rejected():
    with pytest.raises(ValidationError):
        InteractionUnit(id="x", source_type="transcript", segments=[])

def test_segment_requires_text():
    with pytest.raises(ValidationError):
        Segment(speaker="agent")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_contracts.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.contracts'`

- [ ] **Step 3: Implement**

`src/cix/contracts.py`:

```python
from typing import Literal
from pydantic import BaseModel, Field

class Segment(BaseModel):
    speaker: str | None = None
    ts: str | None = None
    text: str

class InteractionUnit(BaseModel):
    id: str
    source_type: Literal["transcript", "email", "note"]
    participants: list[str] = Field(default_factory=list)
    date: str | None = None
    account_id: str | None = None
    thread_id: str | None = None
    segments: list[Segment] = Field(min_length=1)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_contracts.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/cix/contracts.py tests/test_contracts.py
git commit -m "feat: interaction contracts (Segment, InteractionUnit)"
```

---

### Task 3: Input contract doc + synthetic fixtures + normalize

**Files:**
- Create: `docs/A12_input_data_contract.md`, `tests/fixtures/corpus/int-001.json`, `int-002.json`, `int-003.json`, `src/cix/normalize.py`, `tests/test_normalize.py`

- [ ] **Step 1: Write A12 input contract**

`docs/A12_input_data_contract.md`:

```markdown
# A12 — Input Data Contract · v1

A corpus is a directory of `*.json` files, one interaction per file, each matching
the `InteractionUnit` contract (`src/cix/contracts.py`):

| Field | Req | Notes |
|---|---|---|
| `id` | yes | unique across the corpus; stable |
| `source_type` | yes | `transcript` \| `email` \| `note` |
| `participants` | no | display roles, e.g. `["agent","customer"]` |
| `date` | no | ISO `YYYY-MM-DD` |
| `account_id` | no | pseudonymized upstream for real data (R-PII-2); only legal basis for account/chain tags |
| `thread_id` | no | same |
| `segments[]` | yes, ≥1 | `{speaker?, ts?, text}` — one segment per speaker turn |

Eligibility: files failing validation abort the run before any processing
(R-RUN-1: deterministic config validation before any paid call — at G1, before any indexing).
Real corpora additionally pass the scrub stage before this contract applies (G4+;
fixtures here are synthetic, privacy gate records `synthetic-fixture`).
Filenames are arbitrary; ordering never matters (determinism is by sorted `id`).
```

- [ ] **Step 2: Write three synthetic fixtures**

`tests/fixtures/corpus/int-001.json`:

```json
{
  "id": "int-001",
  "source_type": "transcript",
  "participants": ["agent", "customer"],
  "date": "2026-05-01",
  "account_id": "acct-9",
  "segments": [
    {"speaker": "customer", "text": "My card was charged twice for the same order."},
    {"speaker": "agent", "text": "I can help with that. Let me check the billing record."},
    {"speaker": "customer", "text": "I already called about this last time and it is still not fixed."},
    {"speaker": "agent", "text": "I will escalate this to the billing team today."}
  ]
}
```

`tests/fixtures/corpus/int-002.json`:

```json
{
  "id": "int-002",
  "source_type": "transcript",
  "participants": ["agent", "customer"],
  "date": "2026-05-03",
  "account_id": "acct-4",
  "segments": [
    {"speaker": "customer", "text": "How do I reset my password?"},
    {"speaker": "agent", "text": "I can send you a reset link right now."},
    {"speaker": "customer", "text": "That worked, thanks."}
  ]
}
```

`tests/fixtures/corpus/int-003.json`:

```json
{
  "id": "int-003",
  "source_type": "transcript",
  "participants": ["agent", "customer"],
  "date": "2026-05-04",
  "account_id": "acct-9",
  "segments": [
    {"speaker": "customer", "text": "I was told the fee would be waived but I see a $25 charge."},
    {"speaker": "agent", "text": "Please hold on while I transfer you to the fees desk."}
  ]
}
```

- [ ] **Step 3: Write the failing tests**

`tests/test_normalize.py`:

```python
from pathlib import Path
import json
import pytest
from cix.normalize import CorpusValidationError, load_corpus

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def test_loads_all_units_sorted_by_id():
    units = load_corpus(FIXTURES)
    assert [u.id for u in units] == ["int-001", "int-002", "int-003"]

def test_invalid_file_aborts_with_filename(tmp_path):
    (tmp_path / "bad.json").write_text(json.dumps({"id": "x", "source_type": "transcript", "segments": []}))
    with pytest.raises(CorpusValidationError, match="bad.json"):
        load_corpus(tmp_path)

def test_duplicate_ids_rejected(tmp_path):
    doc = {"id": "dup", "source_type": "note", "segments": [{"text": "a"}]}
    (tmp_path / "a.json").write_text(json.dumps(doc))
    (tmp_path / "b.json").write_text(json.dumps(doc))
    with pytest.raises(CorpusValidationError, match="duplicate"):
        load_corpus(tmp_path)
```

- [ ] **Step 4: Run to verify failure**

Run: `uv run pytest tests/test_normalize.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.normalize'`

- [ ] **Step 5: Implement**

`src/cix/normalize.py`:

```python
import json
from pathlib import Path
from pydantic import ValidationError
from cix.contracts import InteractionUnit

class CorpusValidationError(Exception):
    pass

def load_corpus(corpus_dir: Path) -> list[InteractionUnit]:
    units: list[InteractionUnit] = []
    for path in sorted(Path(corpus_dir).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            units.append(InteractionUnit.model_validate(data))
        except (json.JSONDecodeError, ValidationError) as e:
            raise CorpusValidationError(f"{path.name}: {e}") from e
    seen: set[str] = set()
    for u in units:
        if u.id in seen:
            raise CorpusValidationError(f"duplicate interaction id: {u.id}")
        seen.add(u.id)
    units.sort(key=lambda u: u.id)
    return units
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_normalize.py -q`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add docs/A12_input_data_contract.md tests/fixtures/corpus/ src/cix/normalize.py tests/test_normalize.py
git commit -m "feat: A12 input contract, synthetic fixtures, corpus loader"
```

---

### Task 4: Chunker — snippets with stable IDs and content hashes

**Files:**
- Create: `src/cix/chunker.py`, `tests/test_chunker.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_chunker.py`:

```python
import hashlib
from cix.contracts import InteractionUnit
from cix.chunker import chunk

UNIT = InteractionUnit(
    id="int-001", source_type="transcript",
    segments=[{"speaker": "customer", "text": "Hello."}, {"speaker": "agent", "text": "Hi there."}],
)

def test_ids_are_positional_and_stable():
    snippets = chunk(UNIT)
    assert [s["id"] for s in snippets] == ["int-001:0000", "int-001:0001"]
    assert [s["seq"] for s in snippets] == [0, 1]

def test_content_hash_is_sha256_of_text():
    s = chunk(UNIT)[0]
    assert s["content_hash"] == hashlib.sha256("Hello.".encode()).hexdigest()

def test_speaker_carried():
    assert chunk(UNIT)[1]["speaker"] == "agent"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_chunker.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.chunker'`

- [ ] **Step 3: Implement**

`src/cix/chunker.py`:

```python
import hashlib
from cix.contracts import InteractionUnit

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def chunk(unit: InteractionUnit) -> list[dict]:
    """Snippet = one speaker turn (R-IDX-1). IDs are positional and content-stable."""
    return [
        {
            "id": f"{unit.id}:{seq:04d}",
            "interaction_id": unit.id,
            "seq": seq,
            "speaker": seg.speaker,
            "text": seg.text,
            "content_hash": _hash(seg.text),
        }
        for seq, seg in enumerate(unit.segments)
    ]
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_chunker.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/cix/chunker.py tests/test_chunker.py
git commit -m "feat: speaker-turn chunker with stable IDs and content hashes"
```

---

### Task 5: Tag vocabulary (A1) + deterministic taggers

**Files:**
- Create: `configs/tag_vocabulary_v1.yaml`, `src/cix/tags.py`, `tests/test_tags.py`

- [ ] **Step 1: Write the vocabulary config**

`configs/tag_vocabulary_v1.yaml`:

```yaml
# A1 — CIX published tag vocabulary. The index↔rubric contract (R-IDX-2).
# Bright line: nothing here requires judgment. Lexical patterns are versioned config.
version: "1.0.0"
structural: [source_type, speaker_role, position, turn_length]
metadata: [account_id, thread_id, date]
computed: [interaction_len_segments, speaker_balance]
lexical:
  - name: repeat_marker
    pattern: '\b(again|last time|still not|already (called|told))\b'
  - name: transfer_hold
    pattern: '\b(hold on|transfer|escalat\w*)\b'
  - name: negation
    pattern: '\b(no|not|never|cannot|can''t)\b'
  - name: question_mark
    pattern: '\?'
  - name: currency_amount
    pattern: '\$\d+'
```

- [ ] **Step 2: Write the failing tests**

`tests/test_tags.py`:

```python
from pathlib import Path
from cix.contracts import InteractionUnit
from cix.chunker import chunk
from cix.tags import load_vocabulary, tag_interaction, tag_snippets

VOCAB = load_vocabulary(Path("configs/tag_vocabulary_v1.yaml"))

UNIT = InteractionUnit(
    id="int-001", source_type="transcript", account_id="acct-9", date="2026-05-01",
    segments=[
        {"speaker": "customer", "text": "I already called about this last time, still not fixed. Why?"},
        {"speaker": "agent", "text": "Please hold on while I transfer you."},
        {"speaker": "customer", "text": "There is a $25 charge."},
    ],
)
SNIPPETS = chunk(UNIT)

def test_vocabulary_version():
    assert VOCAB["version"] == "1.0.0"

def test_lexical_hits():
    rows = tag_snippets(SNIPPETS, VOCAB)
    tags_by_snippet = {}
    for sid, tag, _ in rows:
        tags_by_snippet.setdefault(sid, set()).add(tag)
    assert "repeat_marker" in tags_by_snippet["int-001:0000"]
    assert "question_mark" in tags_by_snippet["int-001:0000"]
    assert "transfer_hold" in tags_by_snippet["int-001:0001"]
    assert "currency_amount" in tags_by_snippet["int-001:0002"]

def test_structural_tags():
    rows = tag_snippets(SNIPPETS, VOCAB)
    d = {(sid, tag): val for sid, tag, val in rows}
    assert d[("int-001:0000", "position")] == "opening"
    assert d[("int-001:0002", "position")] == "closing"
    assert d[("int-001:0001", "speaker_role")] == "agent"
    assert d[("int-001:0000", "turn_length")] == str(len(SNIPPETS[0]["text"]))

def test_interaction_tags():
    rows = tag_interaction(UNIT, SNIPPETS)
    d = {tag: val for _, tag, val in rows}
    assert d["interaction_len_segments"] == "3"
    assert d["account_id"] == "acct-9"
    assert d["date"] == "2026-05-01"
    assert d["source_type"] == "transcript"
    assert 0.0 < float(d["speaker_balance"]) < 1.0

def test_deterministic_output_order():
    assert tag_snippets(SNIPPETS, VOCAB) == tag_snippets(SNIPPETS, VOCAB)
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_tags.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.tags'`

- [ ] **Step 4: Implement**

`src/cix/tags.py`:

```python
import re
from pathlib import Path
import yaml
from cix.contracts import InteractionUnit

def load_vocabulary(path: Path) -> dict:
    vocab = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for fam in vocab["lexical"]:
        fam["_rx"] = re.compile(fam["pattern"], re.IGNORECASE)
    return vocab

def _position(seq: int, n: int) -> str:
    if seq < n / 3:
        return "opening"
    if seq >= 2 * n / 3:
        return "closing"
    return "middle"

def tag_snippets(snippets: list[dict], vocab: dict) -> list[tuple[str, str, str]]:
    """Rows (snippet_id, tag, value), deterministically ordered."""
    rows: list[tuple[str, str, str]] = []
    n = len(snippets)
    for s in snippets:
        rows.append((s["id"], "position", _position(s["seq"], n)))
        rows.append((s["id"], "turn_length", str(len(s["text"]))))
        if s["speaker"] is not None:
            rows.append((s["id"], "speaker_role", s["speaker"]))
        for fam in vocab["lexical"]:
            if fam["_rx"].search(s["text"]):
                rows.append((s["id"], fam["name"], "1"))
    rows.sort()
    return rows

def tag_interaction(unit: InteractionUnit, snippets: list[dict]) -> list[tuple[str, str, str]]:
    rows = [
        (unit.id, "interaction_len_segments", str(len(snippets))),
        (unit.id, "source_type", unit.source_type),
    ]
    for field in ("account_id", "thread_id", "date"):
        val = getattr(unit, field)
        if val is not None:
            rows.append((unit.id, field, val))
    total = sum(len(s["text"]) for s in snippets) or 1
    agent = sum(len(s["text"]) for s in snippets if s["speaker"] == "agent")
    rows.append((unit.id, "speaker_balance", f"{agent / total:.3f}"))
    rows.sort()
    return rows
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_tags.py -q`
Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add configs/tag_vocabulary_v1.yaml src/cix/tags.py tests/test_tags.py
git commit -m "feat: A1 tag vocabulary + deterministic taggers (4 families)"
```

---

### Task 6: Store — SQLite schema, sorted writes, bidirectional queries, drop log

**Files:**
- Create: `src/cix/store.py`, `tests/test_store.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_store.py`:

```python
from pathlib import Path
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def _built(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIXTURES), Path("configs/tag_vocabulary_v1.yaml"), db)
    return open_store(db)

def test_provenance_lookup_id_to_text(tmp_path):
    store = _built(tmp_path)
    s = store.snippet("int-001:0002")
    assert "already called" in s["text"]
    assert s["interaction_id"] == "int-001"

def test_span_lookup_contiguous(tmp_path):
    store = _built(tmp_path)
    span = store.span("int-001", 0, 1)
    assert len(span) == 2 and span[0]["seq"] == 0 and span[1]["seq"] == 1

def test_preselection_by_tag(tmp_path):
    store = _built(tmp_path)
    ids = store.snippets_with_tag("repeat_marker")
    assert "int-001:0002" in ids

def test_interaction_tag_query(tmp_path):
    store = _built(tmp_path)
    assert set(store.interactions_with_tag("account_id", "acct-9")) == {"int-001", "int-003"}

def test_drop_log_roundtrip(tmp_path):
    store = _built(tmp_path)
    store.log_drop(claim_ref="q1", check="quote_string_match", detail="no match in int-001:0000")
    drops = store.drops()
    assert len(drops) == 1 and drops[0]["check"] == "quote_string_match"

def test_versions_recorded(tmp_path):
    store = _built(tmp_path)
    assert store.meta("index_version") == "1.0.0"
    assert store.meta("tag_vocab_version") == "1.0.0"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_store.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.store'`

- [ ] **Step 3: Implement**

`src/cix/store.py`:

```python
import sqlite3
from pathlib import Path
from cix import INDEX_VERSION
from cix.chunker import chunk
from cix.contracts import InteractionUnit
from cix.tags import load_vocabulary, tag_interaction, tag_snippets

_SCHEMA = """
CREATE TABLE interactions (id TEXT PRIMARY KEY, source_type TEXT NOT NULL, date TEXT,
                           account_id TEXT, thread_id TEXT, participants TEXT);
CREATE TABLE snippets (id TEXT PRIMARY KEY, interaction_id TEXT NOT NULL REFERENCES interactions(id),
                       seq INTEGER NOT NULL, speaker TEXT, text TEXT NOT NULL, content_hash TEXT NOT NULL);
CREATE TABLE snippet_tags (snippet_id TEXT NOT NULL REFERENCES snippets(id), tag TEXT NOT NULL, value TEXT NOT NULL);
CREATE TABLE interaction_tags (interaction_id TEXT NOT NULL REFERENCES interactions(id), tag TEXT NOT NULL, value TEXT NOT NULL);
CREATE TABLE drop_log (n INTEGER PRIMARY KEY AUTOINCREMENT, claim_ref TEXT NOT NULL,
                       "check" TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE run_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX ix_snippet_tags ON snippet_tags (tag, value);
CREATE INDEX ix_interaction_tags ON interaction_tags (tag, value);
"""

def build_store(units: list[InteractionUnit], vocab_path: Path, db_path: Path) -> None:
    """Deterministic build: units arrive sorted (normalize), all inserts in sorted order."""
    vocab = load_vocabulary(vocab_path)
    con = sqlite3.connect(db_path)
    try:
        con.executescript(_SCHEMA)
        for u in units:
            con.execute(
                "INSERT INTO interactions VALUES (?,?,?,?,?,?)",
                (u.id, u.source_type, u.date, u.account_id, u.thread_id, ",".join(u.participants)),
            )
            snippets = chunk(u)
            for s in snippets:
                con.execute(
                    "INSERT INTO snippets VALUES (?,?,?,?,?,?)",
                    (s["id"], s["interaction_id"], s["seq"], s["speaker"], s["text"], s["content_hash"]),
                )
            con.executemany("INSERT INTO snippet_tags VALUES (?,?,?)", tag_snippets(snippets, vocab))
            con.executemany("INSERT INTO interaction_tags VALUES (?,?,?)", tag_interaction(u, snippets))
        con.executemany(
            "INSERT INTO run_meta VALUES (?,?)",
            sorted({"index_version": INDEX_VERSION, "tag_vocab_version": vocab["version"]}.items()),
        )
        con.commit()
    finally:
        con.close()

class Store:
    def __init__(self, db_path: Path):
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row

    def snippet(self, snippet_id: str) -> dict | None:
        row = self.con.execute("SELECT * FROM snippets WHERE id=?", (snippet_id,)).fetchone()
        return dict(row) if row else None

    def span(self, interaction_id: str, start: int, end: int) -> list[dict]:
        rows = self.con.execute(
            "SELECT * FROM snippets WHERE interaction_id=? AND seq BETWEEN ? AND ? ORDER BY seq",
            (interaction_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]

    def snippets_with_tag(self, tag: str, value: str | None = None) -> list[str]:
        if value is None:
            rows = self.con.execute("SELECT snippet_id FROM snippet_tags WHERE tag=? ORDER BY snippet_id", (tag,))
        else:
            rows = self.con.execute(
                "SELECT snippet_id FROM snippet_tags WHERE tag=? AND value=? ORDER BY snippet_id", (tag, value)
            )
        return [r["snippet_id"] for r in rows]

    def interactions_with_tag(self, tag: str, value: str | None = None) -> list[str]:
        if value is None:
            rows = self.con.execute("SELECT interaction_id FROM interaction_tags WHERE tag=? ORDER BY interaction_id", (tag,))
        else:
            rows = self.con.execute(
                "SELECT interaction_id FROM interaction_tags WHERE tag=? AND value=? ORDER BY interaction_id", (tag, value)
            )
        return [r["interaction_id"] for r in rows]

    def log_drop(self, claim_ref: str, check: str, detail: str) -> None:
        self.con.execute('INSERT INTO drop_log (claim_ref, "check", detail) VALUES (?,?,?)', (claim_ref, check, detail))
        self.con.commit()

    def drops(self) -> list[dict]:
        return [dict(r) for r in self.con.execute("SELECT * FROM drop_log ORDER BY n")]

    def meta(self, key: str) -> str | None:
        row = self.con.execute("SELECT value FROM run_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

def open_store(db_path: Path) -> Store:
    return Store(db_path)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_store.py -q`
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add src/cix/store.py tests/test_store.py
git commit -m "feat: SQLite run store — sorted writes, bidirectional queries, drop log"
```

---

### Task 7: Canonical hash + logical-equality property tests (AC-1)

**Files:**
- Create: `src/cix/canonical.py`, `tests/test_canonical.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_canonical.py`:

```python
import json
import shutil
from pathlib import Path
from cix.canonical import canonical_hash
from cix.normalize import load_corpus
from cix.store import build_store

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def _build(corpus_dir, db_path):
    build_store(load_corpus(corpus_dir), Path("configs/tag_vocabulary_v1.yaml"), db_path)
    return canonical_hash(db_path)

def test_rebuild_gives_identical_hash(tmp_path):
    h1 = _build(FIXTURES, tmp_path / "a.db")
    h2 = _build(FIXTURES, tmp_path / "b.db")
    assert h1 == h2

def test_file_order_and_names_do_not_matter(tmp_path):
    shuffled = tmp_path / "shuffled"
    shuffled.mkdir()
    # copy fixtures under reversed filenames so glob order differs
    for i, src in enumerate(sorted(FIXTURES.glob("*.json"), reverse=True)):
        shutil.copy(src, shuffled / f"zz-{i}.json")
    assert _build(FIXTURES, tmp_path / "a.db") == _build(shuffled, tmp_path / "c.db")

def test_content_change_changes_hash(tmp_path):
    mutated = tmp_path / "mutated"
    shutil.copytree(FIXTURES, mutated)
    doc = json.loads((mutated / "int-002.json").read_text())
    doc["segments"][0]["text"] = "How do I close my account?"
    (mutated / "int-002.json").write_text(json.dumps(doc))
    assert _build(FIXTURES, tmp_path / "a.db") != _build(mutated, tmp_path / "d.db")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_canonical.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.canonical'`

- [ ] **Step 3: Implement**

`src/cix/canonical.py`:

```python
import hashlib
import json
import sqlite3
from pathlib import Path

_LOGICAL_QUERIES = [
    ("interactions", "SELECT id, source_type, date, account_id, thread_id, participants FROM interactions ORDER BY id"),
    ("snippets", "SELECT id, interaction_id, seq, speaker, text, content_hash FROM snippets ORDER BY id"),
    ("snippet_tags", "SELECT snippet_id, tag, value FROM snippet_tags ORDER BY snippet_id, tag, value"),
    ("interaction_tags", "SELECT interaction_id, tag, value FROM interaction_tags ORDER BY interaction_id, tag, value"),
    ("run_meta", "SELECT key, value FROM run_meta ORDER BY key"),
]

def canonical_hash(db_path: Path) -> str:
    """Logical-content equality (R-IDX-4): hash canonical JSON of ordered logical rows.
    Excludes drop_log (runtime events) and any physical/byte-level detail."""
    h = hashlib.sha256()
    con = sqlite3.connect(db_path)
    try:
        for name, query in _LOGICAL_QUERIES:
            h.update(name.encode())
            for row in con.execute(query):
                h.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    finally:
        con.close()
    return h.hexdigest()
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_canonical.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/cix/canonical.py tests/test_canonical.py
git commit -m "feat: canonical logical-content hash + AC-1 property tests"
```

---

### Task 8: Evidence gate — quote check + stat recompute + drop log (AC-3a, AC-4a)

**Files:**
- Create: `src/cix/evidence.py`, `tests/fixtures/claims.json`, `tests/test_evidence.py`

- [ ] **Step 1: Write the claims fixture (one good + one planted-bad of each kind)**

`tests/fixtures/claims.json`:

```json
{
  "quotes": [
    {"ref": "q-good", "interaction_id": "int-001", "start": 2, "end": 2,
     "text": "I already called about this last time and it is still not fixed."},
    {"ref": "q-bad", "interaction_id": "int-002", "start": 0, "end": 0,
     "text": "I demand a full refund immediately."}
  ],
  "stats": [
    {"ref": "s-good", "kind": "snippet_tag_count", "tag": "repeat_marker", "expected": 1},
    {"ref": "s-bad", "kind": "snippet_tag_count", "tag": "currency_amount", "expected": 7}
  ]
}
```

- [ ] **Step 2: Write the failing tests**

`tests/test_evidence.py`:

```python
import json
from pathlib import Path
from cix.evidence import gate_claims
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIXTURES = Path(__file__).parent / "fixtures"

def _store(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIXTURES / "corpus"), Path("configs/tag_vocabulary_v1.yaml"), db)
    return open_store(db)

def _claims():
    return json.loads((FIXTURES / "claims.json").read_text())

def test_good_quote_passes_bad_quote_drops(tmp_path):
    store = _store(tmp_path)
    result = gate_claims(store, _claims())
    assert "q-good" in [q["ref"] for q in result["quotes"]]
    assert "q-bad" not in [q["ref"] for q in result["quotes"]]

def test_good_stat_passes_bad_stat_drops(tmp_path):
    store = _store(tmp_path)
    result = gate_claims(store, _claims())
    assert "s-good" in [s["ref"] for s in result["stats"]]
    assert "s-bad" not in [s["ref"] for s in result["stats"]]

def test_every_drop_is_logged_with_check_name(tmp_path):
    store = _store(tmp_path)
    gate_claims(store, _claims())
    drops = store.drops()
    checks = {d["claim_ref"]: d["check"] for d in drops}
    assert checks == {"q-bad": "quote_string_match", "s-bad": "stat_recompute"}

def test_gate_is_exact_not_fuzzy(tmp_path):
    store = _store(tmp_path)
    claims = {"quotes": [{"ref": "q-close", "interaction_id": "int-001", "start": 2, "end": 2,
                          "text": "I already called about this last time and it is still not fixed"}],  # missing final period
              "stats": []}
    result = gate_claims(store, claims)
    assert result["quotes"] == []
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_evidence.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.evidence'`

- [ ] **Step 4: Implement**

`src/cix/evidence.py`:

```python
from cix.store import Store

def _quote_ok(store: Store, q: dict) -> bool:
    """R-EVD-1 component: quoted text must appear verbatim as a full snippet text,
    or exactly equal the newline-join of the cited contiguous span."""
    span = store.span(q["interaction_id"], q["start"], q["end"])
    if not span:
        return False
    joined = "\n".join(s["text"] for s in span)
    return q["text"] == joined or any(q["text"] == s["text"] for s in span)

def _stat_ok(store: Store, s: dict) -> bool:
    """R-EVD-2 component: quantitative claim must recompute from the store."""
    if s["kind"] == "snippet_tag_count":
        return len(store.snippets_with_tag(s["tag"])) == s["expected"]
    return False  # unknown stat kinds never pass (fail closed)

def gate_claims(store: Store, claims: dict) -> dict:
    """Pass/fail, mechanical. Failures are dropped from the result and written
    to the drop log (drop-don't-flag lock + drop-log ruling)."""
    passed_quotes, passed_stats = [], []
    for q in claims.get("quotes", []):
        if _quote_ok(store, q):
            passed_quotes.append(q)
        else:
            store.log_drop(q["ref"], "quote_string_match", f"no exact match at {q['interaction_id']}:{q['start']}-{q['end']}")
    for s in claims.get("stats", []):
        if _stat_ok(store, s):
            passed_stats.append(s)
        else:
            store.log_drop(s["ref"], "stat_recompute", f"{s['kind']}({s.get('tag')}) != {s['expected']}")
    return {"quotes": passed_quotes, "stats": passed_stats}
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_evidence.py -q`
Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add src/cix/evidence.py tests/fixtures/claims.json tests/test_evidence.py
git commit -m "feat: evidence gate — exact quote match + stat recompute, drops logged (AC-3a/4a)"
```

---

### Task 9: Run manifest (A3)

**Files:**
- Create: `docs/A3_run_manifest_schema.md`, `src/cix/manifest.py`, `tests/test_manifest.py`

- [ ] **Step 1: Write the schema doc**

`docs/A3_run_manifest_schema.md`:

```markdown
# A3 — Run Manifest Schema · v1

One `manifest.json` per run directory, alongside `run.db`. Fields (R-IDX-6):

| Field | Type | G1 value |
|---|---|---|
| `manifest_version` | str | "1.0.0" |
| `corpus_hash` | str | sha256 over sorted (interaction_id, canonical unit JSON) |
| `canonical_hash` | str | logical-content hash of the built store |
| `index_version` | str | from `cix.INDEX_VERSION` |
| `tag_vocab_version` | str | from A1 config |
| `label_schema_version` | str\|null | null until G2 |
| `rubric_version` | str\|null | null until G2 |
| `catalogue_version` | str\|null | null until G4 |
| `model_versions` | object | {} until G2 |
| `prompt_hashes` | object | {} until G2 |
| `seeds` | object | {} until G2 (all sampling seeded from G2 on) |
| `thresholds_version` | str\|null | null until G2 freeze |
| `privacy_gate` | str | `synthetic-fixture` \| `scrubbed` |
| `corpus_clearance` | str | provenance/clearance note (informal ruling: manifest records it) |
| `created_at` | str | ISO timestamp — excluded from canonical/corpus hashes |
```

- [ ] **Step 2: Write the failing tests**

`tests/test_manifest.py`:

```python
import json
from pathlib import Path
from cix.manifest import build_manifest, write_manifest
from cix.normalize import load_corpus

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def test_manifest_fields_and_write(tmp_path):
    units = load_corpus(FIXTURES)
    m = build_manifest(units, canonical_hash="abc123", tag_vocab_version="1.0.0",
                       privacy_gate="synthetic-fixture", corpus_clearance="n/a: synthetic fixtures")
    assert m["index_version"] == "1.0.0"
    assert m["label_schema_version"] is None
    assert m["seeds"] == {}
    assert len(m["corpus_hash"]) == 64
    path = write_manifest(m, tmp_path)
    on_disk = json.loads(path.read_text())
    assert on_disk == m

def test_corpus_hash_is_content_stable():
    units = load_corpus(FIXTURES)
    m1 = build_manifest(units, "x", "1.0.0", "synthetic-fixture", "n/a")
    m2 = build_manifest(list(units), "x", "1.0.0", "synthetic-fixture", "n/a")
    assert m1["corpus_hash"] == m2["corpus_hash"]

def test_created_at_not_in_hashes():
    units = load_corpus(FIXTURES)
    m = build_manifest(units, "x", "1.0.0", "synthetic-fixture", "n/a")
    assert "created_at" in m and m["created_at"] not in (m["corpus_hash"], m["canonical_hash"])
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_manifest.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.manifest'`

- [ ] **Step 4: Implement**

`src/cix/manifest.py`:

```python
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from cix import INDEX_VERSION
from cix.contracts import InteractionUnit

MANIFEST_VERSION = "1.0.0"

def corpus_hash(units: list[InteractionUnit]) -> str:
    h = hashlib.sha256()
    for u in sorted(units, key=lambda u: u.id):
        h.update(u.model_dump_json().encode("utf-8"))
    return h.hexdigest()

def build_manifest(units, canonical_hash: str, tag_vocab_version: str,
                   privacy_gate: str, corpus_clearance: str) -> dict:
    return {
        "manifest_version": MANIFEST_VERSION,
        "corpus_hash": corpus_hash(units),
        "canonical_hash": canonical_hash,
        "index_version": INDEX_VERSION,
        "tag_vocab_version": tag_vocab_version,
        "label_schema_version": None,
        "rubric_version": None,
        "catalogue_version": None,
        "model_versions": {},
        "prompt_hashes": {},
        "seeds": {},
        "thresholds_version": None,
        "privacy_gate": privacy_gate,
        "corpus_clearance": corpus_clearance,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def write_manifest(manifest: dict, run_dir: Path) -> Path:
    path = Path(run_dir) / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_manifest.py -q`
Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add docs/A3_run_manifest_schema.md src/cix/manifest.py tests/test_manifest.py
git commit -m "feat: A3 run manifest — schema doc, builder, content-stable corpus hash"
```

---

### Task 10: Label schema config (A2 — authored, consumed at G2)

**Files:**
- Create: `configs/label_schema_v1.yaml`, `tests/test_label_schema_config.py`

- [ ] **Step 1: Write the config**

`configs/label_schema_v1.yaml`:

```yaml
# A2 — CIX core label schema (D§5: core-only for v1; no domain extensions).
# Consumed by the G2 label pass. Authored at G1 so the artifact set is complete.
version: "1.0.0"
fields:
  motion:
    values: [revenue, service, mixed]
  intent:
    type: short_text
  driver_origin:
    values: [customer, internal_defect, policy, upstream_function]
  automatability:
    values: [rote, assisted, exception]
  outcome:
    values: [resolved, deferred, escalated, unresolved]
  handoff_events:
    type: list
```

- [ ] **Step 2: Write the validation test**

`tests/test_label_schema_config.py`:

```python
from pathlib import Path
import yaml

CORE_FIELDS = {"motion", "intent", "driver_origin", "automatability", "outcome", "handoff_events"}

def test_label_schema_is_core_only_and_versioned():
    schema = yaml.safe_load(Path("configs/label_schema_v1.yaml").read_text())
    assert schema["version"] == "1.0.0"
    assert set(schema["fields"].keys()) == CORE_FIELDS  # R-RUB-4: no domain extensions
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_label_schema_config.py -q`
Expected: `1 passed`

- [ ] **Step 4: Commit**

```bash
git add configs/label_schema_v1.yaml tests/test_label_schema_config.py
git commit -m "feat: A2 core label schema config (core-only, versioned)"
```

---

### Task 11: CLI — `cix index`, `cix hash`, `cix verify`

**Files:**
- Create: `src/cix/cli.py`, `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_cli.py`:

```python
import json
from pathlib import Path
from cix.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

def test_index_builds_run_dir(tmp_path, capsys):
    rc = main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "run1")])
    assert rc == 0
    assert (tmp_path / "run1" / "run.db").exists()
    manifest = json.loads((tmp_path / "run1" / "manifest.json").read_text())
    assert manifest["privacy_gate"] == "synthetic-fixture"
    assert manifest["canonical_hash"] == json.loads(capsys.readouterr().out)["canonical_hash"]

def test_hash_reproduces(tmp_path, capsys):
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "runA")])
    outA = json.loads(capsys.readouterr().out)
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "runB")])
    outB = json.loads(capsys.readouterr().out)
    assert outA["canonical_hash"] == outB["canonical_hash"]
    rc = main(["hash", str(tmp_path / "runA")])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["canonical_hash"] == outA["canonical_hash"]

def test_verify_reports_drops(tmp_path, capsys):
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "run1")])
    capsys.readouterr()
    rc = main(["verify", str(tmp_path / "run1"), "--claims", str(FIXTURES / "claims.json")])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1  # drops occurred → nonzero for visibility
    assert out["passed"] == {"quotes": 1, "stats": 1}
    assert out["dropped"] == 2

def test_invalid_corpus_fails_before_any_output(tmp_path, capsys):
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "x.json").write_text("{not json")
    rc = main(["index", str(bad), "--out", str(tmp_path / "run2")])
    assert rc == 2
    assert not (tmp_path / "run2" / "run.db").exists()  # R-RUN-1: validate before writing
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.cli'`

- [ ] **Step 3: Implement**

`src/cix/cli.py`:

```python
import argparse
import json
import sys
from pathlib import Path
from cix.canonical import canonical_hash
from cix.evidence import gate_claims
from cix.manifest import build_manifest, write_manifest
from cix.normalize import CorpusValidationError, load_corpus
from cix.store import build_store, open_store
from cix.tags import load_vocabulary

VOCAB_PATH = Path("configs/tag_vocabulary_v1.yaml")

def _cmd_index(args) -> int:
    try:
        units = load_corpus(Path(args.corpus))          # validates BEFORE any write (R-RUN-1)
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "run.db"
    build_store(units, VOCAB_PATH, db)
    chash = canonical_hash(db)
    vocab = load_vocabulary(VOCAB_PATH)
    manifest = build_manifest(units, chash, vocab["version"],
                              privacy_gate="synthetic-fixture",
                              corpus_clearance=args.clearance)
    write_manifest(manifest, out)
    print(json.dumps({"run": str(out), "interactions": len(units), "canonical_hash": chash}))
    return 0

def _cmd_hash(args) -> int:
    print(json.dumps({"canonical_hash": canonical_hash(Path(args.run) / "run.db")}))
    return 0

def _cmd_verify(args) -> int:
    store = open_store(Path(args.run) / "run.db")
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    result = gate_claims(store, claims)
    dropped = len(store.drops())
    print(json.dumps({"passed": {"quotes": len(result["quotes"]), "stats": len(result["stats"])},
                      "dropped": dropped}))
    return 1 if dropped else 0

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cix")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_index = sub.add_parser("index", help="build a run store from a corpus directory")
    p_index.add_argument("corpus")
    p_index.add_argument("--out", required=True)
    p_index.add_argument("--clearance", default="n/a: synthetic fixtures")
    p_index.set_defaults(fn=_cmd_index)
    p_hash = sub.add_parser("hash", help="print the canonical hash of a run")
    p_hash.add_argument("run")
    p_hash.set_defaults(fn=_cmd_hash)
    p_verify = sub.add_parser("verify", help="run the evidence gate over a claims file")
    p_verify.add_argument("run")
    p_verify.add_argument("--claims", required=True)
    p_verify.set_defaults(fn=_cmd_verify)
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cli.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/cix/cli.py tests/test_cli.py
git commit -m "feat: cix CLI — index / hash / verify"
```

---

### Task 12: G1 exit check — full suite, end-to-end run, push

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest -q`
Expected: all tests pass (≈31), zero warnings that indicate nondeterminism.

- [ ] **Step 2: Exercise the CLI end-to-end manually**

```bash
uv run cix index tests/fixtures/corpus --out /tmp/cix-g1-run
uv run cix hash /tmp/cix-g1-run
uv run cix verify /tmp/cix-g1-run --claims tests/fixtures/claims.json
```

Expected: `index` and `hash` print matching `canonical_hash`; `verify` prints `"passed": {"quotes": 1, "stats": 1}, "dropped": 2` and exits 1.

- [ ] **Step 3: Verify G1 exit criteria against the PRD**

- AC-1: `test_canonical.py` green (rebuild equality + order independence + sensitivity) ✓
- AC-3a: planted bad quote dropped and drop-logged (`test_evidence.py`) ✓
- AC-4a: wrong stat dropped and drop-logged ✓
- A1, A2, A3, A12 all exist as committed artifacts ✓

- [ ] **Step 4: Commit any stragglers and push**

```bash
git status --short   # expect clean or only docs
git push
```

- [ ] **Step 5: Record G1 complete**

Add to `docs/CIX_PRD_v1_2026-07-31.md` changelog: `- **<date> — G1 exit.** Deterministic spine complete; AC-1/AC-3a/AC-4a green.` Commit and push.

---

## Verification (whole plan)

1. `uv run pytest -q` — full suite green.
2. Determinism spot-check beyond the property test: `uv run cix index tests/fixtures/corpus --out /tmp/r1 && uv run cix index tests/fixtures/corpus --out /tmp/r2` → identical `canonical_hash` in both outputs.
3. Evidence gate honesty check: edit a fixture quote by one character in a scratch claims file → `cix verify` drops it (exact match, not fuzzy).
4. G0 human checklist items are KP's and do not block any task here.

## What the next plan (G2) will need from this one

`Store` query surface (`snippets_with_tag`, `span`, `meta`), `canonical_hash`, manifest fields (`label_schema_version`, `model_versions`, `seeds`, `prompt_hashes` currently null/empty — G2 fills them), and the A2 label schema config. No rework expected.
