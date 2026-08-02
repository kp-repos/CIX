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


# ---------------------------------------------------------------------------
# Task 6 — swap_ref join + unit-compat validation + leverage grid + shelf
# ---------------------------------------------------------------------------
from cix.catalogue import join_swaps, leverage_grid, UnitCompatError
import pytest

# rollup-shaped input: item_id -> {unit, count, share, denominator}
ROLL_ITEMS = {
    "seller_admin_burden": {"unit": "occurrence", "count": 12, "share": None, "denominator": None},
    "status_chasing": {"unit": "occurrence", "count": 5, "share": None, "denominator": None},
    "orphan_item": {"unit": "occurrence", "count": 3, "share": None, "denominator": None},
}
# rubric item -> swap_ref crosswalk
CROSS = {"seller_admin_burden": "SW-ADMIN-CAPTURE", "status_chasing": "SW-STATUS-SELFSERVE",
         "orphan_item": None}

def test_join_matches_and_shelves():
    cat = load_catalogue(CAT)
    joined = join_swaps(ROLL_ITEMS, CROSS, cat)
    matched = {j["item_id"] for j in joined["priced"]}
    assert matched == {"seller_admin_burden", "status_chasing"}
    assert [s["item_id"] for s in joined["shelf"]] == ["orphan_item"]  # no swap_ref -> shelf

def test_unit_incompatibility_fails_join():
    cat = load_catalogue(CAT)
    bad = {"x": {"unit": "interaction", "count": 2, "share": None, "denominator": None}}
    # SW-ADMIN-CAPTURE is unit_basis=occurrence; joining an interaction-unit item must fail
    with pytest.raises(UnitCompatError):
        join_swaps(bad, {"x": "SW-ADMIN-CAPTURE"}, cat)

def test_leverage_grid_ranks_and_names_class_d():
    cat = load_catalogue(CAT)
    joined = join_swaps(ROLL_ITEMS, CROSS, cat)
    grid = leverage_grid(joined["priced"], cat)
    # admin-capture (low effort, large outcome) outranks status (medium, medium)
    top = grid["cells"][0]
    assert top["item_id"] == "seller_admin_burden"
    assert "class_d" in grid  # class-D corner is named even if empty here
