from pathlib import Path
import pytest
from cix.rubric import DependencyError, load_rubric

def test_rubric_loads_with_matching_deps():
    r = load_rubric(Path("configs/mini_rubric_v0.yaml"),
                    label_schema_version="1.0.0", tag_vocab_version="1.0.0")
    assert len(r.items) == 5
    assert r.items[0].prefilter == {"tag": "repeat_marker"}
    assert r.items[4].polarity == "positive"
    units = {i.unit_of_count for i in r.items}
    assert units == {"interaction", "occurrence"}

def test_loader_refuses_unmet_schema_dep():
    with pytest.raises(DependencyError, match="label_schema"):
        load_rubric(Path("configs/mini_rubric_v0.yaml"),
                    label_schema_version="2.0.0", tag_vocab_version="1.0.0")

def test_loader_refuses_unmet_vocab_dep():
    with pytest.raises(DependencyError, match="tag_vocab"):
        load_rubric(Path("configs/mini_rubric_v0.yaml"),
                    label_schema_version="1.0.0", tag_vocab_version="9.9.9")

def test_rubric_item_accepts_optional_swap_ref(tmp_path):
    import yaml
    from cix.rubric import load_rubric
    doc = {"version": "9.9.9",
           "requires": {"label_schema_version": "1.0.0", "tag_vocab_version": "1.0.0"},
           "items": [{"id": "x", "description": "d", "polarity": "negative",
                      "unit_of_count": "occurrence", "criterion": "c", "swap_ref": "SW-1"}]}
    p = tmp_path / "r.yaml"; p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    r = load_rubric(p, "1.0.0", "1.0.0")
    assert r.items[0].swap_ref == "SW-1"

def test_swap_ref_defaults_to_none_for_existing_rubrics():
    from cix.rubric import load_rubric
    from pathlib import Path
    r = load_rubric(Path("configs/sales_rubric_v1.yaml"), "1.0.0", "1.0.0")
    assert all(i.swap_ref is None for i in r.items)   # G3 sales rubric omits it, still loads
