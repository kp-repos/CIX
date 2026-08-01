import json
from pathlib import Path
from cix.evidence import gate_claims
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIXTURES = Path(__file__).parent / "fixtures"

def _store(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIXTURES / "corpus"), Path("configs/tag_vocabulary_v1.yaml"), db)
    return open_store(db)

def _claims():
    return json.loads((FIXTURES / "claims.json").read_text())

def test_good_quote_passes_bad_quote_drops(tmp_path):
    store = _store(tmp_path)
    result = gate_claims(store, _claims())
    assert "q-good" in [q["ref"] for q in result["quotes"]]
    assert "q-bad" not in [q["ref"] for q in result["quotes"]]

def test_good_stat_passes_bad_stat_drops(tmp_path):
    store = _store(tmp_path)
    result = gate_claims(store, _claims())
    assert "s-good" in [s["ref"] for s in result["stats"]]
    assert "s-bad" not in [s["ref"] for s in result["stats"]]

def test_every_drop_is_logged_with_check_name(tmp_path):
    store = _store(tmp_path)
    gate_claims(store, _claims())
    drops = store.drops()
    checks = {d["claim_ref"]: d["check"] for d in drops}
    assert checks == {"q-bad": "quote_string_match", "s-bad": "stat_recompute"}

def test_gate_is_exact_not_fuzzy(tmp_path):
    store = _store(tmp_path)
    claims = {"quotes": [{"ref": "q-close", "interaction_id": "int-001", "start": 2, "end": 2,
                          "text": "I already called about this last time and it is still not fixed"}],  # missing final period
              "stats": []}
    result = gate_claims(store, claims)
    assert result["quotes"] == []
