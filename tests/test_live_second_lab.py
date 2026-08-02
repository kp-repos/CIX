import os
import pytest
from pathlib import Path
from cix.model import complete_json
from cix.second_lab import OpenAIClient, load_second_lab_config

pytestmark = pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"),
                                reason="live second-lab test: set OPENAI_API_KEY to run")

def test_second_lab_round_trip():
    cfg = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    client = OpenAIClient(cfg)
    out = complete_json(client, 'Return ONLY JSON: {"ok": true}')
    assert out.get("ok") is True
