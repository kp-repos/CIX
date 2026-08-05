"""Live evidence resolution for the demo (R-OUT-2): resolve a report claim to its
scrubbed source text in the run store. Read-only — the caller opens the store mode=ro.

Two directions:
  resolve_item — a finding's count -> the actual interactions/snippets behind it,
                 plus verbatim checks on any quote-level evidence the finding carries.
  find_quote   — a pasted quote -> the snippet(s) it matches verbatim, or nothing.
"""
from cix.evidence import _quote_ok
from cix.store import Store

def _finding(report: dict, item_id: str) -> dict | None:
    for f in report.get("sections", {}).get("highlights", []):
        if f.get("item_id") == item_id:
            return f
    return None

def resolve_item(store: Store, report: dict, manifest: dict, item_id: str) -> dict:
    """Resolve one finding to its stored source. Returns {"found": False} for an
    unknown item so the CLI can fail closed."""
    finding = _finding(report, item_id)
    if finding is None:
        return {"found": False, "item_id": item_id}
    ha = manifest["artifacts"]["hits"]
    hits = []
    for h in store.hits_for(ha):
        if h["item_id"] != item_id:
            continue
        snips = store.snippets_for_ref(h["snippet_ids"])
        hits.append({"snippet_ids": h["snippet_ids"], "interaction_id": h["interaction_id"],
                     "snippets": [{"id": s["id"], "seq": s["seq"], "text": s["text"]} for s in snips]})
    quotes = [{"text": q["text"], "interaction_id": q["interaction_id"],
               "verbatim": _quote_ok(store, q)}
              for q in finding.get("evidence", [])]
    return {"found": True, "item_id": item_id, "narrative": finding.get("narrative"),
            "count": finding.get("count"), "share": finding.get("share"),
            "hits": hits, "quotes": quotes}

def find_quote(store: Store, text: str) -> list[dict]:
    """Reverse lookup: snippets whose scrubbed text matches `text` verbatim.
    Empty list means the quote does NOT resolve to any stored source."""
    return store.snippets_matching(text)

def resolve_metric(store: Store, manifest: dict, presentation: dict, metric_name: str, eligible: int) -> dict:
    """Resolve a named headline metric to its underlying interaction set (read-only).
    Returns {"found": False} for an unknown metric so the CLI can fail closed.
    Uses the same unit=="interaction" filter as briefing.avoidable_contact_rate so
    the two code paths always produce identical results."""
    spec = presentation.get("headline_metrics", {}).get(metric_name)
    if spec is None:
        return {"found": False, "metric": metric_name}
    members = set(spec["members"])
    ha = manifest["artifacts"]["hits"]
    # Same union as briefing.avoidable_contact_rate: interaction-unit rows only.
    ids = sorted({h["interaction_id"] for h in store.hits_for(ha)
                  if h["item_id"] in members and h.get("unit") == "interaction"})
    return {"found": True, "metric": metric_name, "value": len(ids),
            "denominator": eligible, "interaction_ids": ids, "members": spec["members"]}
