from pathlib import Path
import yaml
from pydantic import BaseModel

class RunConfig(BaseModel):
    version: str
    model: str
    temperature: float
    max_tokens: int
    seed: int

def load_run_config(path: Path) -> RunConfig:
    return RunConfig.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

def load_thresholds(path: Path) -> dict:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return doc["registers"]
