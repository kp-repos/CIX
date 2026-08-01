from pathlib import Path
from cix.contracts import InteractionUnit
from cix.chunker import chunk
from cix.tags import load_vocabulary, tag_interaction, tag_snippets

VOCAB = load_vocabulary(Path("configs/tag_vocabulary_v1.yaml"))

UNIT = InteractionUnit(
    id="int-001", source_type="transcript", account_id="acct-9", date="2026-05-01",
    segments=[
        {"speaker": "customer", "text": "I already called about this last time, still not fixed. Why?"},
        {"speaker": "agent", "text": "Please hold on while I transfer you."},
        {"speaker": "customer", "text": "There is a $25 charge."},
    ],
)
SNIPPETS = chunk(UNIT)

def test_vocabulary_version():
    assert VOCAB["version"] == "1.0.0"

def test_lexical_hits():
    rows = tag_snippets(SNIPPETS, VOCAB)
    tags_by_snippet = {}
    for sid, tag, _ in rows:
        tags_by_snippet.setdefault(sid, set()).add(tag)
    assert "repeat_marker" in tags_by_snippet["int-001:0000"]
    assert "question_mark" in tags_by_snippet["int-001:0000"]
    assert "transfer_hold" in tags_by_snippet["int-001:0001"]
    assert "currency_amount" in tags_by_snippet["int-001:0002"]

def test_structural_tags():
    rows = tag_snippets(SNIPPETS, VOCAB)
    d = {(sid, tag): val for sid, tag, val in rows}
    assert d[("int-001:0000", "position")] == "opening"
    assert d[("int-001:0002", "position")] == "closing"
    assert d[("int-001:0001", "speaker_role")] == "agent"
    assert d[("int-001:0000", "turn_length")] == str(len(SNIPPETS[0]["text"]))

def test_interaction_tags():
    rows = tag_interaction(UNIT, SNIPPETS)
    d = {tag: val for _, tag, val in rows}
    assert d["interaction_len_segments"] == "3"
    assert d["account_id"] == "acct-9"
    assert d["date"] == "2026-05-01"
    assert d["source_type"] == "transcript"
    assert 0.0 < float(d["speaker_balance"]) < 1.0

def test_deterministic_output_order():
    assert tag_snippets(SNIPPETS, VOCAB) == tag_snippets(SNIPPETS, VOCAB)
