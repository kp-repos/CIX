import re
from pathlib import Path
import yaml
from cix.contracts import InteractionUnit

def load_vocabulary(path: Path) -> dict:
    vocab = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for fam in vocab["lexical"]:
        fam["_rx"] = re.compile(fam["pattern"], re.IGNORECASE)
    return vocab

def _position(seq: int, n: int) -> str:
    if seq < n / 3:
        return "opening"
    if seq >= 2 * n / 3:
        return "closing"
    return "middle"

def tag_snippets(snippets: list[dict], vocab: dict) -> list[tuple[str, str, str]]:
    """Rows (snippet_id, tag, value), deterministically ordered."""
    rows: list[tuple[str, str, str]] = []
    n = len(snippets)
    for s in snippets:
        rows.append((s["id"], "position", _position(s["seq"], n)))
        rows.append((s["id"], "turn_length", str(len(s["text"]))))
        if s["speaker"] is not None:
            rows.append((s["id"], "speaker_role", s["speaker"]))
        for fam in vocab["lexical"]:
            if fam["_rx"].search(s["text"]):
                rows.append((s["id"], fam["name"], "1"))
    rows.sort()
    return rows

def tag_interaction(unit: InteractionUnit, snippets: list[dict]) -> list[tuple[str, str, str]]:
    rows = [
        (unit.id, "interaction_len_segments", str(len(snippets))),
        (unit.id, "source_type", unit.source_type),
    ]
    for field in ("account_id", "thread_id", "date"):
        val = getattr(unit, field)
        if val is not None:
            rows.append((unit.id, field, val))
    total = sum(len(s["text"]) for s in snippets) or 1
    agent = sum(len(s["text"]) for s in snippets if s["speaker"] == "agent")
    rows.append((unit.id, "speaker_balance", f"{agent / total:.3f}"))
    rows.sort()
    return rows
