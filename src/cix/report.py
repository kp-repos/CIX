import json
from pathlib import Path
from fpdf import FPDF

def _sections(payload: dict) -> dict:
    findings = payload["findings"]
    positives = [f for f in findings if f.get("polarity") == "positive"]
    return {
        "highlights": [
            {"item_id": f["item_id"], "narrative": f["body"]["narrative"],
             "count": f["body"]["claimed_count"], "share": f.get("share"),
             "denominator": f.get("denominator"), "unit": f.get("unit"),
             "remedy": "none yet", "mechanism_status": f["mechanism_status"],
             "evidence": [q for q in f["body"]["quotes"]]}
            for f in findings
        ],
        "whats_working": [{"item_id": f["item_id"], "narrative": f["body"]["narrative"]} for f in positives],
        "leverage": {"grid": [], "shelf": [{"item_id": f["item_id"], "count": f["body"]["claimed_count"],
                                            "unit": f.get("unit")} for f in findings],
                     "note": "No catalogue loaded: all findings on the 'no known remedy yet' shelf."},
        "priced_plays": {"plays": [], "note": "No catalogue loaded — no priced view in this run."},
        "distribution": {"items": payload["rollup"]["items"],
                         "rank_by_unit": payload["rollup"]["rank_by_unit"],
                         "interaction_coverage": payload["rollup"]["interaction_coverage"],
                         "residual_interactions": payload["rollup"]["residual_interactions"],
                         "eligible_interactions": payload["rollup"]["eligible_interactions"]},
        "method": {"validations": payload["validations"], "drop_summary": payload["drop_summary"],
                   "manifest": payload["manifest"]},
    }

def render_report(payload: dict, out_dir: Path) -> dict:
    """Render report.json + report.pdf from persisted data only — no model access here (AC-15)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {"sections": _sections(payload), "manifest": payload["manifest"]}
    (out_dir / "report.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CIX Run Report", new_x="LMARGIN", new_y="NEXT")
    titles = [("1 - Highlights", "highlights"), ("2 - What's working", "whats_working"),
              ("3 - Leverage", "leverage"), ("4 - Priced plays", "priced_plays"),
              ("5 - Distribution + coverage", "distribution"), ("6 - Method", "method")]
    pdf.set_font("Helvetica", size=9)
    for title, key in titles:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        text = json.dumps(doc["sections"][key], indent=1, ensure_ascii=False)
        # Core Helvetica supports latin-1 only; keep report.json unicode-clean and
        # substitute unsupported glyphs (e.g. em-dash) for the PDF text dump.
        safe = text[:4000].encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 4, safe)
    pdf.output(str(out_dir / "report.pdf"))
    return doc
