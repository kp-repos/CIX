from pathlib import Path
import json
import pytest
from cix.normalize import CorpusValidationError, load_corpus

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def test_loads_all_units_sorted_by_id():
    units = load_corpus(FIXTURES)
    assert [u.id for u in units] == ["int-001", "int-002", "int-003"]

def test_invalid_file_aborts_with_filename(tmp_path):
    (tmp_path / "bad.json").write_text(json.dumps({"id": "x", "source_type": "transcript", "segments": []}))
    with pytest.raises(CorpusValidationError, match="bad.json"):
        load_corpus(tmp_path)

def test_duplicate_ids_rejected(tmp_path):
    doc = {"id": "dup", "source_type": "note", "segments": [{"text": "a"}]}
    (tmp_path / "a.json").write_text(json.dumps(doc))
    (tmp_path / "b.json").write_text(json.dumps(doc))
    with pytest.raises(CorpusValidationError, match="duplicate"):
        load_corpus(tmp_path)
