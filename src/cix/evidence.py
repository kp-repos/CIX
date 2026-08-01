from cix.store import Store

def _quote_ok(store: Store, q: dict) -> bool:
    """R-EVD-1 component: quoted text must appear verbatim as a full snippet text,
    or exactly equal the newline-join of the cited contiguous span."""
    span = store.span(q["interaction_id"], q["start"], q["end"])
    if not span:
        return False
    joined = "\n".join(s["text"] for s in span)
    return q["text"] == joined or any(q["text"] == s["text"] for s in span)

def _stat_ok(store: Store, s: dict) -> bool:
    """R-EVD-2 component: quantitative claim must recompute from the store."""
    if s["kind"] == "snippet_tag_count":
        return len(store.snippets_with_tag(s["tag"])) == s["expected"]
    return False  # unknown stat kinds never pass (fail closed)

def gate_claims(store: Store, claims: dict) -> dict:
    """Pass/fail, mechanical. Failures are dropped from the result and written
    to the drop log (drop-don't-flag lock + drop-log ruling)."""
    passed_quotes, passed_stats = [], []
    for q in claims.get("quotes", []):
        if _quote_ok(store, q):
            passed_quotes.append(q)
        else:
            store.log_drop(q["ref"], "quote_string_match", f"no exact match at {q['interaction_id']}:{q['start']}-{q['end']}")
    for s in claims.get("stats", []):
        if _stat_ok(store, s):
            passed_stats.append(s)
        else:
            store.log_drop(s["ref"], "stat_recompute", f"{s['kind']}({s.get('tag')}) != {s['expected']}")
    return {"quotes": passed_quotes, "stats": passed_stats}
