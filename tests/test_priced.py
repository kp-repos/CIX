from pathlib import Path
from cix.catalogue import load_catalogue, join_swaps
from cix.priced import priced_view

CAT = Path("configs/catalogue_v0_1.yaml")
ROLL = {"seller_admin_burden": {"unit": "occurrence", "count": 12, "share": None, "denominator": None}}
CROSS = {"seller_admin_burden": "SW-ADMIN-CAPTURE"}

def test_priced_view_bands_no_totals():
    cat = load_catalogue(CAT)
    joined = join_swaps(ROLL, CROSS, cat)
    view = priced_view(joined["priced"])
    [play] = view["plays"]
    assert play["item_id"] == "seller_admin_burden"
    assert play["band"] == {"low": 12 * 40, "high": 12 * 120}       # count x per-unit band
    assert play["currency"] == "USD" and play["horizon"] == "per year"
    assert play["unit"] == "occurrence" and play["evidence_tier"] == "candidate"
    assert play["inferred"] is True and play["source"]
    assert "portfolio_total" not in view                            # R-PRC-1: no totals

def test_multi_remedy_shown_as_alternatives():
    cat = load_catalogue(CAT)
    priced = [
        {"item_id": "x", "count": 4, "unit": "occurrence", "entry": cat.by_id("SW-ADMIN-CAPTURE")},
        {"item_id": "x", "count": 4, "unit": "occurrence", "entry": cat.by_id("SW-STATUS-SELFSERVE")},
    ]
    view = priced_view(priced)
    xs = [p for p in view["plays"] if p["item_id"] == "x"]
    assert len(xs) == 1 and len(xs[0]["alternatives"]) == 2         # collapsed to alternatives
