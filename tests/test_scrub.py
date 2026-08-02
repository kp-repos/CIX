from cix.contracts import InteractionUnit
from cix.scrub import load_privacy_protocol, scrub_corpus, residual_scan
from pathlib import Path

PROTO = Path("configs/privacy_protocol_v1.yaml")

def _unit(uid="i1"):
    return InteractionUnit.model_validate({
        "id": uid, "source_type": "transcript",
        "participants": ["Dana Reyes", "customer"],
        "account_id": "ACME-4471", "thread_id": "T-99",
        "segments": [
            {"speaker": "Dana Reyes", "text": "Hi, this is Dana. Reach me at dana@acme.com or 555-123-4567."},
            {"speaker": "customer", "text": "Thanks Dana. The invoice was $500 on 2026-03-01."},
        ],
    })

def test_email_and_phone_redacted():
    proto = load_privacy_protocol(PROTO)
    scrubbed, report = scrub_corpus([_unit()], proto, salt="s")
    text = " ".join(seg.text for seg in scrubbed[0].segments)
    assert "[EMAIL]" in text and "[PHONE]" in text
    assert "dana@acme.com" not in text and "555-123-4567" not in text

def test_amount_and_date_survive():
    proto = load_privacy_protocol(PROTO)
    scrubbed, _ = scrub_corpus([_unit()], proto, salt="s")
    text = " ".join(seg.text for seg in scrubbed[0].segments)
    assert "$500" in text and "2026-03-01" in text

def test_participant_name_pseudonymized_consistently():
    proto = load_privacy_protocol(PROTO)
    scrubbed, _ = scrub_corpus([_unit()], proto, salt="s")
    text = " ".join(seg.text for seg in scrubbed[0].segments)
    assert "Dana" not in text
    # same name -> same token in speaker field and body
    speaker = scrubbed[0].segments[0].speaker
    assert speaker.startswith("PERSON-")
    assert speaker in text  # the pseudonym replaced the name inside the body too

def test_linkage_survives_as_pseudonym():
    proto = load_privacy_protocol(PROTO)
    scrubbed, _ = scrub_corpus([_unit()], proto, salt="s")
    assert scrubbed[0].account_id.startswith("ACCT-")
    assert scrubbed[0].thread_id.startswith("THREAD-")
    assert scrubbed[0].account_id != "ACME-4471"

def test_pseudonym_is_salt_stable_and_salt_sensitive():
    proto = load_privacy_protocol(PROTO)
    a, _ = scrub_corpus([_unit()], proto, salt="s1")
    b, _ = scrub_corpus([_unit()], proto, salt="s1")
    c, _ = scrub_corpus([_unit()], proto, salt="s2")
    assert a[0].account_id == b[0].account_id      # deterministic per salt
    assert a[0].account_id != c[0].account_id      # different salt -> different token

def test_report_counts_and_residual_scan_clean():
    proto = load_privacy_protocol(PROTO)
    scrubbed, report = scrub_corpus([_unit()], proto, salt="s")
    assert report["counts"]["email"] == 1 and report["counts"]["phone"] == 1
    assert report["counts"]["person"] >= 1
    assert residual_scan(scrubbed) == []            # no leftover email/phone patterns
