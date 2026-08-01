import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from cix import INDEX_VERSION
from cix.contracts import InteractionUnit

MANIFEST_VERSION = "1.0.0"

def corpus_hash(units: list[InteractionUnit]) -> str:
    h = hashlib.sha256()
    for u in sorted(units, key=lambda u: u.id):
        h.update(u.model_dump_json().encode("utf-8"))
    return h.hexdigest()

def build_manifest(units, canonical_hash: str, tag_vocab_version: str,
                   privacy_gate: str, corpus_clearance: str) -> dict:
    return {
        "manifest_version": MANIFEST_VERSION,
        "corpus_hash": corpus_hash(units),
        "canonical_hash": canonical_hash,
        "index_version": INDEX_VERSION,
        "tag_vocab_version": tag_vocab_version,
        "label_schema_version": None,
        "rubric_version": None,
        "catalogue_version": None,
        "model_versions": {},
        "prompt_hashes": {},
        "seeds": {},
        "thresholds_version": None,
        "privacy_gate": privacy_gate,
        "corpus_clearance": corpus_clearance,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

def write_manifest(manifest: dict, run_dir: Path) -> Path:
    path = Path(run_dir) / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
