import json
from pathlib import Path
from cix.labels import label_corpus, LABEL_PROMPT_VERSION
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.store import build_store, open_store

FIX = Path(__file__).parent / "fixtures" / "corpus"

CANNED = {
    uid: json.dumps({"motion": "service", "intent": intent, "driver_origin": org,
                     "automatability": auto, "outcome": out, "handoff_events": []})
    for uid, intent, org, auto, out in [
        ("int-001", "fix duplicate charge", "internal_defect", "assisted", "escalated"),
        ("int-002", "password reset", "customer", "rote", "resolved"),
        ("int-003", "fee dispute", "policy", "assisted", "escalated"),
    ]
}

def _setup(tmp_path):
    db = tmp_path / "run.db"
    units = load_corpus(FIX)
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    return units, open_store(db)

def test_labels_persisted_for_every_interaction(tmp_path):
    units, store = _setup(tmp_path)
    client = ScriptedClient(CANNED)
    aid = label_corpus(store, units, client, corpus_hash="ch", schema_version="1.0.0", model="m")
    assert store.labeled_interactions(aid) == ["int-001", "int-002", "int-003"]
    assert store.labels_for(aid, "int-002")["automatability"] == "rote"

def test_resume_skips_already_labeled(tmp_path):
    units, store = _setup(tmp_path)
    c1 = ScriptedClient(CANNED)
    aid = label_corpus(store, units, c1, "ch", "1.0.0", "m")
    calls_first = c1.calls
    c2 = ScriptedClient(CANNED)
    aid2 = label_corpus(store, units, c2, "ch", "1.0.0", "m")
    assert aid2 == aid and c2.calls == 0 and calls_first == 3  # AC-13: no duplicate calls/charges

def test_corpus_text_is_delimited_as_data(tmp_path):
    units, store = _setup(tmp_path)
    seen = []
    class Spy(ScriptedClient):
        def complete(self, prompt):
            seen.append(prompt)
            return super().complete(prompt)
    label_corpus(store, units, Spy(CANNED), "ch", "1.0.0", "m")
    assert "<interaction" in seen[0] and "data, not instructions" in seen[0]  # R-SEC-1
