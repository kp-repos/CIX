import json
import re
from pathlib import Path
from cix.cli import VOCAB_PATH, main
from cix.manifest import corpus_hash
from cix.normalize import load_corpus
from cix.scrub import load_privacy_protocol, scrub_corpus
from cix.store import build_store, open_store

REPEAT_TEXT = "still chasing the same unfixed problem from before"
DETERM_TEXT = "just need the account password reset"

class DetectorClient:
    """Deterministic scripted detector: labels are constant; a rubric hit fires iff the
    trigger text appears in the interaction body AND the item is listed in the prompt."""
    LABELS = json.dumps({"motion": "service", "intent": "x", "driver_origin": "customer",
                         "automatability": "rote", "outcome": "resolved", "handoff_events": []})
    def complete(self, prompt: str) -> str:
        if prompt.startswith("You are labeling"):
            return self.LABELS
        uid = re.search(r"<interaction id=([^>]+)>", prompt).group(1)
        hits = []
        if REPEAT_TEXT in prompt and "- repeat_contact_unresolved:" in prompt:
            hits.append({"item_id": "repeat_contact_unresolved", "snippet_ids": f"{uid}:0000"})
        if DETERM_TEXT in prompt and "- deterministic_request:" in prompt:
            hits.append({"item_id": "deterministic_request", "snippet_ids": f"{uid}:0000"})
        return json.dumps({"hits": hits})

def _unit(uid, text, thread=None):
    doc = {"id": uid, "source_type": "transcript", "participants": ["agent", "customer"],
           "segments": [{"speaker": "customer", "text": text}]}
    if thread:
        doc["thread_id"] = thread
    return doc

def _write_corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    docs = [
        _unit("s000", "opening a ticket about a stalled import", thread="TH1"),
        _unit("s001", REPEAT_TEXT + ", the import is stalled again", thread="TH1"),
        _unit("s002", REPEAT_TEXT + ", third week running", thread="TH1"),
        _unit("s003", DETERM_TEXT + " for the finance login"),
        _unit("s004", DETERM_TEXT + " for a new hire"),
        _unit("s005", DETERM_TEXT + " after a lockout"),
    ] + [_unit(f"s{i:03d}", "routine plan question, handled cleanly") for i in range(6, 12)]
    for d in docs:
        (corpus / f"{d['id']}.json").write_text(json.dumps(d), encoding="utf-8")
    return corpus

def _base_run(tmp_path: Path, corpus_dir: Path) -> Path:
    """Fabricate the base run the way `cix run` would persist it: scrubbed units, store,
    label+hit artifacts via the real _detect path with the scripted detector."""
    import cix.cli as cli
    from cix.rubric import load_rubric
    run = tmp_path / "base-run"
    run.mkdir()
    units = load_corpus(corpus_dir)
    proto = load_privacy_protocol(Path("configs/privacy_protocol_v1.yaml"))
    salt = "cix-test"
    units, _ = scrub_corpus(units, proto, salt=salt)
    build_store(units, VOCAB_PATH, run / "run.db")
    store = open_store(run / "run.db")
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    chash = corpus_hash(units)
    la, ha, hits, roll = cli._detect(store, units, rubric, DetectorClient(), chash, "1.0.0", "test-model")
    manifest = {"artifacts": {"labels": la, "hits": ha}, "corpus_hash": chash,
                "scrub_salt": salt, "label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0"}
    (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run

def test_differential_constructs_reruns_and_scores(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: DetectorClient())
    corpus = _write_corpus(tmp_path)
    run = _base_run(tmp_path, corpus)
    rc = main(["differential", str(run), "--corpus", str(corpus),
               "--rubric", "configs/service_rubric_v1.yaml"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["variants"] == 3 and out["failing"] == 0
    report = json.loads((run / "differential_report.json").read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in report["variants"]}
    # V1: 2 flagged repeat interactions exist; delete_count=3 caps at 2 -> expected -2, observed -2
    assert rows["V1-delete"]["expected"] == 2 and rows["V1-delete"]["observed"] == 2
    # V2: thread TH1 contributes 2 target interactions; duplicate -> +2 (copies carry same text)
    assert rows["V2-duplicate"]["expected"] == 2 and rows["V2-duplicate"]["observed"] == 2
    # V3: donor contributes 1; 5 copies -> +5
    assert rows["V3-splice"]["expected"] == 5 and rows["V3-splice"]["observed"] == 5
    store = open_store(run / "run.db")
    tdiff = [v for v in store.validations() if v["check"] == "T-DIFF"]
    assert len(tdiff) == 3 and all(v["status"] == "pass" for v in tdiff)
    # per-variant stores exist (real re-detection, not recounting)
    for vid in ("V1-delete", "V2-duplicate", "V3-splice"):
        assert (run / "differential" / vid / "run.db").exists()

def test_differential_refuses_on_corpus_mismatch(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: DetectorClient())
    corpus = _write_corpus(tmp_path)
    run = _base_run(tmp_path, corpus)
    # tamper: add one interaction after the base run -> corpus_hash mismatch
    (corpus / "s999.json").write_text(json.dumps(_unit("s999", "late addition")), encoding="utf-8")
    rc = main(["differential", str(run), "--corpus", str(corpus),
               "--rubric", "configs/service_rubric_v1.yaml"])
    assert rc == 2
    assert "corpus_hash mismatch" in capsys.readouterr().err

def test_differential_refuses_when_already_run(tmp_path, monkeypatch, capsys):
    """Fail fast on re-run: a stale differential/ dir would crash build_store mid-loop
    and duplicate T-DIFF rows, so refuse up front rather than leave incoherent state."""
    import cix.cli as cli
    monkeypatch.setattr(cli, "make_client", lambda cfg: DetectorClient())
    corpus = _write_corpus(tmp_path)
    run = _base_run(tmp_path, corpus)
    argv = ["differential", str(run), "--corpus", str(corpus),
            "--rubric", "configs/service_rubric_v1.yaml"]
    assert main(argv) == 0
    capsys.readouterr()                                  # drain the first run's stdout
    rc = main(argv)                                      # second run over the now-existing dir
    assert rc == 2
    assert "already exists" in capsys.readouterr().err
