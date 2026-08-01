import json
import shutil
from pathlib import Path
from cix.canonical import canonical_hash
from cix.normalize import load_corpus
from cix.store import build_store

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def _build(corpus_dir, db_path):
    build_store(load_corpus(corpus_dir), Path("configs/tag_vocabulary_v1.yaml"), db_path)
    return canonical_hash(db_path)

def test_rebuild_gives_identical_hash(tmp_path):
    h1 = _build(FIXTURES, tmp_path / "a.db")
    h2 = _build(FIXTURES, tmp_path / "b.db")
    assert h1 == h2

def test_file_order_and_names_do_not_matter(tmp_path):
    shuffled = tmp_path / "shuffled"
    shuffled.mkdir()
    # copy fixtures under reversed filenames so glob order differs
    for i, src in enumerate(sorted(FIXTURES.glob("*.json"), reverse=True)):
        shutil.copy(src, shuffled / f"zz-{i}.json")
    assert _build(FIXTURES, tmp_path / "a.db") == _build(shuffled, tmp_path / "c.db")

def test_content_change_changes_hash(tmp_path):
    mutated = tmp_path / "mutated"
    shutil.copytree(FIXTURES, mutated)
    doc = json.loads((mutated / "int-002.json").read_text())
    doc["segments"][0]["text"] = "How do I close my account?"
    (mutated / "int-002.json").write_text(json.dumps(doc))
    assert _build(FIXTURES, tmp_path / "a.db") != _build(mutated, tmp_path / "d.db")
