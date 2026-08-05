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
