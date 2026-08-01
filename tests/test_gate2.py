import json
from pathlib import Path
from cix.gate2 import gate_synthesis
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIX = Path(__file__).parent / "fixtures" / "corpus"

GOOD = {"narrative": "x", "claimed_count": 2,
        "quotes": [{"interaction_id": "int-001", "start": 0, "end": 0,
                    "text": "My card was charged twice for the same order."}],
        "mechanism": {"proposed": "p", "alternative": "a",
                      "discriminating_snippet_ids": ["int-001:0001"]}}
BAD_QUOTE = {**GOOD, "quotes": [{"interaction_id": "int-001", "start": 0, "end": 0,
                                 "text": "I demand compensation now."}]}
BAD_COUNT = {**GOOD, "claimed_count": 99}
UNDISCHARGED = {**GOOD, "mechanism": {"proposed": "p", "alternative": "a", "discriminating_snippet_ids": []}}

ROLLUP = {"items": {"good": {"count": 2}, "badq": {"count": 2}, "badc": {"count": 2}, "und": {"count": 2}}}

def _setup(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIX), Path("configs/tag_vocabulary_v1.yaml"), db)
    store = open_store(db)
    sid = "syn1"
    for item, body in [("good", GOOD), ("badq", BAD_QUOTE), ("badc", BAD_COUNT), ("und", UNDISCHARGED)]:
        store.write_synthesis(sid, item, json.dumps(body))
    return store, sid

def test_gate_passes_good_drops_bad(tmp_path):
    store, sid = _setup(tmp_path)
    result = gate_synthesis(store, sid, ROLLUP)
    kept = {f["item_id"] for f in result["findings"]}
    assert "good" in kept and "badq" not in kept and "badc" not in kept

def test_drops_logged_with_check_names(tmp_path):
    store, sid = _setup(tmp_path)
    gate_synthesis(store, sid, ROLLUP)
    checks = {d["claim_ref"]: d["check"] for d in store.drops()}
    assert checks["badq"] == "quote_string_match"
    assert checks["badc"] == "stat_recompute"

def test_mechanism_discharge_status(tmp_path):
    store, sid = _setup(tmp_path)
    result = gate_synthesis(store, sid, ROLLUP)
    by_id = {f["item_id"]: f for f in result["findings"]}
    assert by_id["good"]["mechanism_status"] == "discharged"
    assert by_id["und"]["mechanism_status"] == "undischarged"  # kept, visibly marked (AC-10)

def test_gate_stats_for_drop_rate(tmp_path):
    store, sid = _setup(tmp_path)
    result = gate_synthesis(store, sid, ROLLUP)
    assert result["candidate_claims"] == 8  # 4 quotes + 4 counts
    assert result["quote_drops"] == 1 and result["stat_drops"] == 1
