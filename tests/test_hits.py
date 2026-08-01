import json
from pathlib import Path
from cix.hits import run_rubric
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.rubric import load_rubric
from cix.store import build_store, open_store

FIX = Path(__file__).parent / "fixtures" / "corpus"

def _canned(uid, hits):
    return json.dumps({"hits": hits})

CANNED = {
    "int-001": _canned("int-001", [
        {"item_id": "repeat_contact_unresolved", "snippet_ids": "int-001:0002"},
        {"item_id": "billing_defect_driver", "snippet_ids": "int-001:0000"},
        {"item_id": "billing_defect_driver", "snippet_ids": "int-001:0001"},  # duplicate for dedup test
    ]),
    "int-002": _canned("int-002", [
        {"item_id": "deterministic_request_assisted", "snippet_ids": "int-002:0000"},
        {"item_id": "clean_first_contact_resolution", "snippet_ids": "int-002:0002"},
    ]),
    "int-003": _canned("int-003", [
        {"item_id": "billing_defect_driver", "snippet_ids": "int-003:0000"},
        {"item_id": "transfer_or_escalation_event", "snippet_ids": "int-003:0001"},
    ]),
}

def _setup(tmp_path):
    db = tmp_path / "run.db"
    units = load_corpus(FIX)
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    store = open_store(db)
    rubric = load_rubric(Path("configs/mini_rubric_v0.yaml"), "1.0.0", "1.0.0")
    la = store.ensure_label_artifact("ch", "1.0.0", "m", "p")
    return store, units, rubric, la

def test_interaction_unit_dedups_to_one_hit(tmp_path):
    store, units, rubric, la = _setup(tmp_path)
    ha = run_rubric(store, units, rubric, la, ScriptedClient(CANNED), model="m")
    billing = [h for h in store.hits_for(ha) if h["item_id"] == "billing_defect_driver"]
    assert [h["interaction_id"] for h in billing] == ["int-001", "int-003"]  # deduped per interaction

def test_occurrence_unit_keeps_each_event(tmp_path):
    store, units, rubric, la = _setup(tmp_path)
    ha = run_rubric(store, units, rubric, la, ScriptedClient(CANNED), model="m")
    occ = [h for h in store.hits_for(ha) if h["item_id"] == "transfer_or_escalation_event"]
    assert len(occ) == 1 and occ[0]["unit"] == "occurrence"

def test_prefiltered_item_only_asked_where_tag_present(tmp_path):
    store, units, rubric, la = _setup(tmp_path)
    prompts = []
    class Spy(ScriptedClient):
        def complete(self, prompt):
            prompts.append(prompt)
            return super().complete(prompt)
    run_rubric(store, units, rubric, la, Spy(CANNED), model="m")
    # int-002 has no repeat_marker or transfer_hold tags -> its prompt excludes those items
    p2 = next(p for p in prompts if "int-002" in p)
    assert "repeat_contact_unresolved" not in p2 and "transfer_or_escalation_event" not in p2

def test_unknown_item_id_in_response_is_rejected(tmp_path):
    store, units, rubric, la = _setup(tmp_path)
    bad = dict(CANNED)
    bad["int-002"] = json.dumps({"hits": [{"item_id": "not_in_rubric", "snippet_ids": "int-002:0000"}]})
    import pytest
    with pytest.raises(ValueError, match="not_in_rubric"):
        run_rubric(store, units, load_rubric(Path("configs/mini_rubric_v0.yaml"), "1.0.0", "1.0.0"),
                   la, ScriptedClient(bad), model="m")
