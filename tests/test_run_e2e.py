import json
import re
import sys
from pathlib import Path
from cix.cli import main
from cix.model import ScriptedClient

FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(FIX / "scripted"))
from g2_responses import build_mapping, synthesis_mapping  # noqa: E402

class CountingClient(ScriptedClient):
    """Resolves the COUNT token in synthesis responses to the count stated in the
    prompt, and — emulating a real model — only reports hits for rubric items the
    prompt actually lists. Without this, the fixed per-interaction hit list would
    return foreign items when a narrowed rubric (e.g. the escape audit's single
    item) is asked, tripping run_rubric's unknown-item guard."""
    def complete(self, prompt):
        resp = super().complete(prompt)
        m = re.search(r"count (\d+) \(", prompt)
        if m and '"COUNT"' in resp:
            resp = resp.replace('"COUNT"', m.group(1))
        if '"hits"' in resp:
            data = json.loads(resp)
            data["hits"] = [h for h in data.get("hits", []) if f"- {h['item_id']}:" in prompt]
            resp = json.dumps(data)
        return resp

def _client():
    corpus = FIX / "corpus_g2"
    return CountingClient({**build_mapping(corpus), **synthesis_mapping(corpus)})

def test_one_command_corpus_to_report(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: _client())
    monkeypatch.setattr(cli, "make_second_client",
                        lambda cfg: ScriptedClient(mapping={'"applies"': '{"applies": true}'}))
    rc = main(["run", str(FIX / "corpus_g2"), "--rubric", "configs/mini_rubric_v0.yaml",
               "--out", str(tmp_path / "run")])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "run"
    assert (run_dir / "report.pdf").exists() and (run_dir / "report.json").exists()
    report = json.loads((run_dir / "report.json").read_text())
    assert report["sections"]["distribution"]["eligible_interactions"] == 24
    assert out["validations"] >= 4  # T-ESC rows + T-AGR fields + T-SPLIT + T-DROP
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["rubric_version"] == "0.1.0"
    assert manifest["seeds"]["run"] == 20260731
    assert manifest["model_versions"]["primary"] == "claude-fable-5"
    checks = {v["check"] for v in report["sections"]["method"]["validations"]}
    assert "T-PARA" in checks          # not_run for the mini rubric (honest state)
    assert "SECOND-LAB-SEAT" in checks

def test_null_corpus_runs_and_reports_dev_only(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    corpus = FIX / "corpus_g2_null"
    client = CountingClient({**build_mapping(corpus), **synthesis_mapping(corpus)})
    monkeypatch.setattr(cli, "make_client", lambda cfg: client)
    monkeypatch.setattr(cli, "make_second_client",
                        lambda cfg: ScriptedClient(mapping={'"applies"': '{"applies": true}'}))
    rc = main(["run", str(corpus), "--rubric", "configs/mini_rubric_v0.yaml",
               "--out", str(tmp_path / "null-run"), "--dev-null-control"])
    assert rc == 0
    report = json.loads((tmp_path / "null-run" / "report.json").read_text())
    billing = report["sections"]["distribution"]["items"].get("billing_defect_driver")
    assert billing is None  # zero planted pathology -> zero hits on scripted responses
    vals = report["sections"]["method"]["validations"]
    assert any(v["check"] == "NULL-CONTROL" and v["status"] == "dev_only" for v in vals)

def test_dependency_failure_before_any_model_call(tmp_path, monkeypatch):
    import cix.cli as cli
    calls = {"n": 0}
    class Exploding:
        def complete(self, prompt):
            calls["n"] += 1
            raise AssertionError("model called despite dependency failure")
    monkeypatch.setattr(cli, "make_client", lambda cfg: Exploding())
    bad_rubric = tmp_path / "bad.yaml"
    bad_rubric.write_text(Path("configs/mini_rubric_v0.yaml").read_text().replace(
        'label_schema_version: "1.0.0"', 'label_schema_version: "9.9.9"'))
    rc = main(["run", str(FIX / "corpus_g2"), "--rubric", str(bad_rubric), "--out", str(tmp_path / "r")])
    assert rc == 2 and calls["n"] == 0  # AC-5

def test_calibrate_missing_paths_return_2(tmp_path, capsys):
    from cix.cli import main
    # no manifest.json in run dir
    (tmp_path / "run").mkdir()
    rc = main(["calibrate", str(tmp_path / "run"), "--calibration", str(tmp_path / "cal"),
               "--split", "dev"])
    assert rc == 2
