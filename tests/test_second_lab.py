from pathlib import Path
from cix.model import ModelClient
from cix.second_lab import OpenAIClient, load_second_lab_config

def test_second_lab_config_loads():
    cfg = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    assert cfg.lab == "openai"
    assert cfg.model
    assert cfg.audit_sample_hits == 8
    assert cfg.agreement_floor == 0.8

def test_openai_client_satisfies_protocol():
    # structural check only — no network, no key needed
    assert hasattr(OpenAIClient, "complete")
    assert isinstance(OpenAIClient, type)

def test_content_or_raise_on_none():
    import pytest
    from types import SimpleNamespace
    from cix.model import MalformedResponse
    from cix.second_lab import _content_or_raise
    ok = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",
                                                  message=SimpleNamespace(content='{"ok": true}'))])
    assert _content_or_raise(ok) == '{"ok": true}'
    truncated = SimpleNamespace(choices=[SimpleNamespace(finish_reason="length",
                                                        message=SimpleNamespace(content=None))])
    with pytest.raises(MalformedResponse):
        _content_or_raise(truncated)
