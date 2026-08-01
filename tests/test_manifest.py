import json
from pathlib import Path
from cix.manifest import build_manifest, write_manifest
from cix.normalize import load_corpus

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def test_manifest_fields_and_write(tmp_path):
    units = load_corpus(FIXTURES)
    m = build_manifest(units, canonical_hash="abc123", tag_vocab_version="1.0.0",
                       privacy_gate="synthetic-fixture", corpus_clearance="n/a: synthetic fixtures")
    assert m["index_version"] == "1.0.0"
    assert m["label_schema_version"] is None
    assert m["seeds"] == {}
    assert len(m["corpus_hash"]) == 64
    path = write_manifest(m, tmp_path)
    on_disk = json.loads(path.read_text())
    assert on_disk == m

def test_corpus_hash_is_content_stable():
    units = load_corpus(FIXTURES)
    m1 = build_manifest(units, "x", "1.0.0", "synthetic-fixture", "n/a")
    m2 = build_manifest(list(units), "x", "1.0.0", "synthetic-fixture", "n/a")
    assert m1["corpus_hash"] == m2["corpus_hash"]

def test_created_at_not_in_hashes():
    units = load_corpus(FIXTURES)
    m = build_manifest(units, "x", "1.0.0", "synthetic-fixture", "n/a")
    assert "created_at" in m and m["created_at"] not in (m["corpus_hash"], m["canonical_hash"])
