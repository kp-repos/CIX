import json
import sqlite3
from pathlib import Path
import pytest
from cix.briefing import load_presentation, avoidable_contact_rate, automatable_opportunity, build_briefing, render_briefing_html, render_briefing_pdf
from cix.cli import main

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


def _sections():
    return {
        "highlights": [
            {"item_id": "manual_after_call_work", "count": 87, "share": None, "unit": "occurrence", "evidence": []},
            {"item_id": "first_contact_resolution", "count": 82, "share": 0.82, "unit": "interaction", "evidence": []},
            {"item_id": "billing_defect_driver", "count": 19, "share": 0.19, "unit": "interaction", "evidence": []},
        ],
        "whats_working": [{"item_id": "first_contact_resolution", "narrative": "Resolved in one contact."}],
        "leverage": {
            "grid": _leverage_grid(),
            "shelf": [
                {"item_id": "first_contact_resolution", "count": 82, "unit": "interaction"},
                {"item_id": "unanticipated_failure", "count": 11, "unit": "interaction"},
                {"item_id": "status_chase_inbound", "count": 6, "unit": "interaction"},
            ],
            "class_d": [c for c in _leverage_grid() if c["remedy_class"] == "D"],
            "note": "catalogue 0.1.0",
        },
        "priced_plays": _priced_plays(),
        "distribution": {
            "items": {
                "manual_after_call_work": {"unit": "occurrence", "count": 87, "share": None},
                "first_contact_resolution": {"unit": "interaction", "count": 82, "share": 0.82},
                "billing_defect_driver": {"unit": "interaction", "count": 19, "share": 0.19},
                "deterministic_request": {"unit": "occurrence", "count": 19, "share": None},
                "avoidable_transfer": {"unit": "occurrence", "count": 9, "share": None},
                "unanticipated_failure": {"unit": "interaction", "count": 11, "share": 0.11},
                "status_chase_inbound": {"unit": "interaction", "count": 6, "share": 0.06},
            },
            "interaction_coverage": 1.0, "residual_interactions": 0, "eligible_interactions": 100,
        },
        "method": {
            "validations": [{"check": "T-DROP", "status": "pass"}, {"check": "T-PARA", "status": "not_run"}],
            "drop_summary": {"candidate_claims": 9, "quote_drops": 0, "stat_drops": 0},
        },
    }

def _manifest():
    return {"artifacts": {"hits": "ha"}, "rubric_version": "1.0.0", "catalogue_version": "0.1.0",
            "corpus_clearance": "synthetic service rehearsal corpus — O1 only, never O2/O3 (PRD §2.3)",
            "corpus_hash": "abc123"}

def _hits_rows():
    return [
        {"item_id": "billing_defect_driver", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "status_chase_inbound", "interaction_id": "int-1", "unit": "interaction"},
        {"item_id": "unanticipated_failure", "interaction_id": "int-2", "unit": "interaction"},
    ]

def test_build_briefing_blocks_route_correctly():
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    # meta banner
    assert "O1" in b["meta"]["corpus_clearance"]
    # headline metric ①: union of {int-1, int-2} = 2
    assert b["headline"]["avoidable_contact_rate"]["value"] == 2
    # headline metric ②: class-A band sum
    assert b["headline"]["automatable_opportunity"]["band"] == {"low": 4040.0, "high": 12120.0}
    # plays: class-A only, effort-ranked (low-effort first), with Monday action
    play_ids = [p["item_id"] for p in b["plays"]]
    assert play_ids == ["manual_after_call_work", "deterministic_request", "avoidable_transfer"]
    assert b["plays"][0]["label"] == "Manual after-call admin"
    assert b["plays"][0]["monday_action"] == "Capture at the interaction -> structured extraction"
    # upstream: class-D
    assert [u["item_id"] for u in b["upstream"]] == ["billing_defect_driver"]
    # watch_list: negative-polarity shelf only (config polarity) — positive first_contact_resolution excluded
    watch_ids = [w["item_id"] for w in b["watch_list"]]
    assert "first_contact_resolution" not in watch_ids
    assert set(watch_ids) == {"unanticipated_failure", "status_chase_inbound"}
    # whats_working: the positive
    assert b["whats_working"][0]["item_id"] == "first_contact_resolution"
    # trust: coverage + evidence-gap note (all highlights carry empty evidence)
    assert b["trust"]["coverage"]["interaction_coverage"] == 1.0
    assert "pending" in b["trust"]["evidence_note"].lower()

