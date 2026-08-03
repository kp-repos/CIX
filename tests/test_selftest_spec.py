from pathlib import Path
from cix.selftest import load_selftest_spec

def test_spec_loads():
    s = load_selftest_spec(Path("configs/selftest_spec_v1.yaml"))
    assert s.sample_fraction == 0.10
    assert len(s.seeds) == 5
    assert s.min_evaluable_interactions == 40
    assert s.layers == ["distribution", "rank_topk", "band_movement", "highlight_diff"]
