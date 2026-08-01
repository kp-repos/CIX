from pathlib import Path
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIX = Path(__file__).parent / "fixtures" / "corpus"

def _store(tmp_path):
    db = tmp_path / "run.db"
    build_store(load_corpus(FIX), Path("configs/tag_vocabulary_v1.yaml"), db)
    return open_store(db)

def test_label_artifact_key_excludes_rubric(tmp_path):
    s = _store(tmp_path)
    a1 = s.ensure_label_artifact(corpus_hash="ch", schema_version="1.0.0", model="m", prompts_hash="p")
    a2 = s.ensure_label_artifact(corpus_hash="ch", schema_version="1.0.0", model="m", prompts_hash="p")
    assert a1 == a2  # idempotent — same key, same artifact

def test_hit_artifact_keyed_by_label_artifact_and_rubric(tmp_path):
    s = _store(tmp_path)
    la = s.ensure_label_artifact("ch", "1.0.0", "m", "p")
    h1 = s.ensure_hit_artifact(la, rubric_version="0.1.0", model="m", prompts_hash="q")
    h2 = s.ensure_hit_artifact(la, rubric_version="0.2.0", model="m", prompts_hash="q")
    assert h1 != h2  # new rubric -> new hit artifact, same label artifact

def test_labels_and_hits_roundtrip(tmp_path):
    s = _store(tmp_path)
    la = s.ensure_label_artifact("ch", "1.0.0", "m", "p")
    s.write_labels(la, "int-001", {"motion": "service", "outcome": "escalated"})
    assert s.labels_for(la, "int-001")["motion"] == "service"
    assert s.labeled_interactions(la) == ["int-001"]
    ha = s.ensure_hit_artifact(la, "0.1.0", "m", "q")
    s.write_hit(ha, item_id="billing_defect_driver", interaction_id="int-001",
                unit="interaction", snippet_ids="int-001:0000")
    hits = s.hits_for(ha)
    assert hits[0]["item_id"] == "billing_defect_driver"

def test_validation_results_roundtrip(tmp_path):
    s = _store(tmp_path)
    s.write_validation("T-SPLIT", item_id=None, status="insufficient_power", detail="corpus<20")
    assert s.validations()[0]["check"] == "T-SPLIT"
