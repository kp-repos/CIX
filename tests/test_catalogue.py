from pathlib import Path
from cix.catalogue import load_catalogue

CAT = Path("configs/catalogue_v0_1.yaml")

def test_catalogue_loads_entries():
    cat = load_catalogue(CAT)
    assert cat.version == "0.1.0"
    ids = {e.id for e in cat.entries}
    assert "SW-ADMIN-CAPTURE" in ids
    e = cat.by_id("SW-ADMIN-CAPTURE")
    assert e.remedy_class == "A" and e.effort == "low" and e.outcome == "large"
    assert e.per_unit_band == [40, 120] and e.inferred is True

def test_unknown_id_returns_none():
    assert load_catalogue(CAT).by_id("NOPE") is None
