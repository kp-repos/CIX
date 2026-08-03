import json
from pathlib import Path
import yaml
from cix.cli import main
from cix.model import ScriptedClient

def _mini_spec(tmp_path: Path) -> Path:
    doc = yaml.safe_load(Path("configs/service_corpus_spec_v1.yaml").read_text(encoding="utf-8"))
    doc["threads"] = [{"key": "TH1", "pathology": "SP1", "interactions": 2,
                       "issue": "a data import job that stalls partway"}]
    doc["singles"] = [{"pathology": "SP3", "count": 1}]
    doc["clean_interactions"] = 1
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p

def test_generate_service_corpus_command(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    seg = json.dumps({"segments": [{"speaker": "agent", "text": "How can I help?"},
                                   {"speaker": "customer", "text": "Question on our account."}]})
    monkeypatch.setattr(cli, "make_second_client", lambda cfg: ScriptedClient(sequence=[seg] * 4))
    rc = main(["generate-service-corpus", "--spec", str(_mini_spec(tmp_path)),
               "--out", str(tmp_path / "svc")])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["interactions"] == 4 and out["planted"] == 2   # 1 thread repeat + 1 single
    assert (tmp_path / "svc" / "corpus").is_dir()
    assert (tmp_path / "svc" / "truth.json").exists()
    assert (tmp_path / "svc" / "provenance.yaml").exists()
