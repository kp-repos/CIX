import sqlite3
from pathlib import Path
import pytest
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"
VOCAB = Path("configs/tag_vocabulary_v1.yaml")

def _built(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIXTURES), VOCAB, db)
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

def test_build_store_refuses_existing_db(tmp_path):
    db = tmp_path / "run.db"
    units = load_corpus(FIXTURES)
    build_store(units, VOCAB, db)
    with pytest.raises(FileExistsError):  # a run store is written once; never appended to
        build_store(units, VOCAB, db)

def test_foreign_keys_enforced(tmp_path):
    store = _built(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):  # orphan tag row rejected — declared FKs are live
        store.con.execute("INSERT INTO snippet_tags VALUES ('does-not-exist:9999', 'x', '1')")

def test_snippets_for_ref_single_id(tmp_path):
    store = _built(tmp_path)
    rows = store.snippets_for_ref("int-001:0000")
    assert len(rows) == 1 and rows[0]["text"] == "My card was charged twice for the same order."

def test_snippets_for_ref_range_is_ordered_span(tmp_path):
    # A hits-table range "id-id" must expand to the contiguous span, in seq order —
    # the ':NNNN'-then-'-' shape is exactly what the old split('-')[0] mangled.
    store = _built(tmp_path)
    rows = store.snippets_for_ref("int-001:0000-int-001:0002")
    assert [r["seq"] for r in rows] == [0, 1, 2]
    assert rows[0]["id"] == "int-001:0000" and rows[-1]["id"] == "int-001:0002"

def test_snippets_for_ref_fails_closed(tmp_path):
    store = _built(tmp_path)
    assert store.snippets_for_ref("int-999:0000") == []          # absent single id
    assert store.snippets_for_ref("svc") == []                   # the old bug's bogus token
    assert store.snippets_for_ref("nope-nope") == []             # both endpoints absent
    assert store.snippets_for_ref("int-001:0000-int-002:0000") == []  # cross-interaction range
