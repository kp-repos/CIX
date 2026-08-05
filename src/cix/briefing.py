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
