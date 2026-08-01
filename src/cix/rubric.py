from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel

class DependencyError(Exception):
    pass

class RubricItem(BaseModel):
    id: str
    description: str
    polarity: Literal["positive", "negative"]
    unit_of_count: Literal["occurrence", "interaction", "account", "time-estimate", "chain"]
    prefilter: dict | None = None
    criterion: str
    exemplars: list[str] = []

class Rubric(BaseModel):
    version: str
    requires: dict
    items: list[RubricItem]

def load_rubric(path: Path, label_schema_version: str, tag_vocab_version: str) -> Rubric:
    r = Rubric.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    want_schema = r.requires["label_schema_version"]
    want_vocab = r.requires["tag_vocab_version"]
    if want_schema != label_schema_version:
        raise DependencyError(f"rubric requires label_schema {want_schema}, loaded {label_schema_version}")
    if want_vocab != tag_vocab_version:
        raise DependencyError(f"rubric requires tag_vocab {want_vocab}, loaded {tag_vocab_version}")
    return r
