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
    distribution_tv_max: float

def load_selftest_spec(path: Path) -> SelfTestSpec:
    return SelfTestSpec.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

import random
from cix.aggregate import rollup

def sample_ids(ids: list[str], fraction: float, seed: int) -> list[str]:
    """Deterministic 10% sample of interaction ids (§7.3)."""
    ordered = sorted(ids)
    k = max(1, round(len(ordered) * fraction))
    return sorted(random.Random(seed).sample(ordered, k))

def _sample_hits(hits: list[dict], sample: set[str]) -> list[dict]:
    return [h for h in hits if h["interaction_id"] in sample]

def _ordered_topk(roll: dict, k: int) -> list[str]:
    """rank_topk layer: ordered top-k across units (drives leverage-grid ordering)."""
    ranked = []
    for unit, pairs in sorted(roll["rank_by_unit"].items()):
        ranked.extend(item_id for item_id, _ in pairs)
    return ranked[:k]

def _highlight_set(roll: dict, k: int) -> frozenset:
    """highlight_diff layer: membership of the top-k headline items (order-independent)."""
    ranked = sorted(roll["items"].items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    return frozenset(item_id for item_id, _ in ranked[:k])

def _shares(roll: dict) -> dict:
    total = sum(r["count"] for r in roll["items"].values())
    return {k: r["count"] / total for k, r in roll["items"].items()} if total else {}

def _tv_distance(p: dict, q: dict) -> float:
    """Total-variation distance between two item count-share distributions."""
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)

def _priced_topk(roll: dict, k: int, catalogue, crosswalk: dict) -> list[str]:
    """band_movement layer: priced items ranked by band midpoint (count x mean per-unit band).
    Class-D and unit-incompatible items are excluded (they are never priced)."""
    ranked = []
    for item_id, r in roll["items"].items():
        swap = crosswalk.get(item_id)
        entry = catalogue.by_id(swap) if swap else None
        if entry is None or entry.remedy_class == "D" or entry.unit_basis != r["unit"]:
            continue
        mid = r["count"] * (entry.per_unit_band[0] + entry.per_unit_band[1]) / 2
        ranked.append((item_id, mid))
    ranked.sort(key=lambda t: (-t[1], t[0]))
    return [item_id for item_id, _ in ranked[:k]]

def self_test(all_ids: list[str], hits: list[dict], spec: SelfTestSpec,
              catalogue=None, crosswalk: dict | None = None) -> dict:
    """§7 harness. For each seed's 10% sample (regenerated from sample records only), compares
    the full corpus across four decision-relevant layers: distribution distance, top-k rank,
    highlighted-action set, and opportunity-band movement. A seed is 'material' if ANY applicable
    layer differs; state = material-advantage when the material-seed fraction meets the threshold.
    band_movement is compared only when a catalogue + crosswalk are supplied (the real run has one)."""
    n = len(all_ids)
    if n < spec.min_evaluable_interactions:
        return {"state": "not-evaluable", "reason": f"{n} < {spec.min_evaluable_interactions}",
                "material_fraction": None, "per_seed": [], "per_layer_fraction": {},
                "layers_compared": []}
    has_band = catalogue is not None and crosswalk is not None
    layers = ["distribution", "rank_topk", "highlight_diff"] + (["band_movement"] if has_band else [])
    full = rollup(hits, eligible_interactions=n)
    full_shares = _shares(full)
    full_topk = _ordered_topk(full, spec.topk)
    full_high = _highlight_set(full, spec.topk)
    full_band = _priced_topk(full, spec.topk, catalogue, crosswalk) if has_band else None
    per_seed = []
    for seed in spec.seeds:
        sample = set(sample_ids(all_ids, spec.sample_fraction, seed))
        sroll = rollup(_sample_hits(hits, sample), eligible_interactions=len(sample))
        layer_mat = {
            "distribution": _tv_distance(full_shares, _shares(sroll)) > spec.distribution_tv_max,
            "rank_topk": _ordered_topk(sroll, spec.topk) != full_topk,
            "highlight_diff": _highlight_set(sroll, spec.topk) != full_high,
        }
        if has_band:
            layer_mat["band_movement"] = _priced_topk(sroll, spec.topk, catalogue, crosswalk) != full_band
        material = any(layer_mat[l] for l in layers)
        per_seed.append({"seed": seed, "material": material, "layers": layer_mat})
    per_layer_fraction = {l: round(sum(1 for s in per_seed if s["layers"][l]) / len(per_seed), 3)
                          for l in layers}
    frac = sum(1 for s in per_seed if s["material"]) / len(per_seed)
    state = "material-advantage" if frac >= spec.material_seed_fraction else "no-material-advantage"
    return {"state": state, "material_fraction": round(frac, 3), "per_seed": per_seed,
            "per_layer_fraction": per_layer_fraction, "layers_compared": layers,
            "full_topk": full_topk}
