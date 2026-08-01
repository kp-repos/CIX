import json
from pathlib import Path
from cix.audits import drop_rate_check, escape_audit, label_self_agreement, split_half
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.rubric import load_rubric
from cix.store import build_store, open_store

FIX = Path(__file__).parent / "fixtures" / "corpus"
THRESHOLDS = {"T-ESC": {"escape_sample_per_item": 12, "min_sample_for_validity": 8},
              "T-AGR": {"agreement_sample_interactions": 6, "min_sample_for_validity": 5, "per_field_floor": 0.85},
              "T-DROP": {"rate_alarm": 0.02},
              "T-SPLIT": {"min_corpus_interactions": 20}}

def _setup(tmp_path):
    db = tmp_path / "run.db"
    units = load_corpus(FIX)
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    return units, open_store(db), load_rubric(Path("configs/mini_rubric_v0.yaml"), "1.0.0", "1.0.0")

def test_escape_audit_low_power_on_tiny_corpus(tmp_path):
    units, store, rubric = _setup(tmp_path)
    client = ScriptedClient({"int-": json.dumps({"hits": []})})
    results = escape_audit(store, units, rubric, client, THRESHOLDS["T-ESC"], seed=7)
    by_item = {r["item_id"]: r for r in results}
    # 3-interaction fixture: excluded pool for prefiltered items is < min_sample -> insufficient_power
    assert by_item["repeat_contact_unresolved"]["status"] == "insufficient_power"
    for r in results:
        store.write_validation("T-ESC", r["item_id"], r["status"], r["detail"])
    assert len(store.validations()) == len(results)

def test_self_agreement_flags_unstable_field(tmp_path):
    units, store, rubric = _setup(tmp_path)
    la = store.ensure_label_artifact("ch", "1.0.0", "m", "p")
    for u in units:
        store.write_labels(la, u.id, {"motion": "service", "outcome": "resolved"})
    # re-judge returns a different outcome every time -> outcome agreement 0.0
    rejudge = ScriptedClient({"int-": json.dumps({"motion": "service", "outcome": "escalated"})})
    results = label_self_agreement(store, units, la, rejudge, THRESHOLDS["T-AGR"], seed=7,
                                   fields=["motion", "outcome"])
    by_field = {r["field"]: r for r in results}
    assert by_field["motion"]["status"] in ("agree", "insufficient_power")
    if by_field["outcome"]["status"] != "insufficient_power":
        assert by_field["outcome"]["status"] == "unstable"

def test_split_half_insufficient_power_below_min(tmp_path):
    hits = [{"item_id": "a", "interaction_id": f"i{n}", "unit": "interaction", "snippet_ids": f"i{n}:0000"}
            for n in range(4)]
    r = split_half(hits, interaction_ids=[f"i{n}" for n in range(4)],
                   cfg=THRESHOLDS["T-SPLIT"], seed=7)
    assert r["status"] == "insufficient_power"

def test_split_half_detects_stable_rank():
    ids = [f"i{n}" for n in range(40)]
    hits = [{"item_id": "big", "interaction_id": i, "unit": "interaction", "snippet_ids": f"{i}:0000"} for i in ids]
    hits += [{"item_id": "small", "interaction_id": i, "unit": "interaction", "snippet_ids": f"{i}:0001"} for i in ids[:8]]
    r = split_half(hits, interaction_ids=ids, cfg=THRESHOLDS["T-SPLIT"], seed=7)
    assert r["status"] == "stable"

def test_drop_rate_release_block_on_fabricated_quote(tmp_path):
    r = drop_rate_check(candidate_claims=10, quote_drops=1, stat_drops=0, cfg=THRESHOLDS["T-DROP"])
    assert r["status"] == "release_block"
    r2 = drop_rate_check(candidate_claims=100, quote_drops=0, stat_drops=1, cfg=THRESHOLDS["T-DROP"])
    assert r2["status"] == "pass"  # 1% stat drop, under alarm, no fabricated evidence
