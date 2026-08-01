import json
from pathlib import Path
from cix.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

def test_index_builds_run_dir(tmp_path, capsys):
    rc = main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "run1")])
    assert rc == 0
    assert (tmp_path / "run1" / "run.db").exists()
    manifest = json.loads((tmp_path / "run1" / "manifest.json").read_text())
    assert manifest["privacy_gate"] == "synthetic-fixture"
    assert manifest["canonical_hash"] == json.loads(capsys.readouterr().out)["canonical_hash"]

def test_hash_reproduces(tmp_path, capsys):
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "runA")])
    outA = json.loads(capsys.readouterr().out)
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "runB")])
    outB = json.loads(capsys.readouterr().out)
    assert outA["canonical_hash"] == outB["canonical_hash"]
    rc = main(["hash", str(tmp_path / "runA")])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["canonical_hash"] == outA["canonical_hash"]

def test_verify_reports_drops(tmp_path, capsys):
    main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "run1")])
    capsys.readouterr()
    rc = main(["verify", str(tmp_path / "run1"), "--claims", str(FIXTURES / "claims.json")])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1  # drops occurred → nonzero for visibility
    assert out["passed"] == {"quotes": 1, "stats": 1}
    assert out["dropped"] == 2

def test_invalid_corpus_fails_before_any_output(tmp_path, capsys):
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "x.json").write_text("{not json")
    rc = main(["index", str(bad), "--out", str(tmp_path / "run2")])
    assert rc == 2
    assert not (tmp_path / "run2" / "run.db").exists()  # R-RUN-1: validate before writing

def test_index_works_from_any_cwd(tmp_path, monkeypatch):
    # The tag vocabulary is resolved relative to the package, not the process
    # cwd, so the installed `cix` command works from any directory.
    monkeypatch.chdir(tmp_path)
    rc = main(["index", str(FIXTURES / "corpus"), "--out", str(tmp_path / "run1")])
    assert rc == 0
    assert (tmp_path / "run1" / "run.db").exists()

def test_index_refuses_existing_run(tmp_path, capsys):
    out = tmp_path / "run1"
    assert main(["index", str(FIXTURES / "corpus"), "--out", str(out)]) == 0
    capsys.readouterr()
    rc = main(["index", str(FIXTURES / "corpus"), "--out", str(out)])
    assert rc == 3  # index writes a fresh run; refuse rather than clobber/crash
    assert "already exists" in capsys.readouterr().err
