# G5 Rehearsal — Synthetic FS Corpus + CLI Glue: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build everything G5's execution path needs — a thread-aware synthetic service corpus generator (`servicegen`), the `cix self-test` / `cix differential` / `cix generate-service-corpus` CLI commands, and one end-to-end O1-labeled rehearsal run — so that when the real FS corpus (OD-1) lands, G5 is pure execution.

**Architecture:** One new module (`src/cix/servicegen.py`, modeled on `calgen.py` but thread-aware; calgen untouched), one new config (`configs/service_corpus_spec_v1.yaml`), three new CLI subcommands, and a behavior-preserving refactor that extracts the Pass-A detection path (`label → rubric → rollup`) out of `_cmd_run` so `cix run` and `cix differential` share one code path. `configs/differential_design_v1.yaml` gets a machine-readability-only v1.0.1 bump (PO checkpoint). No frozen threshold numbers move.

**Tech Stack:** Python 3.12 · uv · pytest · pydantic v2 · PyYAML · SQLite. Run all tests with `uv run pytest`.

**Spec:** `docs/superpowers/specs/2026-08-03-g5-rehearsal-design.md` (approved 2026-08-03).

**Branch:** create `feat/g5-rehearsal` from `docs/g5-rehearsal-spec` (so the spec is present):
`git checkout docs/g5-rehearsal-spec && git checkout -b feat/g5-rehearsal`

---

## File structure

| File | Responsibility |
|---|---|
| `configs/service_corpus_spec_v1.yaml` | **Create.** Service-domain generation spec: 8 pathologies mapped to A9 item IDs (firewall: never item text), 3 repeat-contact threads, singles, cleans — 100 interactions total |
| `src/cix/servicegen.py` | **Create.** Spec models + deterministic slot builder + thread-aware generation → `corpus/`, `truth.json`, `provenance.yaml`. Never references rubric machinery (structural firewall) |
| `src/cix/cli.py` | **Modify.** Extract `_detect()` helper from `_cmd_run`; add `generate-service-corpus`, `self-test`, `differential` subcommands |
| `configs/differential_design_v1.yaml` | **Modify → v1.0.1.** Add `target_item` + selection params per variant. Tolerances/perturbations/expected-delta semantics byte-identical. **PO ratification checkpoint** |
| `tests/test_service_spec.py` | **Create.** Spec loads, A9 crosswalk, 5-gram firewall disjointness, coverage minimums, slot shapes, structural firewall |
| `tests/test_servicegen.py` | **Create.** Offline generation: threads share `thread_id`, truth registry, provenance, prompt-level firewall |
| `tests/test_cli_selftest.py` | **Create.** `cix self-test` glue over a fabricated run dir |
| `tests/test_cli_differential.py` | **Create.** `cix differential` glue: variant construction, scripted re-detection, T-DIFF scoring, corpus-hash integrity refusal |
| `tests/test_cli.py` | Existing CLI tests — must stay green throughout (guards the `_detect` refactor together with `tests/test_run_e2e.py`) |
| `README.md`, `docs/superpowers/plans/ROADMAP.md`, spec header | **Modify.** Exit doc pass |

Key existing interfaces (do not change them):
- `label_corpus(store, units, client, corpus_hash, schema_version, model) -> label_artifact_id` (`labels.py:37`)
- `run_rubric(store, units, rubric, label_artifact_id, client, model) -> hit_artifact_id` (`hits.py:36`)
- `store.hits_for(ha) -> [{item_id, interaction_id, unit, snippet_ids}]`; `store.labeled_interactions(la) -> [ids]`; `store.write_validation(check, item_id, status, detail)`
- `rollup(hits, eligible_interactions) -> {"items": {item_id: {"count": n, "unit": ..., ...}}, "rank_by_unit": ...}`
- `self_test(all_ids, hits, spec, catalogue=None, crosswalk=None) -> {"state", "material_fraction", "per_seed", "per_layer_fraction", "layers_compared", ...}` (`selftest.py:68`)
- `delete_subset(units, drop_ids) / duplicate_chains(units, thread_id) / splice_instances(units, donor, copies) -> (variant_units, expected_meta)`; `score_delta(expected, observed, tolerance)` (`differential.py`)
- `load_rubric(path, label_schema_version, tag_vocab_version)`; `scrub_corpus(units, proto, salt)`; `corpus_hash(units)` (`manifest.py:10`, imported in cli.py as `manifest_corpus_hash`)
- CLI test pattern: `monkeypatch.setattr(cli, "make_client", lambda cfg: <ScriptedClient>)` (see `tests/test_run_e2e.py`)

---

### Task 1: Service corpus spec + spec models + slot builder

**Files:**
- Create: `configs/service_corpus_spec_v1.yaml`
- Create: `src/cix/servicegen.py` (models + loader + slot builder only; generation is Task 2)
- Test: `tests/test_service_spec.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_service_spec.py`:

```python
import re
from pathlib import Path
from cix.servicegen import build_service_slots, load_service_spec
from cix.rubric import load_rubric

SPEC = Path("configs/service_corpus_spec_v1.yaml")

def _ngrams(text: str, n: int = 5) -> set[str]:
    toks = re.findall(r"[a-z']+", text.lower())
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}

def test_spec_loads_and_crosswalk_targets_real_a9_items():
    spec = load_service_spec(SPEC)
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    item_ids = {i.id for i in rubric.items}
    assert {p.maps_to_item for p in spec.pathologies} <= item_ids
    assert len(spec.pathologies) == 8

def test_vocabulary_disjointness_against_a9():
    """R-VAL-2 discipline: the plant author sees pathology descriptions, never rubric text.
    No description (or thread issue) shares a 5-token n-gram with any A9 criterion/exemplar."""
    spec = load_service_spec(SPEC)
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    rubric_text = " ".join([i.criterion for i in rubric.items]
                           + [e for i in rubric.items for e in i.exemplars])
    for p in spec.pathologies:
        overlap = _ngrams(p.description) & _ngrams(rubric_text)
        assert not overlap, f"{p.key} shares wording with A9 text: {overlap}"
    for t in spec.threads:
        overlap = _ngrams(t.issue) & _ngrams(rubric_text)
        assert not overlap, f"thread {t.key} issue shares wording with A9 text: {overlap}"

def test_differential_target_coverage_minimums():
    """Spec §3.1 hard requirement: >=6 repeat_contact plants, >=2 threads, >=3 deterministic."""
    spec = load_service_spec(SPEC)
    by_key = {p.key: p for p in spec.pathologies}
    repeat = sum(t.interactions - 1 for t in spec.threads
                 if by_key[t.pathology].maps_to_item == "repeat_contact_unresolved")
    repeat += sum(s.count for s in spec.singles
                  if by_key[s.pathology].maps_to_item == "repeat_contact_unresolved")
    determin = sum(s.count for s in spec.singles
                   if by_key[s.pathology].maps_to_item == "deterministic_request")
    assert repeat >= 6
    assert len(spec.threads) >= 2
    assert determin >= 3

def test_slot_shapes_and_determinism():
    spec = load_service_spec(SPEC)
    slots = build_service_slots(spec)
    thread_slots = [s for s in slots if s["kind"] == "thread"]
    plant_slots = [s for s in slots if s["kind"] == "plant"]
    clean_slots = [s for s in slots if s["kind"] == "clean"]
    assert len(thread_slots) == sum(t.interactions for t in spec.threads)
    assert len(plant_slots) == sum(s.count for s in spec.singles)
    assert len(clean_slots) == spec.clean_interactions
    assert len(slots) == 100
    # first contact of a thread carries no plant; later contacts carry the thread pathology
    firsts = [s for s in thread_slots if s["contact_index"] == 1]
    assert all(s["pathology"] is None for s in firsts)
    assert all(s["pathology"] is not None for s in thread_slots if s["contact_index"] > 1)
    assert build_service_slots(spec) == slots            # deterministic per seed

def test_servicegen_never_touches_rubric_code():
    """Collusion break, structural: the generator module must not import or read rubric machinery."""
    import cix.servicegen
    src = Path(cix.servicegen.__file__).read_text(encoding="utf-8")
    assert "rubric" not in src.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_service_spec.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cix.servicegen'`

