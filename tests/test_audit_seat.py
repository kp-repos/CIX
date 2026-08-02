import json
from pathlib import Path
from cix.audits import second_lab_audit
from cix.contracts import InteractionUnit
from cix.model import ScriptedClient
from cix.rubric import Rubric, RubricItem
from cix.second_lab import SecondLabConfig
from cix.store import build_store, open_store

VOCAB = Path("configs/tag_vocabulary_v1.yaml")

def _cfg(**over):
    base = dict(version="1.0.0", lab="openai", model="m", max_tokens=64,
                audit_sample_hits=4, agreement_floor=0.8, min_sample_for_validity=2)
    return SecondLabConfig(**(base | over))

def _setup(tmp_path, n_hits=4):
    units = [InteractionUnit(id=f"u-{i:03d}", source_type="transcript",
                             segments=[{"speaker": "rep", "text": f"Chasing legal on deal {i}."}])
             for i in range(6)]
    db = tmp_path / "run.db"
    build_store(units, VOCAB, db)
    store = open_store(db)
    la = store.ensure_label_artifact("c", "1.0.0", "m", "p")
    ha = store.ensure_hit_artifact(la, "1.0.0", "m", "p")
    for i in range(n_hits):
        store.write_hit(ha, "status_chasing", f"u-{i:03d}", "occurrence", f"u-{i:03d}:0000")
    rubric = Rubric(version="1.0.0", requires={"label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0"},
                    items=[RubricItem(id="status_chasing", description="d", polarity="negative",
                                      unit_of_count="occurrence", criterion="chasing a blocking answer", exemplars=[])])
    return store, units, rubric, ha

def test_f4_recusal_without_any_model_call(tmp_path):
    store, units, rubric, ha = _setup(tmp_path)
    r = second_lab_audit(store, units, rubric, ha, client2=None, cfg=_cfg(), seed=1,
                         provenance_lab="openai", seat_lab="openai")
    assert r["status"] == "recused_f4"                # client2 never touched: None is safe

def test_seat_agrees(tmp_path):
    store, units, rubric, ha = _setup(tmp_path)
    client = ScriptedClient(sequence=[json.dumps({"applies": True})] * 4)
    r = second_lab_audit(store, units, rubric, ha, client, _cfg(), seed=1,
                         provenance_lab=None, seat_lab="openai")
    assert r["status"] == "agree"

def test_seat_disagreement_flags(tmp_path):
    store, units, rubric, ha = _setup(tmp_path)
    client = ScriptedClient(sequence=[json.dumps({"applies": False})] * 4)
    r = second_lab_audit(store, units, rubric, ha, client, _cfg(), seed=1,
                         provenance_lab="anthropic-synthetic", seat_lab="openai")
    assert r["status"] == "disagree_flag"

def test_too_few_hits(tmp_path):
    store, units, rubric, ha = _setup(tmp_path, n_hits=1)
    r = second_lab_audit(store, units, rubric, ha, ScriptedClient(sequence=[]), _cfg(), seed=1,
                         provenance_lab=None, seat_lab="openai")
    assert r["status"] == "insufficient_power"

def test_none_provenance_proceeds_not_recused(tmp_path):
    # Security boundary: unknown/human provenance (None) must NOT recuse even when a
    # lab name is supplied for the seat — the seat proceeds to adjudicate.
    store, units, rubric, ha = _setup(tmp_path)
    client = ScriptedClient(sequence=[json.dumps({"applies": True})] * 4)
    r = second_lab_audit(store, units, rubric, ha, client, _cfg(), seed=1,
                         provenance_lab=None, seat_lab="openai")
    assert r["status"] != "recused_f4"
    assert r["status"] == "agree"
