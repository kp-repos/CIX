"""Calibration corpus generator (A7). COLLUSION FIREWALL: this module must never
reference the detection side's judgment machinery — it consumes pathology descriptions
from the A7 spec and nothing else (R-VAL-2; enforced by tests/test_calspec.py)."""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
import yaml
from pydantic import BaseModel
from cix.contracts import InteractionUnit
from cix.model import ModelClient, complete_json

GEN_PROMPT_VERSION = "1.0.0"

_GEN_PROMPT = """You are writing one synthetic B2B sales interaction for a measurement-calibration corpus.

Follow this style guide strictly:
{style}

Interaction form: {source_type} between {participants}, 6-14 turns.

{block}

Return ONLY JSON: {{"segments": [{{"speaker": "...", "text": "..."}}]}}
Every segment is one speaker turn. Plausible, mundane, specific business detail. No meta-commentary, no labels, no explanations.
"""

_PLANT_BLOCK = """Embed the following workplace pathology exactly {n} distinct time(s), at "{loudness}" salience:
{description}
Salience meanings — loud: stated explicitly and dwelt on; moderate: plainly present once, not emphasized; camouflaged: implied indirectly, never named, visible only by inference. Everything else in the interaction is routine and healthy."""

_CLEAN_BLOCK = "This interaction is routine and competent: no notable workplace pathology of any kind."

_NULL_BLOCK = """This interaction must contain ZERO instances of any of the following pathologies. Write a plausible, healthy interaction; near-misses are fine, actual instances are not:
{descriptions}"""

def gen_prompts_hash() -> str:
    joined = _GEN_PROMPT + _PLANT_BLOCK + _CLEAN_BLOCK + _NULL_BLOCK + GEN_PROMPT_VERSION
    return hashlib.sha256(joined.encode()).hexdigest()[:16]

class Pathology(BaseModel):
    key: str
    maps_to_item: str            # item id only — never item text (firewall holds)
    description: str
    embeds_per_interaction: list[int]
    source_type: str = "transcript"
    participants: list[str] = ["rep", "customer"]

class SplitSpec(BaseModel):
    id_prefix: str
    seed: int
    instances_per_cell: int = 0
    clean_interactions: int = 0
    interactions: int = 0        # null split only

class CalSpec(BaseModel):
    version: str
    loudness_levels: list[str]
    style_guide: str
    pathologies: list[Pathology]
    splits: dict[str, SplitSpec]

def load_cal_spec(path: Path) -> CalSpec:
    return CalSpec.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

def build_slots(spec: CalSpec, split_name: str) -> list[dict]:
    """Deterministic slot assignment per split seed (sample reproducibility, R-IDX-6)."""
    sp = spec.splits[split_name]
    if split_name == "null":
        return [{"kind": "null"} for _ in range(sp.interactions)]
    slots, k = [], 0
    for p in spec.pathologies:
        for lvl in spec.loudness_levels:
            for _ in range(sp.instances_per_cell):
                n = p.embeds_per_interaction[k % len(p.embeds_per_interaction)]
                slots.append({"kind": "plant", "pathology": p, "loudness": lvl, "n": n})
                k += 1
    slots += [{"kind": "clean"} for _ in range(sp.clean_interactions)]
    random.Random(sp.seed).shuffle(slots)
    return slots

def _prompt_for(spec: CalSpec, slot: dict) -> tuple[str, str, list[str]]:
    if slot["kind"] == "plant":
        p: Pathology = slot["pathology"]
        block = _PLANT_BLOCK.format(n=slot["n"], loudness=slot["loudness"], description=p.description.strip())
        st, parts = p.source_type, p.participants
    elif slot["kind"] == "null":
        descs = "\n".join(f"- {p.description.strip()}" for p in spec.pathologies)
        block, st, parts = _NULL_BLOCK.format(descriptions=descs), "transcript", ["rep", "customer"]
    else:
        block, st, parts = _CLEAN_BLOCK, "transcript", ["rep", "customer"]
    return _GEN_PROMPT.format(style=spec.style_guide.strip(), source_type=st,
                              participants=" and ".join(parts), block=block), st, parts

def generate_corpus(spec: CalSpec, split_name: str, client: ModelClient,
                    out_dir: Path, model_name: str, lab: str) -> dict:
    corpus_dir = Path(out_dir) / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    truth: dict = {}
    for i, slot in enumerate(build_slots(spec, split_name)):
        uid = f"{spec.splits[split_name].id_prefix}-{i:03d}"
        prompt, st, parts = _prompt_for(spec, slot)
        out = complete_json(client, prompt)
        unit = InteractionUnit.model_validate(
            {"id": uid, "source_type": st, "participants": parts, "segments": out["segments"]})
        (corpus_dir / f"{uid}.json").write_text(unit.model_dump_json(indent=2), encoding="utf-8")
        truth[uid] = ({"pathology": slot["pathology"].key, "loudness": slot["loudness"],
                       "expected_occurrences": slot["n"]} if slot["kind"] == "plant" else None)
    (Path(out_dir) / "truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    (Path(out_dir) / "provenance.yaml").write_text(yaml.safe_dump({
        "generator_lab": lab, "generator_model": model_name,
        "gen_prompt_version": GEN_PROMPT_VERSION, "gen_prompts_hash": gen_prompts_hash(),
        "spec_version": spec.version, "split": split_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }), encoding="utf-8")
    return truth
