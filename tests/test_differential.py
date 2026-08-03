from cix.contracts import InteractionUnit
from cix.differential import delete_subset, duplicate_chains, splice_instances, score_delta

def _units(n=10):
    return [InteractionUnit.model_validate(
        {"id": f"i{i:03d}", "source_type": "transcript", "participants": ["a", "customer"],
         "thread_id": ("T1" if i < 3 else None),
         "segments": [{"speaker": "a", "text": f"turn {i}"}]}) for i in range(n)]

def test_delete_subset_removes_and_predicts_delta():
    units = _units(10)
    variant, expected = delete_subset(units, drop_ids={"i000", "i001"})
    assert len(variant) == 8
    assert {u.id for u in variant}.isdisjoint({"i000", "i001"})
    assert expected["interactions_delta"] == -2

def test_duplicate_chains_grows_thread():
    units = _units(10)                                   # i000-i002 share thread_id T1
    variant, expected = duplicate_chains(units, thread_id="T1")
    assert len(variant) == 13                            # 3 chain members duplicated
    assert expected["interactions_delta"] == 3
    assert len({u.id for u in variant}) == 13            # duplicates get fresh ids

def test_splice_instances_adds_known_signal():
    units = _units(10)
    donor = InteractionUnit.model_validate(
        {"id": "donor", "source_type": "transcript", "participants": ["a", "customer"],
         "segments": [{"speaker": "customer", "text": "third time calling about this"}]})
    variant, expected = splice_instances(units, donor=donor, copies=3)
    assert len(variant) == 13 and expected["interactions_delta"] == 3

def test_score_delta_within_tolerance():
    r = score_delta(expected={"count": 10}, observed={"count": 9}, tolerance=0.2)
    assert r["status"] == "pass" and r["rel_error"] == 0.1
    bad = score_delta(expected={"count": 10}, observed={"count": 4}, tolerance=0.2)
    assert bad["status"] == "fail"
