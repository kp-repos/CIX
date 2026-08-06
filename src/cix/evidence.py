from cix.store import Store

def _quote_ok(store: Store, q: dict) -> bool:
    """R-EVD-1 component: quoted text must appear verbatim as a full snippet text,
    or exactly equal the newline-join of the cited contiguous span.

    Synthesis asks for an interaction_id, but the model sometimes returns the snippet id
    it was shown in the evidence block (e.g. "cfpb-123:0004"). Resolve such a snippet id
    back to its interaction so a verbatim quote isn't dropped on an id-field technicality.
    This changes no verification semantics — the quote must still equal a whole snippet (or
    the cited span-join); a fabricated quote still matches nothing and drops."""
    interaction_id = q["interaction_id"]
    snip = store.snippet(interaction_id)          # non-None iff the model gave a snippet id
    if snip is not None:
        interaction_id = snip["interaction_id"]
    span = store.span(interaction_id, q["start"], q["end"])
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
