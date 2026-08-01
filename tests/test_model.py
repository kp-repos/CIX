import pytest
from cix.model import MalformedResponse, ScriptedClient, complete_json

def test_scripted_client_matches_on_prompt_substring():
    c = ScriptedClient({"g2-g2-000": '{"ok": 1}'})
    out = complete_json(c, "label this: <interaction id=g2-g2-000>...</interaction>")
    assert out == {"ok": 1}

def test_conjunctive_keys_route_by_prompt_kind():
    # "&&" joins substrings that must ALL be present — lets one client serve
    # label, hit, and synthesis prompts for the same interaction without collision
    c = ScriptedClient({"labeling&&id=x1": '{"a": 1}', "detecting&&id=x1": '{"b": 2}'})
    assert complete_json(c, "You are labeling ... <interaction id=x1>") == {"a": 1}
    assert complete_json(c, "You are detecting ... <interaction id=x1> [x1:0000]") == {"b": 2}

def test_malformed_then_valid_retries_once():
    c = ScriptedClient(sequence=["not json at all", '{"ok": 2}'])
    assert complete_json(c, "anything") == {"ok": 2}
    assert c.calls == 2

def test_persistent_malformed_fails_cleanly():
    class AlwaysBad:
        def complete(self, prompt):
            return "nope"
    with pytest.raises(MalformedResponse):
        complete_json(AlwaysBad(), "anything")

def test_refusal_is_retried_not_fatal():
    # a stray refusal (client raises MalformedResponse mid-run) must be retried,
    # not abort the whole run — reasoning tiers emit occasional refusal/empty responses
    class FlakyRefusal:
        def __init__(self):
            self.n = 0
        def complete(self, prompt):
            self.n += 1
            if self.n == 1:
                raise MalformedResponse("no text block (stop_reason=refusal)")
            return '{"ok": 5}'
    c = FlakyRefusal()
    assert complete_json(c, "x") == {"ok": 5}
    assert c.n == 2

def test_json_extracted_from_fenced_block():
    c = ScriptedClient(sequence=['Here you go:\n```json\n{"ok": 3}\n```'])
    assert complete_json(c, "x") == {"ok": 3}

def test_json_extracted_from_unfenced_leading_prose():
    # a live model may add a preamble without a code fence — extract the object
    # rather than burning the retry and aborting the run after spend
    c = ScriptedClient(sequence=['Here is the JSON: {"ok": 4} hope that helps'])
    assert complete_json(c, "x") == {"ok": 4}
    assert c.calls == 1

def test_json_extracted_from_prose_with_nested_object():
    c = ScriptedClient(sequence=['Sure: {"a": {"b": 1}, "c": "}"} done'])
    assert complete_json(c, "x") == {"a": {"b": 1}, "c": "}"}
