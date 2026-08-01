import pytest
from pydantic import ValidationError
from cix.contracts import InteractionUnit, Segment

def test_valid_unit_parses():
    u = InteractionUnit(
        id="int-001", source_type="transcript",
        participants=["agent", "customer"], date="2026-05-01",
        account_id="acct-9", thread_id=None,
        segments=[{"speaker": "customer", "text": "My card was charged twice."}],
    )
    assert u.segments[0].speaker == "customer"
    assert u.thread_id is None

def test_source_type_restricted():
    with pytest.raises(ValidationError):
        InteractionUnit(id="x", source_type="carrier-pigeon", segments=[{"text": "hi"}])

def test_empty_segments_rejected():
    with pytest.raises(ValidationError):
        InteractionUnit(id="x", source_type="transcript", segments=[])

def test_segment_requires_text():
    with pytest.raises(ValidationError):
        Segment(speaker="agent")
