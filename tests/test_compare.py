import pytest
from cix.compare import build_compare, reveal_block, render_compare_html

class _FakeStore:
    def __init__(self, rows):
        self._rows = rows
    def hits_for(self, artifact_id):
        return list(self._rows)

def _cfg():
    return {"version": "1.0.0", "requires": {"rubric_version": "1.0.0"},
            "items": {"remediation_denied": {"business_label": "Refunds refused",
                                             "gloss": "g", "polarity": "negative"},
                      "fee_dispute": {"business_label": "Disputed fees",
                                      "gloss": "g", "polarity": "negative"}},
            "headline_metrics": {"unremediated_loss_rate": {
                "members": ["remediation_denied"],
                "statement": "complaints described losing money without remedy"}}}

def _report(eligible, items):
    # items: {item_id: (count, share)}
    dist = {i: {"count": c, "share": s, "unit": "interaction",
                "denominator": eligible} for i, (c, s) in items.items()}
    return {"sections": {
        "distribution": {"items": dist, "eligible_interactions": eligible,
                         "interaction_coverage": 1.0, "residual_interactions": 0},
        "leverage": {"grid": [], "shelf": [], "class_d": [], "note": ""},
        "priced_plays": {"plays": [], "note": "no catalogue"},
        "method": {"validations": [], "drop_summary": {}},
        "highlights": [], "whats_working": []}}

def _manifest(name):
    return {"rubric_version": "1.0.0", "rubric_file": "complaint_rubric_v1.yaml",
            "corpus_clearance": f"CFPB public domain — internal O2 track ({name})",
            "corpus_hash": f"hash-{name}", "catalogue_version": None,
            "substrate_class": "S2", "artifacts": {"hits": "ha"}}

def _side(name, eligible, items, hit_rows):
    return {"name": name, "report": _report(eligible, items),
            "manifest": _manifest(name), "store": _FakeStore(hit_rows)}

def _two_sides():
    a = _side("Block, Inc.", 100,
              {"remediation_denied": (40, 0.40), "fee_dispute": (10, 0.10)},
              [{"item_id": "remediation_denied", "interaction_id": f"i{k}",
                "unit": "interaction"} for k in range(40)])
    b = _side("Bank of America", 100,
              {"remediation_denied": (5, 0.05), "fee_dispute": (20, 0.20)},
              [{"item_id": "remediation_denied", "interaction_id": f"j{k}",
                "unit": "interaction"} for k in range(5)])
    return a, b

def test_build_compare_headline_and_ratio():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    m = c["headline"]["unremediated_loss_rate"]
    assert m["a"]["value"] == 40 and m["b"]["value"] == 5
    assert m["ratio"] == 8.0                      # a.share / b.share
    assert c["meta"]["a"]["name"] == "Block, Inc."
    assert c["meta"]["substrate_class"] == "S2"

def test_build_compare_rank_order_and_divergence():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    ranks_a = [r["item_id"] for r in c["rank_order"]["a"]]
    ranks_b = [r["item_id"] for r in c["rank_order"]["b"]]
    assert ranks_a == ["remediation_denied", "fee_dispute"]
    assert ranks_b == ["fee_dispute", "remediation_denied"]
    top = c["divergence"]["rows"][0]
    assert top["item_id"] == "remediation_denied"
    assert top["share_a"] == 0.40 and top["share_b"] == 0.05
    assert c["divergence"]["total"] >= 1
    assert top["label"] == "Refunds refused"

def test_build_compare_fails_closed_on_rubric_mismatch():
    a, b = _two_sides()
    b["manifest"]["rubric_version"] = "2.0.0"
    with pytest.raises(ValueError, match="rubric"):
        build_compare(a, b, _cfg())

def test_driver_rates_exclude_unit_mismatch_with_note():
    a, b = _two_sides()
    b["report"]["sections"]["distribution"]["items"]["fee_dispute"]["unit"] = "occurrence"
    c = build_compare(a, b, _cfg())
    ids = [r["item_id"] for r in c["driver_rates"]["rows"]]
    assert "fee_dispute" not in ids
    assert any("fee_dispute" in n for n in c["driver_rates"]["excluded"])

