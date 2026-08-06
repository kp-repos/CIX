"""Comparative briefing (model-free): side-by-side rendering of two persisted runs of
the SAME rubric over two operations, with an optional withheld-ground-truth reveal.

Same contract as briefing.py: reads persisted artifacts + read-only stores, never calls
a model, never mutates anything, fails closed. Spec 2026-08-05 §6.
"""
from cix.briefing import build_briefing, _esc

# The exact CFPB `Company response to consumer` value that denotes monetary relief —
# this is the withheld semi-ground-truth diverted to a sealed sidecar at ingest. If the
# substrate/label ever changes this constant MUST change too, or the reveal's relief rate
# silently reads 0. Spec 2026-08-05 §6.
RELIEF = "Closed with monetary relief"

_DIVERGENCE_TOP_N = 5

def _check_comparable(ma: dict, mb: dict) -> None:
    for key in ("rubric_version", "rubric_file", "substrate_class"):
        if ma.get(key) != mb.get(key):
            raise ValueError(f"runs are not comparable: {key} differs "
                             f"({ma.get(key)!r} vs {mb.get(key)!r})")

def _neg_rank(report: dict, cfg: dict) -> list[dict]:
    dist = report["sections"]["distribution"]["items"]
    rows = [{"item_id": i, "share": d.get("share"), "count": d.get("count"),
             "unit": d.get("unit")}
            for i, d in dist.items()
            if cfg["items"].get(i, {}).get("polarity") == "negative"]
    rows.sort(key=lambda r: (-(r["share"] or 0), r["item_id"]))
    for rank, r in enumerate(rows, start=1):
        r["rank"] = rank
    return rows

def build_compare(side_a: dict, side_b: dict, cfg: dict) -> dict:
    """side = {name, report, manifest, store}. Builds each side's briefing via the same
    builder the single-run artifact uses (consistency by construction), then compares."""
    ma, mb = side_a["manifest"], side_b["manifest"]
    _check_comparable(ma, mb)
    brief_a = build_briefing(side_a["report"], ma, cfg, side_a["store"])
    brief_b = build_briefing(side_b["report"], mb, cfg, side_b["store"])
    headline = {}
    for name in cfg["headline_metrics"]:
        a, b = brief_a["headline"][name], brief_b["headline"][name]
        ratio = (round(a["share"] / b["share"], 2)
                 if a.get("share") and b.get("share") else None)
        headline[name] = {"a": a, "b": b, "ratio": ratio,
                          "statement": a.get("statement")}
    rank_a, rank_b = _neg_rank(side_a["report"], cfg), _neg_rank(side_b["report"], cfg)
    pos_b = {r["item_id"]: r for r in rank_b}
    rows, excluded, divergence = [], [], []
    for r in rank_a:
        o = pos_b.get(r["item_id"])
        if o is None:
            excluded.append(f"{r['item_id']}: absent from run B distribution")
            continue
        if r["unit"] != o["unit"]:
            excluded.append(f"{r['item_id']}: unit mismatch ({r['unit']} vs {o['unit']})")
            continue
        sa, sb = r["share"] or 0.0, o["share"] or 0.0
        rows.append({"item_id": r["item_id"],
                     "label": cfg["items"].get(r["item_id"], {}).get("business_label",
                                                                     r["item_id"]),
                     "share_a": sa, "share_b": sb, "count_a": r["count"],
                     "count_b": o["count"], "unit": r["unit"],
                     "ratio": round(sa / sb, 2) if sb else None,
                     "rank_a": r["rank"], "rank_b": o["rank"]})
        divergence.append({"item_id": r["item_id"],
                           "label": cfg["items"].get(r["item_id"], {}).get("business_label",
                                                                           r["item_id"]),
                           "share_a": sa, "share_b": sb,
                           "abs_gap": round(abs(sa - sb), 4)})
    divergence_sorted = sorted(divergence, key=lambda d: (-d["abs_gap"], d["item_id"]))
    return {
        "meta": {"a": {"name": side_a["name"], "corpus_hash": ma.get("corpus_hash"),
                       "clearance": ma.get("corpus_clearance"),
                       "eligible": side_a["report"]["sections"]["distribution"]["eligible_interactions"]},
                 "b": {"name": side_b["name"], "corpus_hash": mb.get("corpus_hash"),
                       "clearance": mb.get("corpus_clearance"),
                       "eligible": side_b["report"]["sections"]["distribution"]["eligible_interactions"]},
                 "rubric_version": ma.get("rubric_version"),
                 "rubric_file": ma.get("rubric_file"),
                 "substrate_class": ma.get("substrate_class")},
        "headline": headline,
        "rank_order": {"a": rank_a, "b": rank_b},
        "driver_rates": {"rows": rows, "excluded": excluded},
        "divergence": {"rows": divergence_sorted[:_DIVERGENCE_TOP_N],
                       "total": len(divergence_sorted)},
        "trust": {"a": brief_a["trust"], "b": brief_b["trust"]},
    }

def reveal_block(labels_a: dict, labels_b: dict) -> dict:
    """Unseal the withheld outcome label. Facts only — rates and response distributions;
    interpretation stays human (spec §6)."""
    def side(labels: dict) -> dict:
        n = len(labels)
        responses: dict[str, int] = {}
        for v in labels.values():
            responses[v] = responses.get(v, 0) + 1
        relief = responses.get(RELIEF, 0)
        relief_key_present = RELIEF in responses
        return {"n": n, "responses": dict(sorted(responses.items())),
                "monetary_relief_rate": round(relief / n, 4) if n else None,
                "relief_key_present": relief_key_present}
    return {"banner": ("WITHHELD GROUND TRUTH — never seen by the model. "
                       "`Company response to consumer` was diverted to a sealed sidecar "
                       "at ingest and is unsealed here, post-run, for validation only."),
            "a": side(labels_a), "b": side(labels_b)}

