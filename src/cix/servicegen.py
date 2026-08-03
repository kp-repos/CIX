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
