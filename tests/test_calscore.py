import json
import pytest
from cix.calscore import HoldoutError, guard_holdout, log_cycle, record_holdout, score_calibration, score_null

T_CAL = {"relative_error_max": 0.25, "absolute_error_max": 2, "mechanism_attribution_floor": 0.8}
T_NULL = {"false_reports_per_100_max": 4, "min_null_interactions": 2}
CROSS = {"P1": "seller_admin_burden"}
UNITS = {"seller_admin_burden": "occurrence", "status_chasing": "occurrence"}

def _truth():
    return {
        "d-000": {"pathology": "P1", "loudness": "loud", "expected_occurrences": 2},
        "d-001": {"pathology": "P1", "loudness": "moderate", "expected_occurrences": 1},
        "d-002": {"pathology": "P1", "loudness": "camouflaged", "expected_occurrences": 1},
        "d-003": None,
    }

def _hit(item, uid):
    return {"item_id": item, "interaction_id": uid, "unit": "occurrence", "snippet_ids": f"{uid}:0000"}

def test_perfect_recovery_passes():
    hits = [_hit("seller_admin_burden", "d-000"), _hit("seller_admin_burden", "d-000"),
            _hit("seller_admin_burden", "d-001"), _hit("seller_admin_burden", "d-002")]
    [row] = score_calibration(_truth(), hits, CROSS, UNITS, T_CAL)
    assert row["pathology"] == "P1" and row["status"] == "pass"
    assert row["expected"] == 3 and row["recovered"] == 3          # loud+moderate pooled; camouflaged ungated
    assert row["detection_by_loudness"]["camouflaged"] == [1, 1]

def test_gross_miss_fails_conjunctively():
    hits = []  # recovered 0 of 3: rel 1.0 > 0.25 AND abs 3 > 2
    [row] = score_calibration(_truth(), hits, CROSS, UNITS, T_CAL)
    assert row["status"] == "fail"

def test_small_absolute_error_passes():
    hits = [_hit("seller_admin_burden", "d-000"), _hit("seller_admin_burden", "d-001")]
    [row] = score_calibration(_truth(), hits, CROSS, UNITS, T_CAL)  # 2 of 3: rel 0.33 but abs 1 <= 2
    assert row["status"] == "pass"

def test_wrong_item_attribution_flags_mechanism():
    hits = [_hit("status_chasing", "d-000"), _hit("status_chasing", "d-001")]
    cross = {"P1": "seller_admin_burden", "P2": "status_chasing"}
    truth = _truth() | {"d-010": {"pathology": "P2", "loudness": "loud", "expected_occurrences": 2},
                        "d-011": {"pathology": "P2", "loudness": "moderate", "expected_occurrences": 2}}
    rows = score_calibration(truth, hits, cross, UNITS, T_CAL)
    p1 = next(r for r in rows if r["pathology"] == "P1")
    assert p1["status"] in ("fail", "mechanism_fail")   # P1 plants detected only as the WRONG item

def test_null_scoring():
    ids = [f"n-{i:03d}" for i in range(50)]
    hits = [_hit("seller_admin_burden", "n-000"), _hit("seller_admin_burden", "n-001"),
            _hit("seller_admin_burden", "n-002")]
    res = score_null(ids, hits, {"seller_admin_burden"}, T_NULL)
    assert res["status"] == "fail" and res["rate_per_100"] == 6.0
    ok = score_null(ids, hits[:1], {"seller_admin_burden"}, T_NULL)
    assert ok["status"] == "pass" and ok["rate_per_100"] == 2.0

def test_null_ignores_untargeted_items():
    ids = [f"n-{i:03d}" for i in range(50)]
    hits = [_hit("clean_handoff_execution", "n-000")]   # positive item: not a false report
    assert score_null(ids, hits, {"seller_admin_burden"}, T_NULL)["rate_per_100"] == 0.0

def test_holdout_is_one_shot(tmp_path):
    with pytest.raises(HoldoutError):
        guard_holdout(tmp_path, final=False)            # requires --final
    guard_holdout(tmp_path, final=True)                 # first evaluation: allowed
    record_holdout(tmp_path, {"T-CAL": []})
    with pytest.raises(HoldoutError):
        guard_holdout(tmp_path, final=True)             # second evaluation: refused

def test_cycle_log_appends(tmp_path):
    assert log_cycle(tmp_path, {"note": "c1"}, max_cycles=3) == 1
    assert log_cycle(tmp_path, {"note": "c2"}, max_cycles=3) == 2
    log = json.loads((tmp_path / "cycles.json").read_text())
    assert [c["summary"]["note"] for c in log] == ["c1", "c2"]
