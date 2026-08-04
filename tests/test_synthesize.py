import json
from pathlib import Path
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.store import build_store, open_store
from cix.synthesize import synthesize_findings

FIX = Path(__file__).parent / "fixtures" / "corpus"

ROLLUP = {"items": {"billing_defect_driver": {"unit": "interaction", "count": 2, "share": 0.6667,
                                              "denominator": "3 eligible interactions"}},
          "rank_by_unit": {"interaction": [("billing_defect_driver", 2)]},
          "interaction_coverage": 0.6667, "residual_interactions": 1, "eligible_interactions": 3}

CANNED = {"billing_defect_driver": json.dumps({
    "narrative": "Billing defects drive the largest share of contact volume.",
    "claimed_count": 2,
    "quotes": [{"interaction_id": "int-001", "start": 0, "end": 0,
                "text": "My card was charged twice for the same order."}],
    "mechanism": {"proposed": "duplicate charge processing defect",
                  "alternative": "customer misreading statements",
                  "discriminating_snippet_ids": ["int-001:0001"]},
})}

def _setup(tmp_path):
    db = tmp_path / "run.db"
    units = load_corpus(FIX)
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    store = open_store(db)
    hits = [{"item_id": "billing_defect_driver", "interaction_id": "int-001", "unit": "interaction",
             "snippet_ids": "int-001:0000"},
            {"item_id": "billing_defect_driver", "interaction_id": "int-003", "unit": "interaction",
             "snippet_ids": "int-003:0000"}]
    return store, hits

def test_synthesis_persisted_per_item(tmp_path):
    store, hits = _setup(tmp_path)
    sid = synthesize_findings(store, ROLLUP, hits, ScriptedClient(CANNED), model="m", seed=7)
    rows = store.synthesis_for(sid)
    assert len(rows) == 1
    body = json.loads(rows[0]["body"])
    assert body["claimed_count"] == 2
    assert body["mechanism"]["proposed"].startswith("duplicate")

def test_evidence_sample_is_seeded_and_stable(tmp_path):
    store, hits = _setup(tmp_path)
    prompts_a, prompts_b = [], []
    for bucket in (prompts_a, prompts_b):
        class Spy(ScriptedClient):
            def complete(self, prompt, _b=bucket):
                _b.append(prompt)
                return super().complete(prompt)
        synthesize_findings(store, ROLLUP, hits, Spy(CANNED), model="m", seed=7)
    assert prompts_a == prompts_b  # same seed -> identical evidence samples in prompts

def test_evidence_text_reaches_the_prompt(tmp_path):
    # Regression: snippet_ids of the shape "int-001:0000" (and ranges "id-id")
    # must resolve to real snippet text in the synthesis prompt. The old
    # split("-")[0] yielded "int" -> store.snippet(None) -> no evidence ever sent,
    # so every finding honestly came back with zero quotes.
    store, _ = _setup(tmp_path)
    captured = []
    class Spy(ScriptedClient):
        def complete(self, prompt):
            captured.append(prompt)
            return super().complete(prompt)
    hits = [{"item_id": "billing_defect_driver", "interaction_id": "int-001", "unit": "interaction",
             "snippet_ids": "int-001:0000"},
            {"item_id": "billing_defect_driver", "interaction_id": "int-001", "unit": "interaction",
             "snippet_ids": "int-001:0001-int-001:0002"}]
    synthesize_findings(store, ROLLUP, hits, Spy(CANNED), model="m", seed=7)
    prompt = "\n".join(captured)
    assert "My card was charged twice for the same order." in prompt          # single id
    assert "I can help with that. Let me check the billing record." in prompt  # first snippet of range

def test_missing_synthesis_field_raises_cleanly(tmp_path):
    # A live response that is valid JSON but omits a required field (e.g. the
    # mechanism block) must fail cleanly at synthesis, not crash later at the
    # gate/report with a KeyError after all model spend.
    import pytest
    store, hits = _setup(tmp_path)
    bad = {"billing_defect_driver": json.dumps({"narrative": "x", "claimed_count": 2, "quotes": []})}
    with pytest.raises(ValueError, match="mechanism"):
        synthesize_findings(store, ROLLUP, hits, ScriptedClient(bad), model="m", seed=7)
