import json
from pathlib import Path
import pytest
from cix.briefing import load_presentation, avoidable_contact_rate

PRESENTATION = Path("configs/briefing_presentation_v1.yaml")

class _FakeStore:
    """Minimal stand-in for cix.store.Store.hits_for."""
    def __init__(self, rows):
        self._rows = rows  # list of {"item_id":..., "interaction_id":..., "unit":...}
    def hits_for(self, artifact_id):
        return list(self._rows)

def test_avoidable_contact_rate_is_a_distinct_union_not_a_sum():
    # Overlap: int-1 matches TWO members; naive sum=3, distinct union=2.
    rows = [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "status_chase_inbound", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "repeat_contact_unresolved", "interaction_id": "int-2", "unit": "interaction"},
    ]
    members = ["repeat_contact_unresolved", "billing_defect_driver",
               "status_chase_inbound", "unanticipated_failure"]
    m = avoidable_contact_rate(_FakeStore(rows), "ha", members, eligible=100)
    assert m["value"] == 2                     # union, not 3
    assert m["denominator"] == 100
    assert m["share"] == 0.02
    assert m["members"] == members

def test_avoidable_contact_rate_ignores_non_member_and_non_interaction_hits():
    rows = [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "manual_after_call_work", "interaction_id": "int-9", "unit": "occurrence"},   # not a member
        {"item_id": "unanticipated_failure", "interaction_id": "int-3", "unit": "occurrence"},    # member but occurrence-unit row -> structurally excluded
    ]
    members = ["repeat_contact_unresolved", "billing_defect_driver",
               "status_chase_inbound", "unanticipated_failure"]
    m = avoidable_contact_rate(_FakeStore(rows), "ha", members, eligible=100)
    assert m["value"] == 1
    assert sorted(m["interaction_ids"]) == ["int-1"]

def test_load_presentation_has_versions_items_and_metric_members():
    cfg = load_presentation(PRESENTATION)
    assert cfg["version"] == "1.0.0"
    assert cfg["requires"]["rubric_version"] == "1.0.0"
    assert cfg["items"]["manual_after_call_work"]["business_label"] == "Manual after-call admin"
    assert cfg["items"]["manual_after_call_work"]["polarity"] == "negative"
    assert cfg["items"]["first_contact_resolution"]["polarity"] == "positive"
    assert cfg["headline_metrics"]["avoidable_contact_rate"]["members"] == [
        "repeat_contact_unresolved", "billing_defect_driver",
        "status_chase_inbound", "unanticipated_failure",
    ]