- [ ] **Step 3: Write the config**

`configs/service_corpus_spec_v1.yaml` (complete file; if the disjointness test in Step 5 flags a 5-gram overlap with A9 text, reword the flagged description — wording below is drafted to be disjoint):

```yaml
# Service corpus spec v1 — synthetic FS-shaped rehearsal corpus (G5 rehearsal spec §3.1).
# FIREWALL: pathology descriptions are the ONLY pathology text the generator sees; they map
# to A9 item IDs, never item text (R-VAL-2 discipline; enforced by tests/test_service_spec.py).
# O1-ONLY by construction (PRD §2.3): this corpus is synthetic and is never presented as O2/O3.
# Coverage minimums (spec §3.1): >=6 repeat_contact plants, >=2 threads, >=3 deterministic.
version: "1.0.0"
id_prefix: svc
seed: 20260803
style_guide: |
  Register: North American B2B software/services customer support, mid-market. Transcripts
  are lightly imperfect speech-to-text: occasional false starts, fillers ("yeah, so"),
  interruptions marked with a dash, no stage directions. Emails are terse, subject implied,
  sign-offs minimal. Agents reference tools generically (the ticketing system, the billing
  tool, the knowledge base, the admin console) — never real vendor names. Customers have
  concrete, mundane concerns: invoices, logins, user provisioning, data imports, go-live
  dates, plan changes. Numbers are specific ($ amounts, dates, ticket numbers, seat counts)
  but unremarkable. Nobody narrates the problem category or names it; it shows up the way
  it would in real work. Purity: an interaction carries at most the single workplace
  problem it is built around; everything else in it is competent and forgettable.
threads:
  # Repeat-contact chains: contact 1 raises the issue (unresolved at end, no plant);
  # contacts 2..n each plant the thread pathology. Repeat plants: 3 + 2 + 2 = 7.
  - key: TH1
    pathology: SP1
    interactions: 4
    issue: "a monthly subscription invoice that keeps showing one seat bundle twice"
  - key: TH2
    pathology: SP1
    interactions: 3
    issue: "a data import job that stalls partway and has to be restarted by support"
  - key: TH3
    pathology: SP1
    interactions: 3
    issue: "an admin account that keeps locking out every few days for no clear reason"
singles:
  - {pathology: SP1, count: 1}    # a standalone repeat-contact mention; total repeat = 8
  - {pathology: SP2, count: 8}
  - {pathology: SP3, count: 6}    # deterministic_request donors for V3
  - {pathology: SP4, count: 6}
  - {pathology: SP5, count: 5}
  - {pathology: SP6, count: 4}
  - {pathology: SP7, count: 5}
  - {pathology: SP8, count: 4}
clean_interactions: 51            # 10 thread + 39 singles + 51 clean = 100
pathologies:
  - key: SP1
    maps_to_item: repeat_contact_unresolved
    description: >
      Someone reaches out yet again because an earlier issue never actually got fixed;
      each fresh touchpoint is the same old complaint resurfacing, and the person makes
      clear this is not their first attempt.
  - key: SP2
    maps_to_item: billing_defect_driver
    description: >
      The whole reason this person got in touch is something wrong on an invoice or
      statement — a figure that does not add up, an unexpected line entry, money taken
      that should not have been.
  - key: SP3
    maps_to_item: deterministic_request
    description: >
      The person wants one tiny routine thing done — a credential reset, a mailing
      detail changed, a toggle flipped — a fixed-script chore needing zero judgment,
      yet a human still has to do it for them.
  - key: SP4
    maps_to_item: manual_after_call_work
    description: >
      Once the customer is gone, the agent grinds through by-hand record keeping:
      retyping what happened into internal systems, copying details between tools,
      finishing paperwork the conversation created.
  - key: SP5
    maps_to_item: avoidable_transfer
    description: >
      The caller gets bounced to another person or queue for something the person who
      first answered could plausibly have handled themselves.
  - key: SP6
    maps_to_item: knowledge_inconsistency
    description: >
      Two people at the company give conflicting explanations of the same policy or
      procedure, and the customer notices the contradiction and has to push for a
      straight answer.
  - key: SP7
    maps_to_item: status_chase_inbound
    description: >
      The person's only purpose in reaching out is to ask where things stand on
      something already underway, because nobody told them proactively.
  - key: SP8
    maps_to_item: unanticipated_failure
    description: >
      The customer had to be the one to notice and report a breakage the company's
      own systems could have caught and flagged first.
```

- [ ] **Step 4: Write the models + loader + slot builder**

`src/cix/servicegen.py` (module start; generation functions are appended in Task 2):

