import pytest
from cix.aggregate import UnitMixError, rollup

HITS = [
    {"item_id": "billing_defect_driver", "interaction_id": "i1", "unit": "interaction", "snippet_ids": "i1:0000"},
    {"item_id": "billing_defect_driver", "interaction_id": "i3", "unit": "interaction", "snippet_ids": "i3:0000"},
    {"item_id": "repeat_contact_unresolved", "interaction_id": "i1", "unit": "interaction", "snippet_ids": "i1:0002"},
    {"item_id": "transfer_or_escalation_event", "interaction_id": "i3", "unit": "occurrence", "snippet_ids": "i3:0001"},
]

def test_counts_shares_and_denominators():
    r = rollup(HITS, eligible_interactions=4)
    b = r["items"]["billing_defect_driver"]
    assert b["count"] == 2 and b["unit"] == "interaction"
    assert b["share"] == 0.5 and b["denominator"] == "4 eligible interactions"

def test_interaction_coverage():
    r = rollup(HITS, eligible_interactions=4)
    assert r["interaction_coverage"] == 0.5  # i1, i3 of 4 have >=1 hit
    assert r["residual_interactions"] == 2

def test_rank_within_unit_only():
    r = rollup(HITS, eligible_interactions=4)
    inter = [i for i, _ in r["rank_by_unit"]["interaction"]]
    assert inter[0] == "billing_defect_driver"
    assert "transfer_or_escalation_event" not in inter  # ranks never mix units

def test_cross_unit_sum_is_impossible():
    with pytest.raises(UnitMixError):
        rollup(HITS + [{"item_id": "billing_defect_driver", "interaction_id": "i2",
                        "unit": "occurrence", "snippet_ids": "i2:0000"}], eligible_interactions=4)
