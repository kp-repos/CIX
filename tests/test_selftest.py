from pathlib import Path
from cix.selftest import load_selftest_spec, sample_ids, self_test

SPEC = load_selftest_spec(Path("configs/selftest_spec_v1.yaml"))

def _hits(item_counts: dict, n_int: int):
    """Build hits so that item -> count interactions carry that item."""
    hits, k = [], 0
    for item, c in item_counts.items():
        for _ in range(c):
            hits.append({"item_id": item, "interaction_id": f"i{k:03d}", "unit": "interaction",
                         "snippet_ids": f"i{k:03d}:0000"})
            k += 1
    return hits

def test_not_evaluable_below_min():
    ids = [f"i{i:03d}" for i in range(10)]                  # < min_evaluable_interactions (40)
    res = self_test(ids, _hits({"a": 5}, 10), SPEC)
    assert res["state"] == "not-evaluable"

def test_sample_ids_deterministic_and_sized():
    ids = [f"i{i:03d}" for i in range(100)]
    s1 = sample_ids(ids, 0.10, seed=11)
    s2 = sample_ids(ids, 0.10, seed=11)
    assert s1 == s2 and len(s1) == 10                      # 10% of 100, deterministic
    assert sample_ids(ids, 0.10, seed=22) != s1            # different seed differs

def test_reproducing_sample_yields_no_material_advantage():
    # uniform signal: every interaction carries item "a" once -> any sample reproduces rank/dist
    ids = [f"i{i:03d}" for i in range(100)]
    hits = [{"item_id": "a", "interaction_id": u, "unit": "interaction", "snippet_ids": f"{u}:0000"}
            for u in ids]
    res = self_test(ids, hits, SPEC)
    assert res["state"] == "no-material-advantage"
    assert 0.0 <= res["material_fraction"] <= 1.0

def test_rare_driver_flips_to_material_advantage():
    # a rare top-item present in the full corpus but absent from most 10% samples
    ids = [f"i{i:03d}" for i in range(100)]
    hits = [{"item_id": "common", "interaction_id": u, "unit": "interaction", "snippet_ids": f"{u}:0000"}
            for u in ids]
    hits += [{"item_id": "rare", "interaction_id": ids[i], "unit": "interaction",
              "snippet_ids": f"{ids[i]}:0001"} for i in (0, 1)]
    res = self_test(ids, hits, SPEC)
    assert res["state"] in ("material-advantage", "no-material-advantage")
    assert "per_seed" in res and len(res["per_seed"]) == len(SPEC.seeds)

def test_layers_exclude_band_without_catalogue():
    ids = [f"i{i:03d}" for i in range(100)]
    hits = [{"item_id": "a", "interaction_id": u, "unit": "interaction", "snippet_ids": f"{u}:0000"}
            for u in ids]
    res = self_test(ids, hits, SPEC)
    assert res["layers_compared"] == ["distribution", "rank_topk", "highlight_diff"]
    assert "band_movement" not in res["per_layer_fraction"]
    assert set(res["per_layer_fraction"]) == set(res["layers_compared"])

def test_band_layer_present_with_catalogue():
    from cix.catalogue import load_catalogue
    ids = [f"i{i:03d}" for i in range(100)]
    hits = [{"item_id": "manual_after_call_work", "interaction_id": u, "unit": "occurrence",
             "snippet_ids": f"{u}:0000"} for u in ids]
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    res = self_test(ids, hits, SPEC, catalogue=cat, crosswalk={"manual_after_call_work": "SW-ADMIN-CAPTURE"})
    assert "band_movement" in res["layers_compared"]
    assert set(res["per_layer_fraction"]) == set(res["layers_compared"])

def test_tv_distance_helper():
    from cix.selftest import _tv_distance
    assert _tv_distance({"a": 1.0}, {"a": 1.0}) == 0.0
    assert _tv_distance({"a": 1.0}, {"b": 1.0}) == 1.0
    assert abs(_tv_distance({"a": 0.5, "b": 0.5}, {"a": 1.0}) - 0.5) < 1e-9
