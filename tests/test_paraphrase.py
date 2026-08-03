import json
from pathlib import Path
import pytest
import yaml
from cix.audits import paraphrase_audit
from cix.contracts import InteractionUnit
from cix.model import ScriptedClient
from cix.rubric import ParaphraseError, Rubric, RubricItem, load_paraphrase_set
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

# --- loader selection (load_paraphrase_set): pure file/dict logic, no model calls ---

def _write_para(dirpath, name, rubric_version, paras, rubric_file=None):
    doc = {"version": rubric_version, "rubric_version": rubric_version, "paraphrases": paras}
    if rubric_file is not None:
        doc["rubric_file"] = rubric_file
    (dirpath / name).write_text(yaml.safe_dump(doc), encoding="utf-8")

def _cfg_dir(tmp_path):
    # a fake configs/ dir holding a rubric file + paraphrase docs beside it
    d = tmp_path / "configs"
    d.mkdir()
    (d / "service_rubric_v1.yaml").write_text("version: '1.0.0'\n", encoding="utf-8")
    (d / "sales_rubric_v1.yaml").write_text("version: '1.1.0'\n", encoding="utf-8")
    return d

def test_loader_selects_service_set_by_version_and_file(tmp_path):
    d = _cfg_dir(tmp_path)
    _write_para(d, "paraphrases_v1.yaml", "1.1.0", {"seller_admin_burden": "S"})  # sales, no rubric_file
    _write_para(d, "paraphrases_service_v1.yaml", "1.0.0", {"repeat_contact_unresolved": "R"},
                rubric_file="service_rubric_v1.yaml")
    paras = load_paraphrase_set(d / "service_rubric_v1.yaml", "1.0.0")
    assert paras == {"repeat_contact_unresolved": "R"}

def test_loader_selects_sales_set_version_only_match(tmp_path):
    d = _cfg_dir(tmp_path)
    _write_para(d, "paraphrases_v1.yaml", "1.1.0", {"seller_admin_burden": "S"})  # no rubric_file
    _write_para(d, "paraphrases_service_v1.yaml", "1.0.0", {"repeat_contact_unresolved": "R"},
                rubric_file="service_rubric_v1.yaml")
    paras = load_paraphrase_set(d / "sales_rubric_v1.yaml", "1.1.0")
    assert paras == {"seller_admin_burden": "S"}

def test_loader_no_match_returns_empty(tmp_path):
    d = _cfg_dir(tmp_path)
    _write_para(d, "paraphrases_v1.yaml", "1.1.0", {"seller_admin_burden": "S"})
    # mini rubric at v0.1.0 — nothing covers it
    assert load_paraphrase_set(d / "service_rubric_v1.yaml", "0.1.0") == {}

def test_loader_ambiguous_match_raises(tmp_path):
    d = _cfg_dir(tmp_path)
    # two docs both claim rubric_version 1.0.0 with no binding file -> ambiguous
    _write_para(d, "paraphrases_a.yaml", "1.0.0", {"x": "A"})
    _write_para(d, "paraphrases_b.yaml", "1.0.0", {"x": "B"})
    with pytest.raises(ParaphraseError):
        load_paraphrase_set(d / "service_rubric_v1.yaml", "1.0.0")

def test_loader_wrong_rubric_file_excluded(tmp_path):
    d = _cfg_dir(tmp_path)
    # version matches but the doc is bound to a different rubric file -> excluded
    _write_para(d, "paraphrases_service_v1.yaml", "1.0.0", {"x": "R"},
                rubric_file="some_other_rubric.yaml")
    assert load_paraphrase_set(d / "service_rubric_v1.yaml", "1.0.0") == {}

def test_loader_matched_but_empty_paraphrases_raises(tmp_path):
    d = _cfg_dir(tmp_path)
    # doc claims the rubric (version + file) but carries no paraphrases -> broken instrument
    _write_para(d, "paraphrases_service_v1.yaml", "1.0.0", {}, rubric_file="service_rubric_v1.yaml")
    with pytest.raises(ParaphraseError):
        load_paraphrase_set(d / "service_rubric_v1.yaml", "1.0.0")

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