```python
"""Synthetic FS-shaped service corpus generator (G5 rehearsal spec, 2026-08-03).
COLLUSION FIREWALL: like calgen, this module must never reference the detection
side's judgment machinery — it consumes pathology descriptions from the service
spec and nothing else (R-VAL-2 discipline; enforced by tests/test_service_spec.py).
Output is synthetic and O1-only by construction (PRD §2.3)."""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, model_validator
from cix.contracts import InteractionUnit
from cix.model import MalformedResponse, ModelClient, complete_json

GEN_PROMPT_VERSION = "1.0.0"

class ServicePathology(BaseModel):
    key: str
    maps_to_item: str            # item id only — never item text (firewall holds)
    description: str
    source_type: Literal["transcript", "email", "note"] = "transcript"
    participants: list[str] = ["agent", "customer"]

class ThreadSpec(BaseModel):
    key: str
    pathology: str               # planted in contacts 2..n; contact 1 just raises the issue
    interactions: int = Field(ge=2)
    issue: str                   # continuity anchor fed to every contact's prompt

class SingleSpec(BaseModel):
    pathology: str
    count: int = Field(ge=1)

class ServiceSpec(BaseModel):
    version: str
    id_prefix: str
    seed: int
    style_guide: str
    threads: list[ThreadSpec]
    singles: list[SingleSpec]
    clean_interactions: int
    pathologies: list[ServicePathology]

    @model_validator(mode="after")
    def _referenced_pathologies_exist(self):
        keys = {p.key for p in self.pathologies}
        missing = ({t.pathology for t in self.threads} | {s.pathology for s in self.singles}) - keys
        if missing:
            raise ValueError(f"spec references unknown pathology keys: {sorted(missing)}")
        return self

def load_service_spec(path: Path) -> ServiceSpec:
    return ServiceSpec.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

def build_service_slots(spec: ServiceSpec) -> list[dict]:
    """Deterministic slot assignment per spec seed (mirrors calgen.build_slots discipline)."""
    by_key = {p.key: p for p in spec.pathologies}
    slots: list[dict] = []
    for t in spec.threads:
        for k in range(1, t.interactions + 1):
            slots.append({"kind": "thread", "thread": t, "contact_index": k,
                          "pathology": by_key[t.pathology] if k > 1 else None})
    for s in spec.singles:
        for _ in range(s.count):
            slots.append({"kind": "plant", "pathology": by_key[s.pathology]})
    slots += [{"kind": "clean"} for _ in range(spec.clean_interactions)]
    random.Random(spec.seed).shuffle(slots)
    return slots
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_service_spec.py -v`
Expected: PASS (5 tests). If `test_vocabulary_disjointness_against_a9` fails, it prints the shared 5-grams — reword the flagged description/issue in the YAML (change words, keep meaning) and re-run until green.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q`
Expected: all green (existing 171 + 5 new)

- [ ] **Step 7: Commit**

```bash
git add configs/service_corpus_spec_v1.yaml src/cix/servicegen.py tests/test_service_spec.py
git commit -m "feat(servicegen): service corpus spec v1 + models + deterministic slot builder (firewall enforced)"
```

---

### Task 2: `servicegen` generation — prompts, threads, truth, provenance

**Files:**
- Modify: `src/cix/servicegen.py` (append prompts + generation)
- Test: `tests/test_servicegen.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_servicegen.py`:

```python
import json
from pathlib import Path
import yaml
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.servicegen import generate_service_corpus, load_service_spec

SPEC = Path("configs/service_corpus_spec_v1.yaml")

def _mini_spec(tmp_path: Path) -> Path:
    doc = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    doc["threads"] = [{"key": "TH1", "pathology": "SP1", "interactions": 3,
                       "issue": "a data import job that stalls partway"}]
    doc["singles"] = [{"pathology": "SP3", "count": 1}]
    doc["clean_interactions"] = 2
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p

def _canned(n: int) -> ScriptedClient:
    seg = json.dumps({"segments": [
        {"speaker": "agent", "text": "Thanks for calling, what can I do for you?"},
        {"speaker": "customer", "text": "Quick one about our account."}]})
    return ScriptedClient(sequence=[seg] * n)

def test_generate_mini_corpus(tmp_path):
    spec = load_service_spec(_mini_spec(tmp_path))
    out = tmp_path / "svc"
    truth = generate_service_corpus(spec, _canned(6), out, model_name="test-model", lab="openai")
    units = load_corpus(out / "corpus")                  # truth/provenance must not break loading
    assert len(units) == 6 and len(truth) == 6
    threaded = [u for u in units if u.thread_id is not None]
    assert len(threaded) == 3
    assert {u.thread_id for u in threaded} == {"svc-TH1"}
    assert all(u.account_id == "acct-TH1" for u in threaded)
    planted = {k: v for k, v in truth.items() if v}
    # thread contacts 2..3 plant SP1, plus the SP3 single = 3 plants
    assert len(planted) == 3
    assert sorted(v["pathology"] for v in planted.values()) == ["SP1", "SP1", "SP3"]
    assert sum(1 for v in planted.values() if v["thread"] == "TH1") == 2
    prov = yaml.safe_load((out / "provenance.yaml").read_text(encoding="utf-8"))
    assert prov["generator_lab"] == "openai"
    assert prov["generator_model"] == "test-model"
    assert prov["spec_version"] == spec.version
    on_disk = json.loads((out / "truth.json").read_text(encoding="utf-8"))
    assert on_disk == truth

def test_thread_prompts_carry_continuity(tmp_path):
    """Contact k>1 prompts name the ongoing issue and the contact number; contact 1 sets it up."""
    spec = load_service_spec(_mini_spec(tmp_path))
    seen: list[str] = []
    class Spy(ScriptedClient):
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return super().complete(prompt)
    generate_service_corpus(spec, Spy(sequence=_canned(6).sequence), tmp_path / "o", "m", "openai")
    thread_prompts = [p for p in seen if "ongoing chain" in p]
    assert len(thread_prompts) == 3
    assert sum(1 for p in thread_prompts if "contact 1 " in p) == 1
    assert all("a data import job that stalls partway" in p for p in thread_prompts)

def test_prompts_never_contain_a9_text(tmp_path):
    """Firewall at the prompt level: no A9 criterion or exemplar string in any generation prompt."""
    from cix.rubric import load_rubric   # imported in the TEST, never in servicegen
    spec = load_service_spec(_mini_spec(tmp_path))
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    seen: list[str] = []
    class Spy(ScriptedClient):
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return super().complete(prompt)
    generate_service_corpus(spec, Spy(sequence=_canned(6).sequence), tmp_path / "o", "m", "openai")
    for prompt in seen:
        for item in rubric.items:
            assert item.criterion not in prompt
            for e in item.exemplars:
                assert e not in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_servicegen.py -v`
Expected: FAIL — `ImportError: cannot import name 'generate_service_corpus'`

- [ ] **Step 3: Append prompts + generation to `src/cix/servicegen.py`**

```python
_GEN_PROMPT = """You are writing one synthetic B2B customer-service interaction for a pipeline-rehearsal corpus.

Follow this style guide strictly:
{style}

Interaction form: {source_type} between {participants}, 6-14 turns.

{block}

Return ONLY JSON: {{"segments": [{{"speaker": "...", "text": "..."}}]}}
Every segment is one speaker turn. Plausible, mundane, specific business detail. No meta-commentary, no labels, no explanations.
"""

_PLANT_BLOCK = """Embed the following workplace problem exactly once, plainly present but not dwelt on:
{description}
Everything else in the interaction is routine and competent."""

_CLEAN_BLOCK = ("This interaction is routine and competent: the request is handled cleanly "
                "on first contact, no notable workplace problem of any kind.")

_THREAD_FIRST_BLOCK = """This is contact 1 of an ongoing chain. The customer raises this issue for the first time, and it is NOT fully fixed by the end — the agent promises a follow-up:
{issue}
Do not foreshadow future contacts; write it as an ordinary interaction that happens to end without a durable fix."""

_THREAD_REPEAT_BLOCK = """This is contact {k} in an ongoing chain about the same still-unfixed issue:
{issue}
The customer naturally references having been in touch about this before. Embed the following workplace problem exactly once, plainly present:
{description}
The issue is still not durably fixed at the end. Everything else is routine and competent."""

def gen_prompts_hash() -> str:
    joined = (_GEN_PROMPT + _PLANT_BLOCK + _CLEAN_BLOCK + _THREAD_FIRST_BLOCK
              + _THREAD_REPEAT_BLOCK + GEN_PROMPT_VERSION)
    return hashlib.sha256(joined.encode()).hexdigest()[:16]

