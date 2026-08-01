import json
from pathlib import Path
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
