from pathlib import Path
import yaml
from cix.rubric import load_rubric
from cix.briefing import load_presentation

RUBRIC = Path("configs/complaint_rubric_v1.yaml")
PRESENTATION = Path("configs/briefing_presentation_complaint_v1.yaml")

def test_complaint_rubric_loads_and_is_speaker_agnostic():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    assert r.version == "1.0.0"
    assert len(r.items) == 9
    assert all(i.requires_speaker is False for i in r.items)
    assert all(i.unit_of_count == "interaction" for i in r.items)
    assert len({i.id for i in r.items}) == 9

def test_complaint_rubric_polarity_split():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    positives = [i.id for i in r.items if i.polarity == "positive"]
    assert positives == ["resolution_acknowledged"]

def test_complaint_rubric_has_no_catalogue_refs_yet():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    assert all(i.swap_ref is None for i in r.items)    # honest empty plays state

def test_complaint_presentation_binds_to_complaint_rubric_file():
    cfg = load_presentation(PRESENTATION)
    assert cfg["requires"]["rubric_version"] == "1.0.0"
    assert cfg["requires"]["rubric_file"] == "complaint_rubric_v1.yaml"

def test_presentation_covers_every_rubric_item_and_metric_members_exist():
    r = load_rubric(RUBRIC, "1.0.0", "1.0.0")
    cfg = load_presentation(PRESENTATION)
    ids = {i.id for i in r.items}
    assert set(cfg["items"]) == ids
    m = cfg["headline_metrics"]["unremediated_loss_rate"]
    assert set(m["members"]) <= ids
    assert m["statement"]
    for iid, item in cfg["items"].items():
        rub = next(i for i in r.items if i.id == iid)
        assert item["polarity"] == rub.polarity        # polarity mirrors the rubric
