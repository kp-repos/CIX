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