def test_reveal_block_computes_relief_rates_and_banner():
    labels_a = {"i1": "Closed with monetary relief", "i2": "Closed with explanation",
                "i3": "Closed with explanation", "i4": "Closed with explanation"}
    labels_b = {"j1": "Closed with monetary relief", "j2": "Closed with monetary relief"}
    r = reveal_block(labels_a, labels_b)
    assert r["a"]["monetary_relief_rate"] == 0.25
    assert r["b"]["monetary_relief_rate"] == 1.0
    assert "never seen by the model" in r["banner"]
    assert r["a"]["n"] == 4 and r["a"]["responses"]["Closed with explanation"] == 3

def test_render_compare_html_contains_banner_names_and_reveal():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())
    c["reveal"] = reveal_block({"i1": "Closed with monetary relief"},
                               {"j1": "Closed with explanation"})
    html = render_compare_html(c)
    assert "Block, Inc." in html and "Bank of America" in html
    assert "never seen by the model" in html
    assert "S2" in html                            # substrate banner

def test_render_compare_html_without_reveal_states_absence():
    a, b = _two_sides()
    c = build_compare(a, b, _cfg())                # no reveal key set
    html = render_compare_html(c)
    assert "reveal not run" in html.lower()

def test_ratio_none_on_zero_share_and_reveal_n_zero():
    # B side: remediation_denied has share 0 -> headline metric member share falsy
    # -> headline ratio is None; driver row share_b == 0 -> row ratio is None ("—").
    a = _side("Block, Inc.", 100,
              {"remediation_denied": (40, 0.40), "fee_dispute": (10, 0.10)},
              [{"item_id": "remediation_denied", "interaction_id": f"i{k}",
                "unit": "interaction"} for k in range(40)])
    b = _side("Bank of America", 100,
              {"remediation_denied": (0, 0.0), "fee_dispute": (20, 0.20)},
              [])  # no remediation_denied hits -> share_b 0
    c = build_compare(a, b, _cfg())
    assert c["headline"]["unremediated_loss_rate"]["ratio"] is None
    row = next(r for r in c["driver_rates"]["rows"]
               if r["item_id"] == "remediation_denied")
    assert row["ratio"] is None
    html = render_compare_html(c)                   # renders without error
    assert "—" in html
    # reveal with no labels: each side monetary_relief_rate None and n == 0
    rev = reveal_block({}, {})
    assert rev["a"]["monetary_relief_rate"] is None and rev["a"]["n"] == 0
    assert rev["b"]["monetary_relief_rate"] is None and rev["b"]["n"] == 0

import json as _json
import sqlite3
from pathlib import Path
from cix.cli import main as cli_main

def test_compare_cli_on_committed_run_no_reveal(tmp_path, capsys):
    # runs/svc-run compared with itself: versions trivially match; --no-reveal because
    # no sidecar exists; --no-pdf keeps it WeasyPrint-free. Read-only guarantee checked
    # via the drop_log row count.
    db = Path("runs/svc-run/run.db")
    before = sqlite3.connect(db).execute("select count(*) from drop_log").fetchone()[0]
    out = tmp_path / "cmp"
    rc = cli_main(["compare", "runs/svc-run", "runs/svc-run",
                   "--presentation", "configs/briefing_presentation_v1.yaml",
                   "--name-a", "Op A", "--name-b", "Op B",
                   "--out", str(out), "--no-reveal", "--no-pdf"])
    assert rc == 0
    after = sqlite3.connect(db).execute("select count(*) from drop_log").fetchone()[0]
    assert before == after
    c = _json.loads((out / "compare.json").read_text(encoding="utf-8"))
    assert c["meta"]["a"]["name"] == "Op A"
    html = (out / "compare.html").read_text(encoding="utf-8")
    assert "Op A" in html and "reveal not run" in html.lower()

def test_compare_cli_fails_closed_without_sidecar_when_reveal_expected(tmp_path, capsys):
    rc = cli_main(["compare", "runs/svc-run", "runs/svc-run",
                   "--presentation", "configs/briefing_presentation_v1.yaml",
                   "--name-a", "A", "--name-b", "B",
                   "--out", str(tmp_path / "cmp2"), "--no-pdf"])
    assert rc == 1
    assert "holdout_labels.json" in capsys.readouterr().out
