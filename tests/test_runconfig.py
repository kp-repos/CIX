from pathlib import Path
from cix.runconfig import load_run_config, load_thresholds

def test_run_config_loads():
    rc = load_run_config(Path("configs/run_config_v1.yaml"))
    assert rc.model == "claude-opus-4-8"
    assert rc.temperature == 0
    assert rc.seed == 20260731

def test_thresholds_register_loads_g2_rows():
    reg = load_thresholds(Path("configs/thresholds_v1.yaml"))
    assert set(reg.keys()) >= {"T-ESC", "T-AGR", "T-DROP", "T-SPLIT"}
    assert reg["T-AGR"]["per_field_floor"] == 0.85
    assert reg["T-ESC"]["frozen_at_gate"] == "G2"

def test_thresholds_register_loads_g3_rows():
    reg = load_thresholds(Path("configs/thresholds_v1.yaml"))
    assert set(reg.keys()) >= {"T-PARA", "T-CAL", "T-NULL", "T-ITER"}
    assert reg["T-CAL"]["relative_error_max"] == 0.25
    assert reg["T-NULL"]["false_reports_per_100_max"] == 4
    assert reg["T-ITER"]["max_dev_cycles"] == 3
    for tid in ("T-PARA", "T-CAL", "T-NULL", "T-ITER"):
        assert reg[tid]["frozen_at_gate"] == "G3"
