import json
from pathlib import Path
from cix.report import render_report

def _payload(findings):
    return {
        "findings": findings,
        "rollup": {"items": {}, "rank_by_unit": {}, "interaction_coverage": 0.5,
                   "residual_interactions": 2, "eligible_interactions": 4},
        "validations": [{"check": "T-SPLIT", "item_id": None, "status": "insufficient_power", "detail": "n<20"}],
        "drop_summary": {"candidate_claims": 8, "quote_drops": 0, "stat_drops": 1},
        "manifest": {"canonical_hash": "abc", "rubric_version": "0.1.0", "privacy_gate": "synthetic-fixture"},
        "catalogue_loaded": False,
    }

FINDING = {"item_id": "billing_defect_driver", "mechanism_status": "undischarged",
           "body": {"narrative": "Billing defects dominate.", "claimed_count": 2,
                    "quotes": [{"interaction_id": "int-001", "start": 0, "end": 0, "text": "q"}],
                    "mechanism": {"proposed": "p", "alternative": "a", "discriminating_snippet_ids": []}},
           "polarity": "negative", "unit": "interaction", "share": 0.5,
           "denominator": "4 eligible interactions"}

def test_report_files_written_and_agree(tmp_path):
    out = render_report(_payload([FINDING]), tmp_path)
    assert (tmp_path / "report.pdf").exists()
    data = json.loads((tmp_path / "report.json").read_text())
    assert data["sections"]["highlights"][0]["item_id"] == "billing_defect_driver"
    assert data["sections"]["highlights"][0]["mechanism_status"] == "undischarged"
    assert data["sections"]["priced_plays"]["note"].startswith("No catalogue loaded")
    assert data["manifest"]["canonical_hash"] == "abc"

def test_no_findings_still_renders_honest_report(tmp_path):
    render_report(_payload([]), tmp_path)
    data = json.loads((tmp_path / "report.json").read_text())
    assert data["sections"]["highlights"] == []
    assert data["sections"]["distribution"]["interaction_coverage"] == 0.5  # AC-12

def test_render_makes_no_model_calls(tmp_path):
    # render_report accepts only data; there is no client parameter to call (AC-15 by construction)
    import inspect
    from cix.report import render_report as rr
    assert "client" not in inspect.signature(rr).parameters

def test_report_renders_priced_and_grid_when_catalogue_loaded(tmp_path):
    from cix.report import render_report
    payload = {
        "findings": [], "rollup": {"items": {}, "rank_by_unit": {}, "interaction_coverage": None,
                                   "residual_interactions": 0, "eligible_interactions": 0},
        "validations": [], "drop_summary": {"candidate_claims": 0, "quote_drops": 0, "stat_drops": 0},
        "manifest": {"manifest_version": "1.0.0"},
        "catalogue_loaded": True,
        "priced_plays": {"plays": [{"item_id": "x", "band": {"low": 1, "high": 2}}], "note": None},
        "leverage": {"grid": [{"item_id": "x"}], "shelf": [], "class_d": [],
                     "note": "catalogue loaded"},
    }
    doc = render_report(payload, tmp_path)
    assert doc["sections"]["priced_plays"]["plays"][0]["item_id"] == "x"
    assert doc["sections"]["leverage"]["grid"][0]["item_id"] == "x"
