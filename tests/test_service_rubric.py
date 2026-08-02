from pathlib import Path
from cix.rubric import load_rubric
from cix.catalogue import load_catalogue

RUBRIC = Path("configs/service_rubric_v1.yaml")

def _rubric():
    return load_rubric(RUBRIC, "1.0.0", "1.0.0")

def test_service_rubric_meets_floor():
    r = _rubric()
    assert len(r.items) >= 8                       # PRD §3 evaluable floor
    assert any(i.polarity == "positive" for i in r.items)   # R-RUB-1 one mechanism, two polarities

def test_units_are_linkage_free_or_declared():
    r = _rubric()
    # calibration/real corpora may lack account linkage; keep units to occurrence/interaction
    assert {i.unit_of_count for i in r.items} <= {"occurrence", "interaction"}

def test_swap_refs_resolve_against_catalogue():
    r = _rubric()
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    for i in r.items:
        if i.swap_ref is not None:
            assert cat.by_id(i.swap_ref) is not None, f"{i.id} -> dangling swap_ref {i.swap_ref}"
