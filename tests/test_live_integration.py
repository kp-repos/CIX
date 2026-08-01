import json
import os
import subprocess
import sys
import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"),
                                reason="live test needs ANTHROPIC_API_KEY")

def test_live_thin_slice(tmp_path):
    """One real end-to-end run on the 24-interaction fixture corpus. Costs ~$1-3."""
    r = subprocess.run([sys.executable, "-m", "cix.cli", "run", "tests/fixtures/corpus_g2",
                        "--rubric", "configs/mini_rubric_v0.yaml", "--out", str(tmp_path / "live")],
                       capture_output=True, text=True, timeout=1200)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["interactions"] == 24
    report = json.loads((tmp_path / "live" / "report.json").read_text())
    assert report["sections"]["method"]["drop_summary"]["candidate_claims"] > 0