def test_build_briefing_unit_safety_guard_rejects_occurrence_member():
    cfg = load_presentation(PRESENTATION)
    sections = _sections()
    # Corrupt a member to an occurrence unit -> the interaction-only rate must refuse.
    sections["distribution"]["items"]["billing_defect_driver"]["unit"] = "occurrence"
    with pytest.raises(ValueError, match="interaction-unit"):
        build_briefing({"sections": sections}, _manifest(), cfg, _FakeStore(_hits_rows()))

def test_build_briefing_fails_closed_on_missing_swap_ref():
    cfg = load_presentation(PRESENTATION)
    sections = _sections()
    # A priced class-A play with no catalogue alternative -> the briefing must refuse,
    # not render a play without a Monday action (spec §3.3: missing swap fails closed).
    sections["priced_plays"]["plays"][0]["alternatives"] = []
    with pytest.raises(ValueError, match="swap"):
        build_briefing({"sections": sections}, _manifest(), cfg, _FakeStore(_hits_rows()))

def test_build_briefing_rejects_rubric_version_mismatch():
    cfg = load_presentation(PRESENTATION)
    manifest = _manifest()
    manifest["rubric_version"] = "2.0.0"  # config requires 1.0.0
    with pytest.raises(ValueError, match="rubric version"):
        build_briefing({"sections": _sections()}, manifest, cfg, _FakeStore(_hits_rows()))


def test_render_html_is_self_contained_and_shows_key_facts():
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    html = render_briefing_html(b)
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in html and "http://" not in html and "https://" not in html  # self-contained, no external assets
    assert "O1" in html                                   # honesty banner
    assert "Manual after-call admin" in html              # business label
    assert "Capture at the interaction" in html           # Monday action
    assert "2 / 100" in html or "2/100" in html           # avoidable-contact rate value
    assert "4,040" in html and "12,120" in html           # opportunity band, formatted
    assert "pending" in html.lower()                      # evidence-gap note


def test_render_pdf_writes_a_pdf_file(tmp_path):
    cfg = load_presentation(PRESENTATION)
    b = build_briefing({"sections": _sections()}, _manifest(), cfg, _FakeStore(_hits_rows()))
    html = render_briefing_html(b)
    out = tmp_path / "briefing.pdf"
    try:
        # render_briefing_pdf sets the macOS DYLD shim itself before importing weasyprint,
        # so this genuinely renders where the libs exist; skip only on true absence.
        render_briefing_pdf(html, out)
    except (OSError, ImportError) as e:
        import pytest
        pytest.skip(f"weasyprint/system libs unavailable: {e}")
    assert out.exists() and out.read_bytes()[:5] == b"%PDF-"


def test_cli_briefing_on_svc_run_golden(tmp_path):
    # Copy the persisted svc-run into a temp dir so we don't write into the repo fixture.
    import shutil
    src = Path("runs/svc-run")
    run = tmp_path / "svc-run"
    shutil.copytree(src, run)
    drops_before = sqlite3.connect(f"file:{run/'run.db'}?mode=ro", uri=True).execute(
        "SELECT count(*) FROM drop_log").fetchone()[0]

    rc = main(["briefing", str(run), "--no-pdf"])
    assert rc == 0

    briefing = json.loads((run / "briefing.json").read_text(encoding="utf-8"))
    assert briefing["headline"]["avoidable_contact_rate"]["value"] == 33
    assert briefing["headline"]["automatable_opportunity"]["band"] == {"low": 4040.0, "high": 12120.0}
    assert [p["item_id"] for p in briefing["plays"]] == [
        "manual_after_call_work", "deterministic_request", "avoidable_transfer"]
    assert "O1" in briefing["meta"]["corpus_clearance"]

    html = (run / "briefing.html").read_text(encoding="utf-8")
    assert "Manual after-call admin" in html and "33 / 100" in html

    # Read-only guarantee: drop_log unchanged.
    drops_after = sqlite3.connect(f"file:{run/'run.db'}?mode=ro", uri=True).execute(
        "SELECT count(*) FROM drop_log").fetchone()[0]
    assert drops_after == drops_before


def test_cli_briefing_no_pdf_skips_pdf(tmp_path):
    import shutil
    run = tmp_path / "svc-run"
    shutil.copytree(Path("runs/svc-run"), run)
    # svc-run ships a committed demo briefing.pdf; clear it so we test that --no-pdf
    # does not *produce* a PDF, not merely that the fixture lacks one.
    (run / "briefing.pdf").unlink(missing_ok=True)
    assert main(["briefing", str(run), "--no-pdf"]) == 0
    assert not (run / "briefing.pdf").exists()


def test_cli_briefing_missing_artifacts_fail_closed(tmp_path):
    # Spec §3.3: a dir without persisted artifacts fails closed with a message, no traceback.
    empty = tmp_path / "not-a-run"
    empty.mkdir()
    assert main(["briefing", str(empty), "--no-pdf"]) == 1
