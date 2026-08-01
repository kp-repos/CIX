from pathlib import Path
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

def _built(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIXTURES), Path("configs/tag_vocabulary_v1.yaml"), db)
    return open_store(db)

def test_provenance_lookup_id_to_text(tmp_path):
    store = _built(tmp_path)
    s = store.snippet("int-001:0002")
    assert "already called" in s["text"]
    assert s["interaction_id"] == "int-001"

def test_span_lookup_contiguous(tmp_path):
    store = _built(tmp_path)
    span = store.span("int-001", 0, 1)
    assert len(span) == 2 and span[0]["seq"] == 0 and span[1]["seq"] == 1

def test_preselection_by_tag(tmp_path):
    store = _built(tmp_path)
    ids = store.snippets_with_tag("repeat_marker")
    assert "int-001:0002" in ids

def test_interaction_tag_query(tmp_path):
    store = _built(tmp_path)
    assert set(store.interactions_with_tag("account_id", "acct-9")) == {"int-001", "int-003"}

def test_drop_log_roundtrip(tmp_path):
    store = _built(tmp_path)
    store.log_drop(claim_ref="q1", check="quote_string_match", detail="no match in int-001:0000")
    drops = store.drops()
    assert len(drops) == 1 and drops[0]["check"] == "quote_string_match"

def test_versions_recorded(tmp_path):
    store = _built(tmp_path)
    assert store.meta("index_version") == "1.0.0"
    assert store.meta("tag_vocab_version") == "1.0.0"
