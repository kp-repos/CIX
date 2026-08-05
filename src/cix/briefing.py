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
