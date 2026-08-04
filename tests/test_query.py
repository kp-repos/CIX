import json
import sqlite3
from pathlib import Path
import pytest
from cix.cli import main
from cix.normalize import load_corpus
from cix.store import build_store, open_store
from cix.query import resolve_item, find_quote

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"
VOCAB = Path("configs/tag_vocabulary_v1.yaml")

# A quote that is verbatim-correct against the fixture, and one that is not.
GOOD_QUOTE = {"interaction_id": "int-001", "start": 0, "end": 0,
              "text": "My card was charged twice for the same order."}
BAD_QUOTE = {"interaction_id": "int-001", "start": 0, "end": 0,
             "text": "This text was never in any transcript."}

def _run_dir(tmp_path, evidence=None):
    """Build a minimal but real run dir: run.db with hits, report.json, manifest.json."""
    run = tmp_path / "run"
    run.mkdir()
    db = run / "run.db"
    build_store(load_corpus(FIXTURES), VOCAB, db)
    store = open_store(db)
    la = store.ensure_label_artifact("chash", "1.0.0", "m", "lph")
    ha = store.ensure_hit_artifact(la, "1.0.0", "m", "ph")
    store.write_hit(ha, "billing_defect_driver", "int-001", "interaction", "int-001:0000")
    store.write_hit(ha, "billing_defect_driver", "int-001", "interaction", "int-001:0001-int-001:0002")
    finding = {"item_id": "billing_defect_driver", "narrative": "Billing defects lead volume.",
               "count": 2, "share": 0.6667, "evidence": evidence or []}
    report = {"sections": {"highlights": [finding]}}
    manifest = {"artifacts": {"labels": la, "hits": ha}}
    (run / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run, store, report, manifest

def test_resolve_item_expands_hits_to_scrubbed_text(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path)
    res = resolve_item(store, report, manifest, "billing_defect_driver")
    assert res["found"] and res["count"] == 2
    texts = [s["text"] for h in res["hits"] for s in h["snippets"]]
    assert "My card was charged twice for the same order." in texts            # single-id hit
    assert "I can help with that. Let me check the billing record." in texts    # first of range hit

def test_resolve_item_marks_quote_verbatim(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path, evidence=[GOOD_QUOTE])
    res = resolve_item(store, report, manifest, "billing_defect_driver")
    assert res["quotes"] and res["quotes"][0]["verbatim"] is True

def test_resolve_item_flags_tampered_quote(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path, evidence=[BAD_QUOTE])
    res = resolve_item(store, report, manifest, "billing_defect_driver")
    assert res["quotes"][0]["verbatim"] is False

def test_resolve_item_unknown_is_not_found(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path)
    assert resolve_item(store, report, manifest, "no_such_item")["found"] is False

def test_find_quote_verbatim_match_and_miss(tmp_path):
    run, store, report, manifest = _run_dir(tmp_path)
    hit = find_quote(store, "My card was charged twice for the same order.")
    assert len(hit) == 1 and hit[0]["id"] == "int-001:0000"
    assert find_quote(store, "text that is not in the corpus") == []

def test_read_only_store_refuses_writes(tmp_path):
    run, _, _, _ = _run_dir(tmp_path)
    ro = open_store(run / "run.db", read_only=True)
    with pytest.raises(sqlite3.OperationalError):
        ro.log_drop("x", "quote_string_match", "should never be written by query")

def test_cli_query_item_prints_source(tmp_path, capsys):
    run, _, _, _ = _run_dir(tmp_path)
    rc = main(["query", str(run), "--item", "billing_defect_driver"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "My card was charged twice for the same order." in out

def test_cli_query_bogus_quote_fails_closed(tmp_path, capsys):
    run, _, _, _ = _run_dir(tmp_path)
    rc = main(["query", str(run), "--quote", "definitely not in the corpus"])
    assert rc == 1
    assert "does NOT resolve" in capsys.readouterr().out

def test_cli_query_real_quote_resolves(tmp_path, capsys):
    run, _, _, _ = _run_dir(tmp_path)
    rc = main(["query", str(run), "--quote", "My card was charged twice for the same order."])
    assert rc == 0
    assert "int-001:0000" in capsys.readouterr().out

def test_cli_query_unknown_item_nonzero(tmp_path, capsys):
    run, _, _, _ = _run_dir(tmp_path)
    rc = main(["query", str(run), "--item", "no_such_item"])
    assert rc == 1

def test_cli_query_leaves_drop_log_untouched(tmp_path, capsys):
    run, store, _, _ = _run_dir(tmp_path)
    before = len(store.drops())
    main(["query", str(run), "--item", "billing_defect_driver"])
    main(["query", str(run), "--quote", "nope"])
    assert len(open_store(run / "run.db").drops()) == before == 0
