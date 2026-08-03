"""Swap catalogue (A5) load + Pass B join. Detector-side, priced-view code — never
suppresses Pass A detection (R-ARCH-2). Schema per CIX_Swap_Catalogue_v0.md §2."""
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel

class CatalogueEntry(BaseModel):
    id: str
    labour_unit: str
    signal: str
    substitute: str
    remedy_class: Literal["A", "B", "C", "D"]
    effort: str
    outcome: str
    unit_basis: str
    currency: str
    horizon: str
    per_unit_band: list[float]
    evidence_tier: Literal["confirmed", "candidate", "none"]
    inferred: bool
    source: str

class Catalogue(BaseModel):
    version: str
    effort_bands: list[str]
    outcome_bands: list[str]
    entries: list[CatalogueEntry]

    def by_id(self, swap_id: str) -> CatalogueEntry | None:
        return next((e for e in self.entries if e.id == swap_id), None)

def load_catalogue(path: Path) -> Catalogue:
    return Catalogue.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def join_swaps(roll_items: dict, crosswalk: dict[str, str | None], cat: "Catalogue") -> dict:
    """Join rollup items to catalogue entries by swap_ref. A unit-incompatible join drops
    THAT claim (R-CAT-3) — recorded in `dropped`, the rest still price; items with no
    swap_ref go on the 'no known remedy yet' shelf (R-CAT-4)."""
    priced, shelf, dropped = [], [], []
    for item_id, row in sorted(roll_items.items()):
        swap_id = crosswalk.get(item_id)
        entry = cat.by_id(swap_id) if swap_id else None
        if entry is None:
            shelf.append({"item_id": item_id, "count": row["count"], "unit": row["unit"]})
            continue
        if entry.unit_basis != row["unit"]:
            dropped.append({"item_id": item_id, "swap_ref": entry.id, "unit": row["unit"],
                            "swap_basis": entry.unit_basis,
                            "reason": f"unit '{row['unit']}' != swap {entry.id} basis '{entry.unit_basis}'"})
            continue
        priced.append({"item_id": item_id, "count": row["count"], "unit": row["unit"], "entry": entry})
    shelf.sort(key=lambda s: (-s["count"], s["item_id"]))
    return {"priced": priced, "shelf": shelf, "dropped": dropped}

def leverage_grid(priced: list[dict], cat: Catalogue) -> dict:
    """Effort-band x outcome-band grid; count tie-break within tier; Class D named in its
    corner; remedy-less items are on the shelf, not here (R-CAT-4)."""
    eff_rank = {b: i for i, b in enumerate(cat.effort_bands)}          # low=0 best
    out_rank = {b: i for i, b in enumerate(cat.outcome_bands)}         # large=highest
    def score(j):
        e = j["entry"]
        # higher outcome and lower effort rank first; count breaks ties
        return (-out_rank[e.outcome], eff_rank[e.effort], -j["count"], j["item_id"])
    ordered = sorted(priced, key=score)
    cells = [{"item_id": j["item_id"], "effort": j["entry"].effort, "outcome": j["entry"].outcome,
              "count": j["count"], "remedy_class": j["entry"].remedy_class} for j in ordered]
    class_d = [c for c in cells if c["remedy_class"] == "D"]
    return {"cells": cells, "class_d": class_d}
