import json
from pathlib import Path
from cix.cli import VOCAB_PATH, main
from cix.contracts import InteractionUnit
from cix.store import build_store, open_store

def _fake_run(tmp_path: Path, n: int = 60) -> Path:
    """Fabricate a minimal run dir: store + persisted label/hit artifacts + manifest."""
    run = tmp_path / "run"
    run.mkdir()
    units = [InteractionUnit.model_validate(
        {"id": f"i{i:03d}", "source_type": "transcript", "participants": ["agent", "customer"],
         "segments": [{"speaker": "agent", "text": f"routine contact number {i}"}]})
        for i in range(n)]
    build_store(units, VOCAB_PATH, run / "run.db")
    store = open_store(run / "run.db")
    la = store.ensure_label_artifact("chash-test", "1.0.0", "test-model", "ph-labels")
    for u in units:
        store.write_labels(la, u.id, {"motion": "service", "intent": "x",
                                      "driver_origin": "customer", "automatability": "rote",
                                      "outcome": "resolved", "handoff_events": ""})
    ha = store.ensure_hit_artifact(la, "1.0.0", "test-model", "ph-hits")
    # skewed occurrence hits so the distribution is non-degenerate
    for u in units[:20]:
        store.write_hit(ha, "manual_after_call_work", u.id, "occurrence", f"{u.id}:0000")
    for u in units[20:28]:
        store.write_hit(ha, "status_chase_inbound", u.id, "occurrence", f"{u.id}:0000")
    manifest = {"artifacts": {"labels": la, "hits": ha},
                "label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0",
                "corpus_hash": "chash-test", "scrub_salt": "cix-test"}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run

def test_selftest_emits_state_and_report(tmp_path, capsys):
    run = _fake_run(tmp_path)
    rc = main(["self-test", str(run),
               "--catalogue", "configs/catalogue_v0_1.yaml",
               "--rubric", "configs/service_rubric_v1.yaml"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] in ("material-advantage", "no-material-advantage", "not-evaluable")
    assert "band_movement" in out["layers_compared"]        # catalogue+rubric supplied
    report = json.loads((run / "selftest_report.json").read_text(encoding="utf-8"))
    assert report["state"] == out["state"]
    store = open_store(run / "run.db")
    rows = [v for v in store.validations() if v["check"] == "T-SST"]
    assert len(rows) == 1 and rows[0]["status"] == out["state"]

def test_selftest_not_evaluable_below_floor(tmp_path, capsys):
    run = _fake_run(tmp_path, n=10)                          # below min_evaluable_interactions=40
    rc = main(["self-test", str(run)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] == "not-evaluable"

def test_selftest_refuses_without_manifest(tmp_path, capsys):
    (tmp_path / "empty").mkdir()
    rc = main(["self-test", str(tmp_path / "empty")])
    assert rc == 2

def _tsst_detail(run: Path) -> str:
    store = open_store(run / "run.db")
    rows = [v for v in store.validations() if v["check"] == "T-SST"]
    assert len(rows) == 1
    return rows[0]["detail"]

def test_selftest_outcome_level_defaults_o1_without_substrate_class(tmp_path, capsys):
    run = _fake_run(tmp_path)                                # manifest has no substrate_class
    rc = main(["self-test", str(run)])
    assert rc == 0
    detail = _tsst_detail(run)
    assert "outcome_level=O1-synthetic" in detail
    assert "outcome_level=O3" not in detail

def test_selftest_outcome_level_s2_is_o3_corpus_level(tmp_path, capsys):
    run = _fake_run(tmp_path)
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["substrate_class"] = "S2"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    rc = main(["self-test", str(run)])
    assert rc == 0
    detail = _tsst_detail(run)
    assert "outcome_level=O3-corpus-level-items-only" in detail
    assert "O1-synthetic" not in detail
