import json
from pathlib import Path
import pytest
from cix.briefing import load_presentation, avoidable_contact_rate, automatable_opportunity

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


def _leverage_grid():
    return [
        {"item_id": "manual_after_call_work", "effort": "low", "outcome": "large", "count": 87, "remedy_class": "A"},
        {"item_id": "deterministic_request", "effort": "medium", "outcome": "medium", "count": 19, "remedy_class": "A"},
        {"item_id": "avoidable_transfer", "effort": "medium", "outcome": "medium", "count": 9, "remedy_class": "A"},
        {"item_id": "billing_defect_driver", "effort": "high", "outcome": "large", "count": 19, "remedy_class": "D"},
    ]

def _priced_plays():
    return {"plays": [
        {"item_id": "manual_after_call_work", "band": {"low": 3480.0, "high": 10440.0},
         "alternatives": [{"swap_ref": "SW-ADMIN-CAPTURE",
                           "substitute": "Capture at the interaction -> structured extraction"}]},
        {"item_id": "deterministic_request", "band": {"low": 380.0, "high": 1140.0},
         "alternatives": [{"swap_ref": "SW-STATUS-SELFSERVE",
                           "substitute": "Self-service status + automated routing"}]},
        {"item_id": "avoidable_transfer", "band": {"low": 180.0, "high": 540.0},
         "alternatives": [{"swap_ref": "SW-STATUS-SELFSERVE",
                           "substitute": "Self-service status + automated routing"}]},
    ]}

def test_automatable_opportunity_sums_class_a_bands_with_caveats():
    m = automatable_opportunity(_leverage_grid(), _priced_plays())
    assert m["band"] == {"low": 4040.0, "high": 12120.0}
    assert m["inferred"] is True
    assert m["evidence_tier"] == "candidate"
    # Two class-A plays share SW-STATUS-SELFSERVE -> shared-remedy note present.
    assert "SW-STATUS-SELFSERVE" in m["shared_remedy_note"]

def test_automatable_opportunity_absent_without_catalogue():
    assert automatable_opportunity(_leverage_grid(), {"plays": []}) is None
