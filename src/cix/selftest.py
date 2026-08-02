"""Full-vs-10% self-test harness (§7, R-VAL-5). Reads persisted hits/rollup; regenerates
sample aggregation from sample records only (no full-corpus leakage). Emits one of
material-advantage / no-material-advantage / not-evaluable."""
from pathlib import Path
import yaml
from pydantic import BaseModel

class SelfTestSpec(BaseModel):
    version: str
    sample_fraction: float
    seeds: list[int]
    min_evaluable_interactions: int
    material_seed_fraction: float
    layers: list[str]
    topk: int

def load_selftest_spec(path: Path) -> SelfTestSpec:
    return SelfTestSpec.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

import random
from cix.aggregate import rollup

def sample_ids(ids: list[str], fraction: float, seed: int) -> list[str]:
    """Deterministic 10% sample of interaction ids (§7.3)."""
    ordered = sorted(ids)
    k = max(1, round(len(ordered) * fraction))
    return sorted(random.Random(seed).sample(ordered, k))

def _topk(roll: dict, k: int) -> list[str]:
    ranked = []
    for unit, pairs in sorted(roll["rank_by_unit"].items()):
        ranked.extend(item_id for item_id, _ in pairs)
    return ranked[:k]

def _sample_hits(hits: list[dict], sample: set[str]) -> list[dict]:
    return [h for h in hits if h["interaction_id"] in sample]

def self_test(all_ids: list[str], hits: list[dict], spec: SelfTestSpec) -> dict:
    """§7 harness. Compares full-corpus outputs to each seed's 10% sample, from sample records
    only. Returns state + the fraction of seeds showing a material (top-k) difference."""
    n = len(all_ids)
    if n < spec.min_evaluable_interactions:
        return {"state": "not-evaluable", "reason": f"{n} < {spec.min_evaluable_interactions}",
                "material_fraction": None, "per_seed": []}
    full = rollup(hits, eligible_interactions=n)
    full_top = _topk(full, spec.topk)
    per_seed = []
    for seed in spec.seeds:
        sample = set(sample_ids(all_ids, spec.sample_fraction, seed))
        sroll = rollup(_sample_hits(hits, sample), eligible_interactions=len(sample))
        sample_top = _topk(sroll, spec.topk)
        material = sample_top != full_top
        per_seed.append({"seed": seed, "material": material,
                         "full_topk": full_top, "sample_topk": sample_top})
    frac = sum(1 for s in per_seed if s["material"]) / len(per_seed)
    state = "material-advantage" if frac >= spec.material_seed_fraction else "no-material-advantage"
    return {"state": state, "material_fraction": round(frac, 3), "per_seed": per_seed,
            "full_topk": full_top}
