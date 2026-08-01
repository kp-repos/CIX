import hashlib
from cix.contracts import InteractionUnit
from cix.chunker import chunk

UNIT = InteractionUnit(
    id="int-001", source_type="transcript",
    segments=[{"speaker": "customer", "text": "Hello."}, {"speaker": "agent", "text": "Hi there."}],
)

def test_ids_are_positional_and_stable():
    snippets = chunk(UNIT)
    assert [s["id"] for s in snippets] == ["int-001:0000", "int-001:0001"]
    assert [s["seq"] for s in snippets] == [0, 1]

def test_content_hash_is_sha256_of_text():
    s = chunk(UNIT)[0]
    assert s["content_hash"] == hashlib.sha256("Hello.".encode()).hexdigest()

def test_speaker_carried():
    assert chunk(UNIT)[1]["speaker"] == "agent"
