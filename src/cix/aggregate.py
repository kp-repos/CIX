from collections import defaultdict

class UnitMixError(Exception):
    pass

def rollup(hits: list[dict], eligible_interactions: int) -> dict:
    """Corpus statistics from persisted hits. Shares only within a unit; every share names
    its denominator (R-RUB-3 / AC-9). Interaction coverage per the ratified scheme (R-VAL-4)."""
    items: dict[str, dict] = {}
    unit_of: dict[str, str] = {}
    counts: dict[str, int] = defaultdict(int)
    covered: set[str] = set()
    for h in hits:
        if h["item_id"] in unit_of and unit_of[h["item_id"]] != h["unit"]:
            raise UnitMixError(f"{h['item_id']} appears with two units")
        unit_of[h["item_id"]] = h["unit"]
        counts[h["item_id"]] += 1
        covered.add(h["interaction_id"])
    for item_id, count in counts.items():
        unit = unit_of[item_id]
        share = None
        denominator = None
        if unit == "interaction" and eligible_interactions > 0:
            share = round(count / eligible_interactions, 4)
            denominator = f"{eligible_interactions} eligible interactions"
        items[item_id] = {"unit": unit, "count": count, "share": share, "denominator": denominator}
    rank_by_unit: dict[str, list] = defaultdict(list)
    for item_id, row in items.items():
        rank_by_unit[row["unit"]].append((item_id, row["count"]))
    for unit in rank_by_unit:
        rank_by_unit[unit].sort(key=lambda t: (-t[1], t[0]))
    return {
        "items": items,
        "rank_by_unit": dict(rank_by_unit),
        "interaction_coverage": round(len(covered) / eligible_interactions, 4) if eligible_interactions else None,
        "residual_interactions": eligible_interactions - len(covered),
        "eligible_interactions": eligible_interactions,
    }
