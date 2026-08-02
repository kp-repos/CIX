"""Priced view assembly (R-PRC-1). Indicative opportunity bands only: each names its
count unit, currency, horizon, per-unit basis, source, inferred/observed, evidence tier.
No portfolio totals; a finding joined to multiple remedies is shown as alternatives,
never summed."""
from collections import defaultdict

def _alt(count: int, entry) -> dict:
    lo, hi = entry.per_unit_band
    return {"swap_ref": entry.id, "substitute": entry.substitute, "remedy_class": entry.remedy_class,
            "band": {"low": count * lo, "high": count * hi}, "currency": entry.currency,
            "horizon": entry.horizon, "per_unit_band": entry.per_unit_band,
            "evidence_tier": entry.evidence_tier, "inferred": entry.inferred, "source": entry.source}

def priced_view(priced: list[dict]) -> dict:
    by_item: dict[str, list[dict]] = defaultdict(list)
    unit_of: dict[str, str] = {}
    count_of: dict[str, int] = {}
    for j in priced:
        # Class D ("not ours") is named in the leverage grid's Class-D corner, never shown as a
        # dollar band in the priced view (R-CAT-4/5). Skip it here.
        if j["entry"].remedy_class == "D":
            continue
        by_item[j["item_id"]].append(j["entry"])
        unit_of[j["item_id"]] = j["unit"]
        count_of[j["item_id"]] = j["count"]
    plays = []
    for item_id in sorted(by_item):
        alts = [_alt(count_of[item_id], e) for e in by_item[item_id]]
        primary = alts[0]
        plays.append({"item_id": item_id, "unit": unit_of[item_id], "count": count_of[item_id],
                      "band": primary["band"], "currency": primary["currency"],
                      "horizon": primary["horizon"], "evidence_tier": primary["evidence_tier"],
                      "inferred": primary["inferred"], "source": primary["source"],
                      "alternatives": alts})
    return {"plays": plays, "note": None}