def _prompt_for(spec: ServiceSpec, slot: dict) -> tuple[str, str, list[str]]:
    if slot["kind"] == "thread":
        t: ThreadSpec = slot["thread"]
        p: ServicePathology | None = slot["pathology"]
        if slot["contact_index"] == 1:
            block, st, parts = _THREAD_FIRST_BLOCK.format(issue=t.issue), "transcript", ["agent", "customer"]
        else:
            block = _THREAD_REPEAT_BLOCK.format(k=slot["contact_index"], issue=t.issue,
                                                description=p.description.strip())
            st, parts = p.source_type, p.participants
    elif slot["kind"] == "plant":
        p = slot["pathology"]
        block = _PLANT_BLOCK.format(description=p.description.strip())
        st, parts = p.source_type, p.participants
    elif slot["kind"] == "clean":
        block, st, parts = _CLEAN_BLOCK, "transcript", ["agent", "customer"]
    else:
        raise ValueError(f"unknown slot kind: {slot['kind']!r}")
    return _GEN_PROMPT.format(style=spec.style_guide.strip(), source_type=st,
                              participants=" and ".join(parts), block=block), st, parts

def generate_service_corpus(spec: ServiceSpec, client: ModelClient, out_dir: Path,
                            model_name: str, lab: str) -> dict:
    corpus_dir = Path(out_dir) / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    truth: dict = {}
    for i, slot in enumerate(build_service_slots(spec)):
        uid = f"{spec.id_prefix}-{i:03d}"
        prompt, st, parts = _prompt_for(spec, slot)
        out = complete_json(client, prompt)
        if "segments" not in out:
            raise MalformedResponse(f"generation response for {uid} lacks 'segments'")
        extra = {}
        if slot["kind"] == "thread":
            extra = {"thread_id": f"{spec.id_prefix}-{slot['thread'].key}",
                     "account_id": f"acct-{slot['thread'].key}"}
        unit = InteractionUnit.model_validate(
            {"id": uid, "source_type": st, "participants": parts,
             "segments": out["segments"], **extra})
        (corpus_dir / f"{uid}.json").write_text(unit.model_dump_json(indent=2), encoding="utf-8")
        if slot["kind"] == "thread" and slot["pathology"] is not None:
            truth[uid] = {"pathology": slot["pathology"].key, "thread": slot["thread"].key,
                          "expected_occurrences": 1}
        elif slot["kind"] == "plant":
            truth[uid] = {"pathology": slot["pathology"].key, "thread": None,
                          "expected_occurrences": 1}
        else:
            truth[uid] = None
    (Path(out_dir) / "truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    (Path(out_dir) / "provenance.yaml").write_text(yaml.safe_dump({
        "generator_lab": lab, "generator_model": model_name,
        "gen_prompt_version": GEN_PROMPT_VERSION, "gen_prompts_hash": gen_prompts_hash(),
        "spec_version": spec.version, "corpus_kind": "service-rehearsal-synthetic-O1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }), encoding="utf-8")
    return truth
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_servicegen.py tests/test_service_spec.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/cix/servicegen.py tests/test_servicegen.py
git commit -m "feat(servicegen): thread-aware generation — continuity prompts, truth registry, provenance"
```

---

### Task 3: `cix generate-service-corpus` subcommand

**Files:**
- Modify: `src/cix/cli.py`
- Test: `tests/test_cli_servicegen.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli_servicegen.py`:

```python
import json
from pathlib import Path
import yaml
from cix.cli import main
from cix.model import ScriptedClient

def _mini_spec(tmp_path: Path) -> Path:
    doc = yaml.safe_load(Path("configs/service_corpus_spec_v1.yaml").read_text(encoding="utf-8"))
    doc["threads"] = [{"key": "TH1", "pathology": "SP1", "interactions": 2,
                       "issue": "a data import job that stalls partway"}]
    doc["singles"] = [{"pathology": "SP3", "count": 1}]
    doc["clean_interactions"] = 1
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p

def test_generate_service_corpus_command(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    seg = json.dumps({"segments": [{"speaker": "agent", "text": "How can I help?"},
                                   {"speaker": "customer", "text": "Question on our account."}]})
    monkeypatch.setattr(cli, "make_second_client", lambda cfg: ScriptedClient(sequence=[seg] * 4))
    rc = main(["generate-service-corpus", "--spec", str(_mini_spec(tmp_path)),
               "--out", str(tmp_path / "svc")])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["interactions"] == 4 and out["planted"] == 2   # 1 thread repeat + 1 single
    assert (tmp_path / "svc" / "corpus").is_dir()
    assert (tmp_path / "svc" / "truth.json").exists()
    assert (tmp_path / "svc" / "provenance.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_servicegen.py -v`
Expected: FAIL — argparse error `invalid choice: 'generate-service-corpus'` (exits 2 via SystemExit)

- [ ] **Step 3: Implement the subcommand**

In `src/cix/cli.py`, add to the imports block:

```python
from cix.servicegen import generate_service_corpus, load_service_spec
```

Add the command function after `_cmd_generate_calibration`:

```python
def _cmd_generate_service(args) -> int:
    spec = load_service_spec(Path(args.spec))
    slc = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    truth = generate_service_corpus(spec, make_second_client(slc), Path(args.out),
                                    model_name=slc.model, lab=slc.lab)
    print(json.dumps({"out": str(args.out), "interactions": len(truth),
                      "planted": sum(1 for t in truth.values() if t)}))
    return 0
```

Add the parser in `main()` after the `generate-calibration` block:

```python
p_svc = sub.add_parser("generate-service-corpus",
                       help="generate the synthetic FS-shaped service corpus via the second lab (O1-only)")
p_svc.add_argument("--spec", required=True)
p_svc.add_argument("--out", required=True)
p_svc.set_defaults(fn=_cmd_generate_service)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_servicegen.py tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cix/cli.py tests/test_cli_servicegen.py
git commit -m "feat(cli): cix generate-service-corpus — second-lab generation of the rehearsal corpus"
```

---

### Task 4: Extract the `_detect()` helper from `_cmd_run` (behavior-preserving)

**Files:**
- Modify: `src/cix/cli.py:84-87`
- Test: existing `tests/test_run_e2e.py` + `tests/test_cli.py` (no new tests — the refactor is proven by existing e2e staying green)

- [ ] **Step 1: Add the helper**

In `src/cix/cli.py`, above `_cmd_run`:

```python
def _detect(store, units, rubric, client, chash, schema_version, model):
    """Pass-A detection (labels -> rubric hits -> rollup). The ONE detection code path,
    shared by `cix run` and `cix differential` (G5 rehearsal spec §2.3)."""
    la = label_corpus(store, units, client, chash, schema_version, model)
    ha = run_rubric(store, units, rubric, la, client, model)
    hits = store.hits_for(ha)
    return la, ha, hits, rollup(hits, eligible_interactions=len(units))
```

- [ ] **Step 2: Use it in `_cmd_run`**

Replace these four lines in `_cmd_run` (currently `cli.py:84-87`):

```python
    la = label_corpus(store, units, client, chash, schema_version, config.model)
    ha = run_rubric(store, units, rubric, la, client, config.model)
    hits = store.hits_for(ha)
    roll = rollup(hits, eligible_interactions=len(units))
```

with:

```python
    la, ha, hits, roll = _detect(store, units, rubric, client, chash, schema_version, config.model)
```

- [ ] **Step 3: Run the full suite to prove behavior preserved**

Run: `uv run pytest -q`
Expected: all green — especially `tests/test_run_e2e.py` (three e2e runs) untouched in behavior

- [ ] **Step 4: Commit**

```bash
git add src/cix/cli.py
git commit -m "refactor(cli): extract _detect() Pass-A helper — one detection path for run + differential"
```

---

### Task 5: `cix self-test` subcommand

**Files:**
- Modify: `src/cix/cli.py`
- Test: `tests/test_cli_selftest.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_cli_selftest.py`:

```python
import json
from pathlib import Path
from cix.cli import VOCAB_PATH, main
from cix.contracts import InteractionUnit
from cix.store import build_store, open_store

def _fake_run(tmp_path: Path, n: int = 60) -> Path:
    """Fabricate a minimal run dir: store + persisted label/hit artifacts + manifest."""
    run = tmp_path / "run"
    run.mkdir()
    units = [InteractionUnit.model_validate(
        {"id": f"i{i:03d}", "source_type": "transcript", "participants": ["agent", "customer"],
         "segments": [{"speaker": "agent", "text": f"routine contact number {i}"}]})
        for i in range(n)]
    build_store(units, VOCAB_PATH, run / "run.db")
    store = open_store(run / "run.db")
    la = store.ensure_label_artifact("chash-test", "1.0.0", "test-model", "ph-labels")
    for u in units:
        store.write_labels(la, u.id, {"motion": "service", "intent": "x",
                                      "driver_origin": "customer", "automatability": "rote",
                                      "outcome": "resolved", "handoff_events": ""})
    ha = store.ensure_hit_artifact(la, "1.0.0", "test-model", "ph-hits")
    # skewed occurrence hits so the distribution is non-degenerate
    for u in units[:20]:
        store.write_hit(ha, "manual_after_call_work", u.id, "occurrence", f"{u.id}:0000")
    for u in units[20:28]:
        store.write_hit(ha, "status_chase_inbound", u.id, "occurrence", f"{u.id}:0000")
    manifest = {"artifacts": {"labels": la, "hits": ha},
                "label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0",
                "corpus_hash": "chash-test", "scrub_salt": "cix-test"}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run

def test_selftest_emits_state_and_report(tmp_path, capsys):
    run = _fake_run(tmp_path)
    rc = main(["self-test", str(run),
               "--catalogue", "configs/catalogue_v0_1.yaml",
               "--rubric", "configs/service_rubric_v1.yaml"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] in ("material-advantage", "no-material-advantage", "not-evaluable")
    assert "band_movement" in out["layers_compared"]        # catalogue+rubric supplied
    report = json.loads((run / "selftest_report.json").read_text(encoding="utf-8"))
    assert report["state"] == out["state"]
    store = open_store(run / "run.db")
    rows = [v for v in store.validations() if v["check"] == "T-SST"]
    assert len(rows) == 1 and rows[0]["status"] == out["state"]

def test_selftest_not_evaluable_below_floor(tmp_path, capsys):
    run = _fake_run(tmp_path, n=10)                          # below min_evaluable_interactions=40
    rc = main(["self-test", str(run)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] == "not-evaluable"

def test_selftest_refuses_without_manifest(tmp_path, capsys):
    (tmp_path / "empty").mkdir()
    rc = main(["self-test", str(tmp_path / "empty")])
    assert rc == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_selftest.py -v`
Expected: FAIL — argparse `invalid choice: 'self-test'`

- [ ] **Step 3: Implement the subcommand**

In `src/cix/cli.py`, add to imports:

```python
from cix.selftest import load_selftest_spec, self_test
```

Add after `_cmd_calibrate`:

```python
def _cmd_selftest(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir} (is this a cix run output dir?)", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in manifest:
        print("error: run manifest has no 'artifacts' key — re-run with the current cix version", file=sys.stderr)
        return 2
    spec = load_selftest_spec(Path(args.spec))
    store = open_store(run_dir / "run.db")
    hits = store.hits_for(manifest["artifacts"]["hits"])
    all_ids = store.labeled_interactions(manifest["artifacts"]["labels"])
    catalogue = crosswalk = None
    if args.catalogue and args.rubric:
        catalogue = load_catalogue(Path(args.catalogue))
        rubric = load_rubric(Path(args.rubric), manifest["label_schema_version"],
                             manifest["tag_vocab_version"])
        crosswalk = {i.id: i.swap_ref for i in rubric.items}
    res = self_test(all_ids, hits, spec, catalogue=catalogue, crosswalk=crosswalk)
    store.write_validation("T-SST", None, res["state"],
                           f"material_fraction={res['material_fraction']} "
                           f"layers={','.join(res['layers_compared'])} spec={spec.version} "
                           "outcome_level=O1-synthetic-until-real-corpus")
    report = {"spec_version": spec.version, **res}
    (run_dir / "selftest_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"state": res["state"], "material_fraction": res["material_fraction"],
                      "layers_compared": res["layers_compared"],
                      "report": str(run_dir / "selftest_report.json")}))
    return 0
```

Add the parser in `main()`:

```python
p_st = sub.add_parser("self-test", help="full-vs-10% self-test (§7, R-VAL-5) over a completed run")
p_st.add_argument("run")
p_st.add_argument("--spec", default="configs/selftest_spec_v1.yaml")
p_st.add_argument("--catalogue", default=None, help="enables the band_movement layer (with --rubric)")
p_st.add_argument("--rubric", default=None, help="supplies the swap_ref crosswalk for band_movement")
p_st.set_defaults(fn=_cmd_selftest)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_selftest.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Run the full suite, then commit**

Run: `uv run pytest -q` — expected all green.

```bash
git add src/cix/cli.py tests/test_cli_selftest.py
git commit -m "feat(cli): cix self-test — §7 harness over a persisted run, T-SST row + report"
```

---

### Task 6: Differential design v1.0.1 — machine-readable targets → **CHECKPOINT (PO ratification)**

**Files:**
- Modify: `configs/differential_design_v1.yaml`

- [ ] **Step 1: Amend the design file**

Replace the full contents of `configs/differential_design_v1.yaml` with:

```yaml
# Differential variant design (R-VAL-7). Predeclares the perturbations, expected deltas, and
# per-variant tolerances. Variants are CONSTRUCTED from the scrubbed FS corpus at G5 (follow-on);
# this design + T-DIFF freeze at G4 before any variant run.
# PO-RATIFIED: 2026-08-02 (Checkpoint B — T-DIFF frozen)
# v1.0.1 (2026-08-03, G5-rehearsal): MACHINE-READABILITY AMENDMENT ONLY (R-VAL-6 versioned
# register change). Adds target_item + selection params per variant so `cix differential`
# constructs variants without interpreting prose. Tolerances, perturbations, and
# expected-delta semantics are UNCHANGED from the 1.0.0 freeze. PO-RATIFIED: 2026-08-03.
version: "1.0.1"
variants:
  - id: V1-delete
    perturbation: delete_subset
    target: "a known-labeled subset of repeat_contact_unresolved interactions"
    target_item: repeat_contact_unresolved
    delete_count: 3                  # up to 3 known-labeled interactions (fewer if fewer flagged)
    expected_delta: "the repeat_contact_unresolved count drops by the deleted magnitude"
    tolerance: 0.20
  - id: V2-duplicate
    perturbation: duplicate_chains
    target: "an identified repeat-contact thread"
    target_item: repeat_contact_unresolved
    thread_selection: most_target_hits   # the thread contributing the most target-item count
    expected_delta: "chain/interaction counts for that thread rise by the duplicated magnitude"
    tolerance: 0.20
  - id: V3-splice
    perturbation: splice_instances
    target: "N donor deterministic_request interactions"
    target_item: deterministic_request
    splice_copies: 5
    expected_delta: "the deterministic_request count rises by N"
    tolerance: 0.20
```

- [ ] **Step 2: Verify no frozen number moved**

Run: `git diff configs/differential_design_v1.yaml`
Confirm by eye: every `tolerance: 0.20`, every `perturbation`, every `expected_delta` line unchanged; only comments, `version`, and the new machine fields differ. Also confirm `configs/thresholds_v1.yaml` is untouched (`git status`).

- [ ] **Step 3: CHECKPOINT — present the diff to the PO and get explicit ratification**

Hard stop. Show the diff; PO confirms "ratified". Do not proceed to commit without it. (Spec exit criterion 2a.)

- [ ] **Step 4: Run the full suite (nothing reads this file yet — must stay green)**

Run: `uv run pytest -q`
Expected: all green

- [ ] **Step 5: Commit**

```bash
git add configs/differential_design_v1.yaml
git commit -m "docs(config): differential design v1.0.1 — machine-readable targets, PO-ratified; frozen values unchanged"
```

---

### Task 7: `cix differential` subcommand

**Files:**
- Modify: `src/cix/cli.py`
- Test: `tests/test_cli_differential.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_cli_differential.py`:

```python
import json
import re
from pathlib import Path
from cix.cli import VOCAB_PATH, main
from cix.manifest import corpus_hash
from cix.normalize import load_corpus
from cix.scrub import load_privacy_protocol, scrub_corpus
from cix.store import build_store, open_store

REPEAT_TEXT = "still chasing the same unfixed problem from before"
DETERM_TEXT = "just need the account password reset"

class DetectorClient:
    """Deterministic scripted detector: labels are constant; a rubric hit fires iff the
    trigger text appears in the interaction body AND the item is listed in the prompt."""
    LABELS = json.dumps({"motion": "service", "intent": "x", "driver_origin": "customer",
                         "automatability": "rote", "outcome": "resolved", "handoff_events": []})
    def complete(self, prompt: str) -> str:
        if prompt.startswith("You are labeling"):
            return self.LABELS
        uid = re.search(r"<interaction id=([^>]+)>", prompt).group(1)
        hits = []
        if REPEAT_TEXT in prompt and "- repeat_contact_unresolved:" in prompt:
            hits.append({"item_id": "repeat_contact_unresolved", "snippet_ids": f"{uid}:0000"})
        if DETERM_TEXT in prompt and "- deterministic_request:" in prompt:
            hits.append({"item_id": "deterministic_request", "snippet_ids": f"{uid}:0000"})
        return json.dumps({"hits": hits})

def _unit(uid, text, thread=None):
    doc = {"id": uid, "source_type": "transcript", "participants": ["agent", "customer"],
           "segments": [{"speaker": "customer", "text": text}]}
    if thread:
        doc["thread_id"] = thread
    return doc

def _write_corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    docs = [
        _unit("s000", "opening a ticket about a stalled import", thread="TH1"),
        _unit("s001", REPEAT_TEXT + ", the import is stalled again", thread="TH1"),
        _unit("s002", REPEAT_TEXT + ", third week running", thread="TH1"),
        _unit("s003", DETERM_TEXT + " for the finance login"),
        _unit("s004", DETERM_TEXT + " for a new hire"),
        _unit("s005", DETERM_TEXT + " after a lockout"),
    ] + [_unit(f"s{i:03d}", "routine plan question, handled cleanly") for i in range(6, 12)]
    for d in docs:
        (corpus / f"{d['id']}.json").write_text(json.dumps(d), encoding="utf-8")
    return corpus

def _base_run(tmp_path: Path, corpus_dir: Path) -> Path:
    """Fabricate the base run the way `cix run` would persist it: scrubbed units, store,
    label+hit artifacts via the real _detect path with the scripted detector."""
    import cix.cli as cli
    from cix.rubric import load_rubric
    run = tmp_path / "base-run"
    run.mkdir()
    units = load_corpus(corpus_dir)
    proto = load_privacy_protocol(Path("configs/privacy_protocol_v1.yaml"))
    salt = "cix-test"
    units, _ = scrub_corpus(units, proto, salt=salt)
    build_store(units, VOCAB_PATH, run / "run.db")
    store = open_store(run / "run.db")
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    chash = corpus_hash(units)
    la, ha, hits, roll = cli._detect(store, units, rubric, DetectorClient(), chash, "1.0.0", "test-model")
    manifest = {"artifacts": {"labels": la, "hits": ha}, "corpus_hash": chash,
                "scrub_salt": salt, "label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0"}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run

def test_differential_constructs_reruns_and_scores(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: DetectorClient())
    corpus = _write_corpus(tmp_path)
    run = _base_run(tmp_path, corpus)
    rc = main(["differential", str(run), "--corpus", str(corpus),
               "--rubric", "configs/service_rubric_v1.yaml"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["variants"] == 3 and out["failing"] == 0
    report = json.loads((run / "differential_report.json").read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in report["variants"]}
    # V1: 2 flagged repeat interactions exist; delete_count=3 caps at 2 -> expected -2, observed -2
    assert rows["V1-delete"]["expected"] == 2 and rows["V1-delete"]["observed"] == 2
    # V2: thread TH1 contributes 2 target interactions; duplicate -> +2 (copies carry same text)
    assert rows["V2-duplicate"]["expected"] == 2 and rows["V2-duplicate"]["observed"] == 2
    # V3: donor contributes 1; 5 copies -> +5
    assert rows["V3-splice"]["expected"] == 5 and rows["V3-splice"]["observed"] == 5
    store = open_store(run / "run.db")
    tdiff = [v for v in store.validations() if v["check"] == "T-DIFF"]
    assert len(tdiff) == 3 and all(v["status"] == "pass" for v in tdiff)
    # per-variant stores exist (real re-detection, not recounting)
    for vid in ("V1-delete", "V2-duplicate", "V3-splice"):
        assert (run / "differential" / vid / "run.db").exists()

def test_differential_refuses_on_corpus_mismatch(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: DetectorClient())
    corpus = _write_corpus(tmp_path)
    run = _base_run(tmp_path, corpus)
    # tamper: add one interaction after the base run -> corpus_hash mismatch
    (corpus / "s999.json").write_text(json.dumps(_unit("s999", "late addition")), encoding="utf-8")
    rc = main(["differential", str(run), "--corpus", str(corpus),
               "--rubric", "configs/service_rubric_v1.yaml"])
    assert rc == 2
    assert "corpus_hash mismatch" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli_differential.py -v`
Expected: FAIL — argparse `invalid choice: 'differential'`

- [ ] **Step 3: Implement the subcommand**

In `src/cix/cli.py`, add to imports:

```python
from cix.differential import delete_subset, duplicate_chains, splice_instances, score_delta
```

Add after `_cmd_selftest`:

```python
def _target_contribution(t_hits: list[dict], unit_basis: str, interaction_ids: set[str]) -> int:
    """Count the target-item contribution of a set of interactions, respecting the item's
    unit_of_count (interaction: distinct flagged interactions; occurrence: hit rows)."""
    if unit_basis == "interaction":
        return len({h["interaction_id"] for h in t_hits} & interaction_ids)
    return sum(1 for h in t_hits if h["interaction_id"] in interaction_ids)

def _cmd_differential(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir} (is this a cix run output dir?)", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in manifest:
        print("error: run manifest has no 'artifacts' key — re-run with the current cix version", file=sys.stderr)
        return 2
    try:
        units = load_corpus(Path(args.corpus))
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    # Reload + integrity check (rehearsal spec §3.3 step 0): re-scrub with the persisted
    # salt, refuse unless the recomputed hash matches the base run's manifest.
    proto = load_privacy_protocol(Path("configs/privacy_protocol_v1.yaml"))
    units, _ = scrub_corpus(units, proto, salt=manifest["scrub_salt"])
    if manifest_corpus_hash(units) != manifest["corpus_hash"]:
        print("refused: corpus_hash mismatch — --corpus is not the corpus the base run saw", file=sys.stderr)
        return 2
    store = open_store(run_dir / "run.db")
    base_hits = store.hits_for(manifest["artifacts"]["hits"])
    design = yaml.safe_load(Path(args.design).read_text(encoding="utf-8"))
    rubric = load_rubric(Path(args.rubric), manifest["label_schema_version"],
                         manifest["tag_vocab_version"])
    unit_basis_of = {i.id: i.unit_of_count for i in rubric.items}
    config = load_run_config(Path("configs/run_config_v1.yaml"))
    client = make_client(config)
    base_roll = rollup(base_hits, eligible_interactions=len(units))
    rows = []
    for v in design["variants"]:
        item = v["target_item"]
        unit_basis = unit_basis_of[item]
        base_count = base_roll["items"].get(item, {}).get("count", 0)
        t_hits = [h for h in base_hits if h["item_id"] == item]
        flagged = sorted({h["interaction_id"] for h in t_hits})
        if not flagged:
            store.write_validation("T-DIFF", v["id"], "not_run",
                                   f"no {item} hits in the base run — variant not constructible")
            rows.append({"id": v["id"], "status": "not_run", "expected": None, "observed": None})
            continue
        if v["perturbation"] == "delete_subset":
            ids = set(flagged[:v["delete_count"]])
            variant_units, _meta = delete_subset(units, ids)
            expected = _target_contribution(t_hits, unit_basis, ids)      # count drops by this
        elif v["perturbation"] == "duplicate_chains":
            tid_of = {u.id: u.thread_id for u in units}
            per_thread: dict[str, set[str]] = {}
            for h in t_hits:
                tid = tid_of.get(h["interaction_id"])
                if tid:
                    per_thread.setdefault(tid, set()).add(h["interaction_id"])
            if not per_thread:
                store.write_validation("T-DIFF", v["id"], "not_run",
                                       f"no {item} hits inside any thread — variant not constructible")
                rows.append({"id": v["id"], "status": "not_run", "expected": None, "observed": None})
                continue
            thread_id = max(sorted(per_thread), key=lambda t: len(per_thread[t]))
            member_ids = {u.id for u in units if u.thread_id == thread_id}
            variant_units, _meta = duplicate_chains(units, thread_id)
            expected = _target_contribution(t_hits, unit_basis, member_ids)  # count rises by this
        elif v["perturbation"] == "splice_instances":
            per_donor = {uid: _target_contribution(t_hits, unit_basis, {uid}) for uid in flagged}
            donor_id = max(sorted(per_donor), key=lambda u: per_donor[u])
            donor = next(u for u in units if u.id == donor_id)
            variant_units, _meta = splice_instances(units, donor, v["splice_copies"])
            expected = per_donor[donor_id] * v["splice_copies"]           # count rises by this
        else:
            print(f"error: unknown perturbation {v['perturbation']!r} in design", file=sys.stderr)
            return 2
        vdir = run_dir / "differential" / v["id"]
        vdir.mkdir(parents=True, exist_ok=True)
        build_store(variant_units, VOCAB_PATH, vdir / "run.db")
        vstore = open_store(vdir / "run.db")
        chash_v = manifest_corpus_hash(variant_units)
        _la, _ha, _vhits, vroll = _detect(vstore, variant_units, rubric, client,
                                          chash_v, manifest["label_schema_version"], config.model)
        variant_count = vroll["items"].get(item, {}).get("count", 0)
        observed = abs(variant_count - base_count)
        direction_ok = (variant_count < base_count) if v["perturbation"] == "delete_subset" \
            else (variant_count > base_count) if expected else (variant_count == base_count)
        res = score_delta({"count": expected}, {"count": observed}, v["tolerance"])
        if not direction_ok:
            res["status"] = "fail"
        detail = (f"{item} base={base_count} variant={variant_count} expected_delta={expected} "
                  f"rel_err={res['rel_error']} direction_ok={direction_ok} outcome_level=O1-synthetic")
        store.write_validation("T-DIFF", v["id"], res["status"], detail)
        rows.append({"id": v["id"], "status": res["status"], "expected": expected,
                     "observed": observed, "rel_error": res["rel_error"],
                     "tolerance": v["tolerance"], "detail": detail})
    report = {"design_version": design["version"], "variants": rows}
    (run_dir / "differential_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    failing = sum(1 for r in rows if r["status"] == "fail")
    print(json.dumps({"variants": len(rows), "failing": failing,
                      "report": str(run_dir / "differential_report.json")}))
    return 1 if failing else 0
```

Add the parser in `main()`:

```python
p_diff = sub.add_parser("differential",
                        help="construct the predeclared variants, re-run detection, score vs T-DIFF (R-VAL-7)")
p_diff.add_argument("run", help="base run dir (output of cix run)")
p_diff.add_argument("--corpus", required=True, help="the corpus dir the base run ingested")
p_diff.add_argument("--design", default="configs/differential_design_v1.yaml")
p_diff.add_argument("--rubric", required=True)
p_diff.set_defaults(fn=_cmd_differential)
```

Note: no `--catalogue` on `differential` — the differential tier reads counts, not prices. (Deviation from the spec §3.4 sample command line, which listed one; the spec's own §3.3 input inventory does not include it.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli_differential.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the full suite, then commit**

Run: `uv run pytest -q` — expected all green.

```bash
git add src/cix/cli.py tests/test_cli_differential.py
git commit -m "feat(cli): cix differential — construct frozen variants, re-run real detection, score vs T-DIFF"
```

---

### Task 8: The rehearsal run (live) → **CHECKPOINT (PO spend approval)**

**Files:**
- Create (by the pipeline): `runs/svc-corpus/`, `runs/svc-run/`

- [ ] **Step 1: CHECKPOINT — PO approves live spend**

Hard stop. Confirm with the PO: live keys available (Anthropic primary + second-lab), spend envelope **~$25–80** accepted (spec §1.1). Do not run without explicit go-ahead.

- [ ] **Step 2: Generate the service corpus (second lab, live)**

Run:
```bash
uv run cix generate-service-corpus --spec configs/service_corpus_spec_v1.yaml --out runs/svc-corpus
```
Expected stdout: `{"out": "runs/svc-corpus", "interactions": 100, "planted": 46}` (7 thread repeats + 39 singles). Spot-read 3 corpus files: service register, thread members reference the ongoing issue.

- [ ] **Step 3: Base run (primary lab, live)**

Run:
```bash
uv run cix run runs/svc-corpus/corpus --rubric configs/service_rubric_v1.yaml \
  --catalogue configs/catalogue_v0_1.yaml --out runs/svc-run \
  --clearance "synthetic service rehearsal corpus — O1 only, never O2/O3 (PRD §2.3)"
```
Expected: rc 0; report.json + report.pdf + manifest.json in `runs/svc-run`; the SECOND-LAB-SEAT validation row reads `recused_f4` (expected — the corpus is second-lab generated; spec §3.4 honest note).

- [ ] **Step 4: Self-test (offline arithmetic over the persisted run)**

Run:
```bash
uv run cix self-test runs/svc-run --catalogue configs/catalogue_v0_1.yaml --rubric configs/service_rubric_v1.yaml
```
Expected: rc 0; state is one of the three §7 states with `layers_compared` including `band_movement`; `runs/svc-run/selftest_report.json` written. Any state is a valid rehearsal outcome — record it, do not tune toward one.

- [ ] **Step 5: Differential (live — 3 variant re-detections)**

Run:
```bash
uv run cix differential runs/svc-run --corpus runs/svc-corpus/corpus --rubric configs/service_rubric_v1.yaml
```
Expected: rc 0 if all 3 variants track within tolerance 0.20. **If a variant fails:** this is diagnostic signal about detector stability on perturbed synthetic text, NOT an abandon-trigger input (triggers bind to the real corpus, §8) — record it honestly in the report and surface it to the PO; do not re-run to a pass.

- [ ] **Step 6: Commit the run artifacts**

```bash
git add runs/svc-corpus runs/svc-run
git commit -m "feat(g5-rehearsal): O1 rehearsal run — service corpus generated, base run, self-test + differential executed"
```

---

### Task 9: Exit doc pass

**Files:**
- Modify: `README.md`, `docs/superpowers/plans/ROADMAP.md`, `docs/superpowers/specs/2026-08-03-g5-rehearsal-design.md`

- [ ] **Step 1: Update the spec status header**

In `docs/superpowers/specs/2026-08-03-g5-rehearsal-design.md`, replace:

```markdown
**Status:** 📝 designed — not yet implemented · **Date:** 2026-08-03 · **Owner:** PO
```

with:

```markdown
**Status:** ✅ implemented — G5 rehearsal executed (O1), 2026-08-03 · **Date:** 2026-08-03 · **Owner:** PO
```

- [ ] **Step 2: Update the ROADMAP progress line**

In `docs/superpowers/plans/ROADMAP.md`, replace the trailing part of the **Progress:** line

```markdown
· ▶ **G5 next** (first real run), gated on the FS corpus (OD-1) + a thin scrub+ingest / differential-construction follow-on. Executed detail lives in `2026-08-02-g4-assembly.md`, the design spec, and the PRD changelog.
```

with:

```markdown
· ✅ **G5 rehearsal (2026-08-03; servicegen synthetic service corpus, cix self-test / cix differential CLI, end-to-end O1 dress run — the G4 follow-on's tooling half)** · ▶ **G5 next** (first real run), now gated ONLY on the FS corpus (OD-1). Executed detail lives in `2026-08-02-g4-assembly.md`, `2026-08-03-g5-rehearsal-design.md`, and the PRD changelog.
```

- [ ] **Step 3: Update the README status row and next action**

In `README.md`, in the Status table's **Build** row, append after "…(AC-16). **T-SST + T-DIFF frozen before any result** (R-VAL-6).":

```markdown
G5 rehearsal complete (2026-08-03): synthetic FS-shaped service corpus (servicegen), `cix self-test` + `cix differential` shipped, full G5 path executed end-to-end, O1-labeled.
```

And in **Next action**, replace "It is blocked on two things: the **FS corpus landing (OD-1)**, and a **thin follow-on carried over from G4** (real scrub+ingest, differential-variant construction on real language, and the `cix self-test` / `cix differential` CLI glue)." with:

```markdown
The G4 follow-on's tooling half is done (G5 rehearsal, 2026-08-03): `cix self-test` and `cix differential` are shipped and the whole G5 path has run end-to-end on a synthetic service corpus (O1-labeled). G5 is now blocked only on the **FS corpus landing (OD-1)**; when it lands, the remaining slice is real scrub+ingest and running the same commands on real language.
```

- [ ] **Step 4: Run the full suite one last time**

Run: `uv run pytest -q`
Expected: all green

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/plans/ROADMAP.md docs/superpowers/specs/2026-08-03-g5-rehearsal-design.md
git commit -m "docs(g5-rehearsal): mark rehearsal complete — G5 now blocked only on OD-1"
```

---

## Self-review checklist (for the executing agent, before opening the PR)

- **Spec coverage:** servicegen + spec (T1–2, spec §3.1 incl. coverage minimums), `generate-service-corpus` (T3), one detection path (T4, §2.3), `self-test` (T5, §3.2), design v1.0.1 + PO checkpoint (T6, §2.2/exit 2a), `differential` with reload + integrity check (T7, §3.3), rehearsal run (T8, §3.4 incl. F4 note + spend checkpoint), docs (T9, exit 5).
- **Honesty:** every rehearsal artifact carries O1 labeling (clearance string T8, `outcome_level` in T-SST/T-DIFF details); a failed variant or an unwanted self-test state is recorded, never tuned away.
- **Freeze discipline:** `configs/thresholds_v1.yaml` untouched; design v1.0.1 changes no tolerance/perturbation/expected-delta; T6 verifies by diff before the PO checkpoint.
- **Firewall:** servicegen never references rubric machinery (structural test), descriptions disjoint from A9 text (5-gram test), prompt-level check in T2.
- **Backward compatibility:** existing e2e (`test_run_e2e.py`, `test_cli.py`) green after the T4 refactor; calgen untouched.
- **Checkpoints:** T6 Step 3 (design ratification) and T8 Step 1 (spend) are hard stops — do not proceed on silence.
