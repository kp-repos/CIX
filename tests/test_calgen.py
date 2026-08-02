import json
from pathlib import Path
import yaml
from cix.calgen import build_slots, generate_corpus, load_cal_spec
from cix.model import ScriptedClient
from cix.normalize import load_corpus

SPEC = Path("configs/calibration_spec_v1.yaml")

def _mini_spec(tmp_path: Path) -> Path:
    doc = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    doc["pathologies"] = doc["pathologies"][:1]          # P1 only
    doc["splits"] = {
        "dev": {"id_prefix": "t-dev", "seed": 7, "instances_per_cell": 1, "clean_interactions": 1},
        "null": {"id_prefix": "t-null", "seed": 8, "interactions": 2},
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p

def _canned(n: int) -> ScriptedClient:
    seg = json.dumps({"segments": [{"speaker": "rep", "text": "Morning, quick one on the Harmon account."},
                                   {"speaker": "customer", "text": "Sure, go ahead."}]})
    return ScriptedClient(sequence=[seg] * n)

def test_generate_dev_split(tmp_path):
    spec = load_cal_spec(_mini_spec(tmp_path))
    out = tmp_path / "dev"
    truth = generate_corpus(spec, "dev", _canned(4), out, model_name="test-model", lab="openai")
    # 1 pathology x 3 loudness x 1 + 1 clean = 4 interactions
    units = load_corpus(out / "corpus")                  # truth/provenance must not break loading
    assert len(units) == 4
    assert len(truth) == 4
    planted = {k: v for k, v in truth.items() if v}
    assert len(planted) == 3
    assert {v["loudness"] for v in planted.values()} == {"loud", "moderate", "camouflaged"}
    assert all(v["pathology"] == "P1" for v in planted.values())
    prov = yaml.safe_load((out / "provenance.yaml").read_text(encoding="utf-8"))
    assert prov["generator_lab"] == "openai"
    assert prov["generator_model"] == "test-model"
    on_disk = json.loads((out / "truth.json").read_text(encoding="utf-8"))
    assert on_disk == truth

def test_generate_null_split(tmp_path):
    spec = load_cal_spec(_mini_spec(tmp_path))
    out = tmp_path / "null"
    truth = generate_corpus(spec, "null", _canned(2), out, model_name="test-model", lab="openai")
    assert len(truth) == 2 and all(v is None for v in truth.values())

def test_prompts_never_contain_rubric_text(tmp_path):
    """Firewall check at the prompt level: capture every generation prompt, assert no criterion string."""
    from cix.rubric import load_rubric   # imported in the TEST, never in calgen
    spec = load_cal_spec(_mini_spec(tmp_path))
    rubric = load_rubric(Path("configs/sales_rubric_v1.yaml"), "1.0.0", "1.0.0")
    seen: list[str] = []
    class Spy(ScriptedClient):
        def complete(self, prompt: str) -> str:
            seen.append(prompt)
            return super().complete(prompt)
    generate_corpus(spec, "dev", Spy(sequence=_canned(4).sequence), tmp_path / "o", "m", "openai")
    for prompt in seen:
        for item in rubric.items:
            assert item.criterion not in prompt
            for e in item.exemplars:
                assert e not in prompt