_CSS = """
body{font-family:Helvetica,Arial,sans-serif;color:#1a1a1a;max-width:960px;margin:2rem auto;line-height:1.5}
h1{font-size:1.6rem;margin-bottom:.2rem}
.banner{background:#fef3c7;border:1px solid #f59e0b;padding:.5rem .8rem;border-radius:6px;font-size:.85rem;margin:.6rem 0}
.reveal{background:#fee2e2;border:1px solid #ef4444;padding:.6rem .9rem;border-radius:6px;margin:.8rem 0}
h2{font-size:1.15rem;border-bottom:2px solid #e5e7eb;padding-bottom:.2rem;margin-top:1.6rem}
.headline{background:#f0f9ff;border:1px solid #bae6fd;padding:.8rem 1rem;border-radius:8px;margin:.8rem 0}
.big{font-size:1.3rem;font-weight:700}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid #e5e7eb;vertical-align:top}
.muted{color:#6b7280;font-size:.85rem}
"""

def _pct(x) -> str:
    return "—" if x is None else f"{round(x * 100, 1)}%"

def render_compare_html(c: dict) -> str:
    a, b = c["meta"]["a"], c["meta"]["b"]
    out = ["<!DOCTYPE html>", "<html><head><meta charset='utf-8'>",
           f"<style>{_CSS}</style></head><body>"]
    out.append(f"<h1>Comparative Review — {_esc(a['name'])} vs {_esc(b['name'])}</h1>")
    out.append(f"<div class='banner'>Substrate class {_esc(c['meta']['substrate_class'])} · "
               f"rubric {_esc(c['meta']['rubric_file'])} v{_esc(c['meta']['rubric_version'])} · "
               f"A: {_esc(a['clearance'])} · B: {_esc(b['clearance'])}</div>")
    out.append("<h2>Headline</h2><div class='headline'>")
    for name, m in c["headline"].items():
        ra, rb = m["a"], m["b"]
        ratio = f" — {m['ratio']}× apart" if m.get("ratio") else ""
        out.append(f"<div class='big'>{_esc(a['name'])}: {ra['value']}/{ra['denominator']} · "
                   f"{_esc(b['name'])}: {rb['value']}/{rb['denominator']}{ratio}</div>")
        out.append(f"<div class='muted'>{_esc(m.get('statement'))} · {_esc(ra['method'])} · "
                   f"resolve per run with {_esc(ra['query'])}</div>")
    out.append("</div>")
    out.append("<h2>Pattern rank order</h2><table>")
    out.append(f"<tr><th>Pattern</th><th>{_esc(a['name'])} rank · share</th>"
               f"<th>{_esc(b['name'])} rank · share</th><th>Ratio</th></tr>")
    for r in c["driver_rates"]["rows"]:
        ratio = f"{r['ratio']}×" if r["ratio"] is not None else "—"
        out.append(f"<tr><td><b>{_esc(r['label'])}</b></td>"
                   f"<td>#{r['rank_a']} · {_pct(r['share_a'])} ({r['count_a']})</td>"
                   f"<td>#{r['rank_b']} · {_pct(r['share_b'])} ({r['count_b']})</td>"
                   f"<td>{ratio}</td></tr>")
    out.append("</table>")
    for note in c["driver_rates"]["excluded"]:
        out.append(f"<p class='muted'>excluded from comparison — {_esc(note)}</p>")
    out.append("<h2>Where the operations diverge most</h2><ul>")
    div_rows = c["divergence"]["rows"]
    div_total = c["divergence"]["total"]
    for d in div_rows:
        out.append(f"<li><b>{_esc(d['label'])}</b> — {_pct(d['share_a'])} vs "
                   f"{_pct(d['share_b'])} (gap {_pct(d['abs_gap'])} pts)</li>")
    out.append("</ul>")
    if div_total > len(div_rows):
        out.append(f"<p class='muted'>Showing the top {len(div_rows)} of {div_total} "
                   f"compared patterns by share gap.</p>")
    out.append("<h2>The reveal</h2>")
    rev = c.get("reveal")
    if rev:
        out.append(f"<div class='reveal'><b>{_esc(rev['banner'])}</b>")
        for key, side_meta in (("a", a), ("b", b)):
            s = rev[key]
            out.append(f"<p><b>{_esc(side_meta['name'])}</b>: monetary-relief rate "
                       f"{_pct(s['monetary_relief_rate'])} over n={s['n']} withheld labels.")
            if s["n"] > 0 and not s.get("relief_key_present", False):
                out.append(f"<span class='muted'>(no \"{_esc(RELIEF)}\" value seen in "
                           f"{s['n']} labels — the CFPB response vocabulary may have "
                           f"changed; 0% may be an artifact, not a finding)</span>")
            out.append("</p>")
        out.append("</div>")
    else:
        out.append("<p class='muted'>Reveal not run — no sealed sidecar was supplied "
                   "(--no-reveal or labels absent).</p>")
    out.append("<h2>Trust</h2>")
    for key, side_meta in (("a", a), ("b", b)):
        t = c["trust"][key]
        cov = t["coverage"]
        out.append(f"<p class='muted'><b>{_esc(side_meta['name'])}</b>: "
                   f"{round((cov['interaction_coverage'] or 0) * 100)}% of "
                   f"{cov['eligible_interactions']} eligible interactions read; "
                   f"honesty: {_esc(t['honesty_ladder'])}</p>")
        if t.get("evidence_note"):
            out.append(f"<p class='muted'>{_esc(t['evidence_note'])}</p>")
    out.append("</body></html>")
    return "\n".join(out)
