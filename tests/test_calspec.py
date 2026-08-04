from pathlib import Path
import yaml
from cix.calgen import build_slots, load_cal_spec
from cix.rubric import load_rubric
from textcheck import ngrams

SPEC = Path("configs/calibration_spec_v1.yaml")

def test_spec_loads_and_crosswalk_targets_real_items():
    spec = load_cal_spec(SPEC)
    rubric = load_rubric(Path("configs/sales_rubric_v1.yaml"), "1.0.0", "1.0.0")
    item_ids = {i.id for i in rubric.items}
    assert {p.maps_to_item for p in spec.pathologies} <= item_ids
    assert len(spec.pathologies) >= 6
    assert spec.loudness_levels == ["loud", "moderate", "camouflaged"]

def test_vocabulary_disjointness():
    """R-VAL-2: plant author sees pathology descriptions, never rubric text.
    No pathology description shares a 5-token n-gram with any criterion, exemplar, or paraphrase."""
    spec = load_cal_spec(SPEC)
    rubric = load_rubric(Path("configs/sales_rubric_v1.yaml"), "1.0.0", "1.0.0")
    paras = yaml.safe_load(Path("configs/paraphrases_v1.yaml").read_text(encoding="utf-8"))["paraphrases"]
    rubric_text = " ".join(
        [i.criterion for i in rubric.items]
        + [e for i in rubric.items for e in i.exemplars]
        + list(paras.values())
    )
    for p in spec.pathologies:
        overlap = ngrams(p.description) & ngrams(rubric_text)
        assert not overlap, f"{p.key} shares wording with rubric text: {overlap}"

def test_split_shapes():
    spec = load_cal_spec(SPEC)
    dev = build_slots(spec, "dev")
    hold = build_slots(spec, "holdout")
    null = build_slots(spec, "null")
    planted = [s for s in dev if s["kind"] == "plant"]
    assert len(planted) == len(spec.pathologies) * 3 * spec.splits["dev"].instances_per_cell
    assert len(dev) == len(planted) + spec.splits["dev"].clean_interactions
    assert all(s["kind"] == "null" for s in null) and len(null) == spec.splits["null"].interactions
    assert len(hold) == len(dev)                      # same shape, different seed
    assert build_slots(spec, "dev") == dev            # deterministic per seed

def test_calgen_never_touches_rubric_code():
    """Collusion break, structural: the generator module must not import or read rubric machinery."""
    import cix.calgen
    src = Path(cix.calgen.__file__).read_text(encoding="utf-8")
    assert "rubric" not in src.lower()
