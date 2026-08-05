import json
from pathlib import Path
import pytest
from cix.briefing import load_presentation

PRESENTATION = Path("configs/briefing_presentation_v1.yaml")

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
