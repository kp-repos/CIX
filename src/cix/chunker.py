import hashlib
from cix.contracts import InteractionUnit

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def chunk(unit: InteractionUnit) -> list[dict]:
    """Snippet = one speaker turn (R-IDX-1). IDs are positional and content-stable."""
    return [
        {
            "id": f"{unit.id}:{seq:04d}",
            "interaction_id": unit.id,
            "seq": seq,
            "speaker": seg.speaker,
            "text": seg.text,
            "content_hash": _hash(seg.text),
        }
        for seq, seg in enumerate(unit.segments)
    ]
