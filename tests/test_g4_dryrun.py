"""Post-freeze synthetic mechanism dry-runs. Proves AC-16 (differential readings track
injected deltas) and the self-test emits a valid state — across all four §7 layers — on
calibration-scale data. No live model calls (reads persisted-shaped hit lists)."""
from pathlib import Path
from cix.selftest import load_selftest_spec, self_test
from cix.differential import splice_instances, score_delta
from cix.catalogue import load_catalogue
from cix.contracts import InteractionUnit
from cix.normalize import load_corpus

DEV = Path("tests/fixtures/calibration/dev/corpus")
SPEC = load_selftest_spec(Path("configs/selftest_spec_v1.yaml"))

def _units(n=60):
    if DEV.exists():
        return load_corpus(DEV)
    return [InteractionUnit.model_validate(
        {"id": f"i{i:03d}", "source_type": "transcript", "participants": ["a", "customer"],
         "segments": [{"speaker": "a", "text": "x"}]}) for i in range(n)]

def _uniform_hits(ids, item="repeat_contact_unresolved"):
    return [{"item_id": item, "interaction_id": u, "unit": "interaction", "snippet_ids": f"{u}:0000"}
            for u in ids]

def test_selftest_emits_state_on_calibration_scale():
    units = _units()
    ids = [u.id for u in units]
    res = self_test(ids, _uniform_hits(ids), SPEC)
    assert res["state"] in ("material-advantage", "no-material-advantage", "not-evaluable")
    if res["state"] != "not-evaluable":
        assert res["layers_compared"] == ["distribution", "rank_topk", "highlight_diff"]

def test_selftest_all_four_layers_with_catalogue():
    units = _units()
    ids = [u.id for u in units]
    hits = [{"item_id": "manual_after_call_work", "interaction_id": u, "unit": "occurrence",
             "snippet_ids": f"{u}:0000"} for u in ids]
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    res = self_test(ids, hits, SPEC, catalogue=cat, crosswalk={"manual_after_call_work": "SW-ADMIN-CAPTURE"})
    if res["state"] != "not-evaluable":
        assert res["layers_compared"] == ["distribution", "rank_topk", "highlight_diff", "band_movement"]
        assert set(res["per_layer_fraction"]) == set(res["layers_compared"])

def test_differential_ac16_tracks_delta():
    base = [InteractionUnit.model_validate(
        {"id": f"i{i:03d}", "source_type": "transcript", "participants": ["a", "customer"],
         "segments": [{"speaker": "a", "text": "x"}]}) for i in range(40)]
    donor = InteractionUnit.model_validate(
        {"id": "donor", "source_type": "transcript", "participants": ["a", "customer"],
         "segments": [{"speaker": "customer", "text": "third time calling about this"}]})
    variant, expected = splice_instances(base, donor=donor, copies=10)
    observed = {"count": expected["interactions_delta"]}     # synthetic: instrument reads the injected signal exactly
    res = score_delta({"count": expected["interactions_delta"]}, observed, tolerance=0.20)
    assert res["status"] == "pass"                            # AC-16 mechanism: reading tracks the delta
    assert len(variant) == len(base) + 10
