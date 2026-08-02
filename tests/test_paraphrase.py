import json
from pathlib import Path
from cix.audits import paraphrase_audit
from cix.contracts import InteractionUnit
from cix.model import ScriptedClient
from cix.rubric import Rubric, RubricItem
from cix.store import build_store, open_store

VOCAB = Path("configs/tag_vocabulary_v1.yaml")
CFG = {"sample_top_items": 1, "sample_rare_items": 1, "rare_max_count": 2,
       "judgments_per_item": 4, "min_sample_for_validity": 2, "disagreement_floor": 0.2}

def _setup(tmp_path, n_hits):
    units = [InteractionUnit(id=f"u-{i:03d}", source_type="transcript",
                             segments=[{"speaker": "rep", "text": f"Chasing legal again on deal {i}."}])
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
                                      unit_of_count="occurrence", criterion="ORIGINAL CRITERION", exemplars=[])])
    return store, units, rubric, ha

def test_agreement_is_stable(tmp_path):
    store, units, rubric, ha = _setup(tmp_path, 4)
    client = ScriptedClient(sequence=[json.dumps({"applies": True})] * 8)   # 4 hits x paired
    [r] = paraphrase_audit(store, units, rubric, {"status_chasing": "PARAPHRASED"}, ha, client, CFG, seed=1)
    assert r["item_id"] == "status_chasing" and r["status"] == "stable"

def test_disagreement_marks_not_a_measurement(tmp_path):
    store, units, rubric, ha = _setup(tmp_path, 4)
    client = ScriptedClient(sequence=[json.dumps({"applies": True}), json.dumps({"applies": False})] * 4)
    [r] = paraphrase_audit(store, units, rubric, {"status_chasing": "PARAPHRASED"}, ha, client, CFG, seed=1)
    assert r["status"] == "not_a_measurement"

def test_too_few_hits_reports_insufficient_power(tmp_path):
    store, units, rubric, ha = _setup(tmp_path, 1)
    [r] = paraphrase_audit(store, units, rubric, {"status_chasing": "PARAPHRASED"}, ha,
                           ScriptedClient(sequence=[]), CFG, seed=1)
    assert r["status"] == "insufficient_power"

def test_no_paraphrase_coverage_reports_not_run(tmp_path):
    store, units, rubric, ha = _setup(tmp_path, 4)
    [r] = paraphrase_audit(store, units, rubric, {}, ha, ScriptedClient(sequence=[]), CFG, seed=1)
    assert r["status"] == "not_run"

def test_rare_item_path(tmp_path):
    # top item (status_chasing, 4 hits) has NO paraphrase -> excluded from chosen;
    # rare item (seller_admin_burden, 2 hits) HAS a paraphrase -> selected via the rare branch
    units = [InteractionUnit(id=f"u-{i:03d}", source_type="transcript",
                             segments=[{"speaker": "rep", "text": f"Admin work on deal {i}."}])
             for i in range(6)]
    db = tmp_path / "run.db"
    build_store(units, VOCAB, db)
    store = open_store(db)
    la = store.ensure_label_artifact("c", "1.0.0", "m", "p")
    ha = store.ensure_hit_artifact(la, "1.0.0", "m", "p")
    for i in range(4):
        store.write_hit(ha, "status_chasing", f"u-{i:03d}", "occurrence", f"u-{i:03d}:0000")
    for i in range(2):
        store.write_hit(ha, "seller_admin_burden", f"u-{i:03d}", "occurrence", f"u-{i:03d}:0000")
    rubric = Rubric(version="1.0.0", requires={"label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0"},
                    items=[RubricItem(id="status_chasing", description="d", polarity="negative",
                                      unit_of_count="occurrence", criterion="C1", exemplars=[]),
                           RubricItem(id="seller_admin_burden", description="d", polarity="negative",
                                      unit_of_count="occurrence", criterion="C2", exemplars=[])])
    client = ScriptedClient(sequence=[json.dumps({"applies": True})] * 8)
    results = paraphrase_audit(store, units, rubric, {"seller_admin_burden": "PARA"}, ha, client, CFG, seed=1)
    assert {r["item_id"] for r in results} == {"seller_admin_burden"}   # only the rare item, via the rare branch
    assert results[0]["status"] == "stable"
