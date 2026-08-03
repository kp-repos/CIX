import json
from pathlib import Path
import yaml
from cix.model import ScriptedClient
from cix.normalize import load_corpus
from cix.servicegen import generate_service_corpus, load_service_spec

SPEC = Path("configs/service_corpus_spec_v1.yaml")

def _mini_spec(tmp_path: Path) -> Path:
    doc = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    doc["threads"] = [{"key": "TH1", "pathology": "SP1", "interactions": 3,
                       "issue": "a data import job that stalls partway"}]
    doc["singles"] = [{"pathology": "SP3", "count": 1}]
    doc["clean_interactions"] = 2
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p

def _canned(n: int) -> ScriptedClient:
    seg = json.dumps({"segments": [
        {"speaker": "agent", "text": "Thanks for calling, what can I do for you?"},
        {"speaker": "customer", "text": "Quick one about our account."}]})
    return ScriptedClient(sequence=[seg] * n)

def test_generate_mini_corpus(tmp_path):
    spec = load_service_spec(_mini_spec(tmp_path))
    out = tmp_path / "svc"
    truth = generate_service_corpus(spec, _canned(6), out, model_name="test-model", lab="openai")
    units = load_corpus(out / "corpus")                  # truth/provenance must not break loading
    assert len(units) == 6 and len(truth) == 6
    threaded = [u for u in units if u.thread_id is not None]
    assert len(threaded) == 3
    assert {u.thread_id for u in threaded} == {"svc-TH1"}
    assert all(u.account_id == "acct-TH1" for u in threaded)
    planted = {k: v for k, v in truth.items() if v}
    # thread contacts 2..3 plant SP1, plus the SP3 single = 3 plants
    assert len(planted) == 3
    assert sorted(v["pathology"] for v in planted.values()) == ["SP1", "SP1", "SP3"]
    assert sum(1 for v in planted.values() if v["thread"] == "TH1") == 2
    prov = yaml.safe_load((out / "provenance.yaml").read_text(encoding="utf-8"))
    assert prov["generator_lab"] == "openai"
    assert prov["generator_model"] == "test-model"
    assert prov["spec_version"] == spec.version
    on_disk = json.loads((out / "truth.json").read_text(encoding="utf-8"))
    assert on_disk == truth

def test_thread_prompts_carry_continuity(tmp_path):
    """Contact k>1 prompts name the ongoing issue and the contact number; contact 1 sets it up."""
    spec = load_service_spec(_mini_spec(tmp_path))
    seen: list[str] = []
    class Spy(ScriptedClient):
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return super().complete(prompt)
    generate_service_corpus(spec, Spy(sequence=_canned(6).sequence), tmp_path / "o", "m", "openai")
    thread_prompts = [p for p in seen if "ongoing chain" in p]
    assert len(thread_prompts) == 3
    assert sum(1 for p in thread_prompts if "contact 1 " in p) == 1
    assert all("a data import job that stalls partway" in p for p in thread_prompts)

def test_prompts_never_contain_a9_text(tmp_path):
    """Firewall at the prompt level: no A9 criterion or exemplar string in any generation prompt."""
    from cix.rubric import load_rubric   # imported in the TEST, never in servicegen
    spec = load_service_spec(_mini_spec(tmp_path))
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    seen: list[str] = []
    class Spy(ScriptedClient):
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return super().complete(prompt)
    generate_service_corpus(spec, Spy(sequence=_canned(6).sequence), tmp_path / "o", "m", "openai")
    for prompt in seen:
        for item in rubric.items:
            assert item.criterion not in prompt
            for e in item.exemplars:
                assert e not in prompt
