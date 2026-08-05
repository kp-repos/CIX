import json
from pathlib import Path
import yaml
from pydantic import ValidationError
from cix.contracts import InteractionUnit

class CorpusValidationError(Exception):
    pass

def load_corpus(corpus_dir: Path) -> list[InteractionUnit]:
    units: list[InteractionUnit] = []
    for path in sorted(Path(corpus_dir).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            units.append(InteractionUnit.model_validate(data))
        except (json.JSONDecodeError, ValidationError) as e:
            raise CorpusValidationError(f"{path.name}: {e}") from e
    seen: set[str] = set()
    for u in units:
        if u.id in seen:
            raise CorpusValidationError(f"duplicate interaction id: {u.id}")
        seen.add(u.id)
    units.sort(key=lambda u: u.id)
    return units

# Recorded per PRD v1.3 §2.3-S. "unspecified" is the honest legacy default: it maps to
# the strictest posture downstream (no O3, O1-synthetic outcome level).
DEFAULT_CORPUS_PROPERTIES = {
    "substrate_class": "unspecified",
    "licence_tier": "unspecified",
    "speaker_attribution": "none",
    "economic_signal": "redacted",
    "ivr_structure": "absent",
}

def load_corpus_properties(corpus_dir: Path) -> dict:
    """PRD v1.3 §2.3-S corpus-property record. Looks in the corpus dir, then its parent
    (the adapter writes units to <out>/units with properties at <out>/). Absent file ->
    honest defaults, never an error."""
    for cand in (Path(corpus_dir) / "corpus_properties.yaml",
                 Path(corpus_dir).parent / "corpus_properties.yaml"):
        if cand.exists():
            loaded = yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
            return {**DEFAULT_CORPUS_PROPERTIES, **loaded}
    return dict(DEFAULT_CORPUS_PROPERTIES)
