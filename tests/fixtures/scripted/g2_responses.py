"""Canned model responses for offline end-to-end tests over corpus_g2."""
import json
from pathlib import Path

def build_mapping(corpus_dir: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in sorted(corpus_dir.glob("*.json")):
        doc = json.loads(path.read_text())
        uid = doc["id"]
        text = " ".join(s["text"] for s in doc["segments"])
        if "charged twice" in text:
            labels = {"motion": "service", "intent": "fix duplicate charge", "driver_origin": "internal_defect",
                      "automatability": "assisted", "outcome": "escalated", "handoff_events": ["billing team"]}
            hits = [{"item_id": "billing_defect_driver", "snippet_ids": f"{uid}:0000"},
                    {"item_id": "repeat_contact_unresolved", "snippet_ids": f"{uid}:0002"}]
        elif "fee would be waived" in text:
            labels = {"motion": "service", "intent": "fee dispute", "driver_origin": "policy",
                      "automatability": "assisted", "outcome": "escalated", "handoff_events": ["fees desk"]}
            hits = [{"item_id": "billing_defect_driver", "snippet_ids": f"{uid}:0000"},
                    {"item_id": "transfer_or_escalation_event", "snippet_ids": f"{uid}:0001"}]
        elif "reset my password" in text:
            labels = {"motion": "service", "intent": "password reset", "driver_origin": "customer",
                      "automatability": "rote", "outcome": "resolved", "handoff_events": []}
            hits = [{"item_id": "deterministic_request_assisted", "snippet_ids": f"{uid}:0000"},
                    {"item_id": "clean_first_contact_resolution", "snippet_ids": f"{uid}:0002"}]
        else:  # delivery_complaint
            labels = {"motion": "service", "intent": "missing statement", "driver_origin": "internal_defect",
                      "automatability": "assisted", "outcome": "resolved", "handoff_events": []}
            hits = [{"item_id": "clean_first_contact_resolution", "snippet_ids": f"{uid}:0002"}]
        # Conjunctive keys ("&&") route by prompt kind + interaction id — a hit prompt
        # also contains the interaction tag, so kind-markers are required to disambiguate.
        mapping[f"You are labeling&&<interaction id={uid}>"] = json.dumps(labels)
        mapping[f"You are detecting&&<interaction id={uid}>"] = json.dumps({"hits": hits})
    return mapping

def synthesis_mapping(corpus_dir: Path) -> dict[str, str]:
    """Synthesis prompts are keyed by item id; quotes copy real fixture text."""
    first_billing = None
    for path in sorted(corpus_dir.glob("*.json")):
        doc = json.loads(path.read_text())
        if "charged twice" in doc["segments"][0]["text"]:
            first_billing = doc
            break
    def quote_for(doc):
        return {"interaction_id": doc["id"], "start": 0, "end": 0, "text": doc["segments"][0]["text"]}
    def body(item, count_token="COUNT"):
        return json.dumps({"narrative": f"Finding for {item}.", "claimed_count": count_token,
                           "quotes": [quote_for(first_billing)] if first_billing else [],
                           "mechanism": {"proposed": "p", "alternative": "a",
                                         "discriminating_snippet_ids": []}})
    return {f'rubric item "{item}"': body(item) for item in [
        "repeat_contact_unresolved", "deterministic_request_assisted", "billing_defect_driver",
        "transfer_or_escalation_event", "clean_first_contact_resolution"]}
