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
