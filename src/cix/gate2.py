import json
from cix.evidence import _quote_ok
from cix.store import Store

def gate_synthesis(store: Store, synthesis_id: str, rollup: dict) -> dict:
    """End-to-end evidence gate (R-EVD-1/2/3). Quote fail or count fail -> finding dropped
    and drop-logged. Empty discriminating evidence -> kept, marked undischarged (R-VAL-3)."""
    findings, quote_drops, stat_drops, candidates = [], 0, 0, 0
    for row in store.synthesis_for(synthesis_id):
        item_id = row["item_id"]
        body = json.loads(row["body"])
        candidates += len(body.get("quotes", [])) + 1  # quotes + the count claim
        ok = True
        for q in body.get("quotes", []):
            if not _quote_ok(store, q):
                store.log_drop(item_id, "quote_string_match",
                               f"quote does not match {q['interaction_id']}:{q['start']}-{q['end']}")
                quote_drops += 1
                ok = False
        expected = rollup["items"].get(item_id, {}).get("count")
        if body.get("claimed_count") != expected:
            store.log_drop(item_id, "stat_recompute",
                           f"claimed {body.get('claimed_count')} != rollup {expected}")
            stat_drops += 1
            ok = False
        if not ok:
            continue
        disc = body["mechanism"].get("discriminating_snippet_ids", [])
        resolved = [d for d in disc if store.snippet(d) is not None]
        status = "discharged" if resolved else "undischarged"
        findings.append({"item_id": item_id, "body": body, "mechanism_status": status})
    return {"findings": findings, "candidate_claims": candidates,
            "quote_drops": quote_drops, "stat_drops": stat_drops}
