"""AC-6: service rubric hot-swaps with ZERO code changes, reusing the persisted label
artifact and creating a NEW hit artifact. AC-7: a catalogue swap regenerates only the
priced view — index/labels/hits untouched."""
import json
from pathlib import Path
from cix.contracts import InteractionUnit
from cix.store import build_store, open_store
from cix.model import ScriptedClient
from cix.rubric import load_rubric
from cix.labels import label_corpus
from cix.hits import run_rubric
from cix.catalogue import load_catalogue, join_swaps
from cix.priced import priced_view
from cix.manifest import corpus_hash

VOCAB = Path("configs/tag_vocabulary_v1.yaml")


def _units():
    return [InteractionUnit.model_validate(
        {"id": "i1", "source_type": "transcript", "participants": ["agent", "customer"],
         "segments": [{"speaker": "customer", "text": "third time calling about this charge"}]})]


def _label_client():
    # valid label JSON matching configs/label_schema_v1.yaml field names exactly
    return ScriptedClient(sequence=[json.dumps({
        "motion": "service", "intent": "complaint", "driver_origin": "internal_defect",
        "automatability": "exception", "outcome": "unresolved", "handoff_events": []})])


def _hit_client(item_id):
    return ScriptedClient(sequence=[json.dumps({"hits": [{"item_id": item_id, "snippet_ids": "i1:0000"}]})])


def test_ac6_rubric_swap_reuses_labels_new_hit_artifact(tmp_path):
    db = tmp_path / "run.db"
    units = _units()
    build_store(units, VOCAB, db)
    store = open_store(db)
    chash = corpus_hash(units)
    la = label_corpus(store, units, _label_client(), chash, "1.0.0", "test-model")

    # sales rubric is version 1.1.0; service rubric is version 1.0.0 — both require
    # label_schema_version 1.0.0 and tag_vocab_version 1.0.0
    sales = load_rubric(Path("configs/sales_rubric_v1.yaml"), "1.0.0", "1.0.0")
    service = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    ha_sales = run_rubric(store, units, sales, la, _hit_client("seller_admin_burden"), "test-model")
    ha_service = run_rubric(store, units, service, la, _hit_client("repeat_contact_unresolved"), "test-model")

    assert ha_sales != ha_service                     # different rubric version -> new hit artifact
    rows = store.con.execute("SELECT COUNT(*) c FROM label_artifacts").fetchone()["c"]
    assert rows == 1                                  # AC-6: labels reused, not recomputed
    # the service hit artifact is keyed off the REUSED label artifact, not a fresh one
    row = store.con.execute("SELECT label_artifact_id FROM hit_artifacts WHERE id=?", (ha_service,)).fetchone()
    assert row["label_artifact_id"] == la


def test_ac7_catalogue_swap_changes_priced_view_only():
    roll = {"manual_after_call_work": {"unit": "occurrence", "count": 6,
                                       "share": None, "denominator": None}}
    cross = {"manual_after_call_work": "SW-ADMIN-CAPTURE"}      # Class A, occurrence — priced
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    view1 = priced_view(join_swaps(roll, cross, cat)["priced"])
    cat2 = cat.model_copy(deep=True)
    cat2.by_id("SW-ADMIN-CAPTURE").per_unit_band = [100, 200]
    view2 = priced_view(join_swaps(roll, cross, cat2)["priced"])
    assert view1 != view2                                       # priced view regenerated
    assert roll["manual_after_call_work"]["count"] == 6         # rollup untouched
