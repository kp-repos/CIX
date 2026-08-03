from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel

class DependencyError(Exception):
    pass

class ParaphraseError(Exception):
    pass

class RubricItem(BaseModel):
    id: str
    description: str
    polarity: Literal["positive", "negative"]
    unit_of_count: Literal["occurrence", "interaction", "account", "time-estimate", "chain"]
    prefilter: dict | None = None
    criterion: str
    exemplars: list[str] = []
    swap_ref: str | None = None      # R-RUB-1: nullable crosswalk into the swap catalogue

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

def load_paraphrase_set(rubric_path: Path, rubric_version: str) -> dict[str, str]:
    """Select the frozen T-PARA paraphrase set for a rubric, from `paraphrases*.yaml`
    beside the rubric. A doc is a candidate when its `rubric_version` matches AND it is
    not bound to a different rubric (`rubric_file` absent, or equal to the rubric's
    filename). Binding by filename gives each instrument an identity beyond its version
    string, which two rubrics can share. Exactly one candidate -> its paraphrases; none
    -> {} (caller emits the honest T-PARA not_run); more than one -> ParaphraseError, so
    ambiguity never silently picks the wrong instrument."""
    rubric_path = Path(rubric_path)
    candidates = []
    for p in sorted(rubric_path.parent.glob("paraphrases*.yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if doc.get("rubric_version") != rubric_version:
            continue
        bound = doc.get("rubric_file")
        if bound is not None and bound != rubric_path.name:
            continue
        candidates.append((p, doc))
    if not candidates:
        return {}
    if len(candidates) > 1:
        names = ", ".join(p.name for p, _ in candidates)
        raise ParaphraseError(
            f"ambiguous paraphrase set for {rubric_path.name} v{rubric_version}: {names}")
    path, doc = candidates[0]
    paras = doc.get("paraphrases")
    if not paras:
        # A doc that claims this rubric but carries no paraphrases is a broken
        # instrument, not honest absence — fail loud rather than emit a misleading not_run.
        raise ParaphraseError(f"paraphrase set {path.name} matches {rubric_path.name} "
                              f"v{rubric_version} but has no paraphrases")
    return paras
