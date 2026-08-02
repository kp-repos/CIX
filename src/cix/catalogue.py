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
