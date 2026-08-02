from pathlib import Path
import yaml
from cix.rubric import load_rubric

RUBRIC = Path("configs/sales_rubric_v1.yaml")
PARAS = Path("configs/paraphrases_v1.yaml")

def _rubric():
    return load_rubric(RUBRIC, label_schema_version="1.0.0", tag_vocab_version="1.0.0")

def test_sales_rubric_meets_g3_floor():
    r = _rubric()
    assert len(r.items) >= 8                       # PRD §3 evaluable floor
    assert any(i.polarity == "positive" for i in r.items)
    assert any(i.prefilter for i in r.items)       # T-ESC has something to audit

def test_units_are_linkage_free():
    r = _rubric()
    assert {i.unit_of_count for i in r.items} <= {"occurrence", "interaction"}

def test_paraphrase_set_covers_rubric():
    r = _rubric()
    doc = yaml.safe_load(PARAS.read_text(encoding="utf-8"))
    assert doc["rubric_version"] == r.version
    paras = doc["paraphrases"]
    for item in r.items:
        assert item.id in paras
        assert paras[item.id].strip() and paras[item.id].strip() != item.criterion.strip()
