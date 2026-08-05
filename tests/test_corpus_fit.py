import json
import shutil
import sys
from pathlib import Path

import yaml

from cix.cli import main
from cix.model import ScriptedClient
from cix.normalize import DEFAULT_CORPUS_PROPERTIES, load_corpus_properties

FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(FIX / "scripted"))
from g2_responses import build_mapping, synthesis_mapping  # noqa: E402
from test_run_e2e import CountingClient  # noqa: E402


def test_default_properties_when_no_file(tmp_path):
    props = load_corpus_properties(tmp_path)
    assert props == DEFAULT_CORPUS_PROPERTIES
    assert props["substrate_class"] == "unspecified"


def test_properties_load_from_corpus_dir(tmp_path):
    (tmp_path / "corpus_properties.yaml").write_text(yaml.safe_dump({
        "substrate_class": "S2", "licence_tier": "public-domain",
        "speaker_attribution": "none", "economic_signal": "present",
        "ivr_structure": "absent"}), encoding="utf-8")
    props = load_corpus_properties(tmp_path)
    assert props["substrate_class"] == "S2"
    assert props["licence_tier"] == "public-domain"


def test_partial_properties_merge_over_defaults(tmp_path):
    (tmp_path / "corpus_properties.yaml").write_text(
        yaml.safe_dump({"substrate_class": "S2"}), encoding="utf-8")
    props = load_corpus_properties(tmp_path)
    assert props["substrate_class"] == "S2"          # from file
    assert props["licence_tier"] == "unspecified"    # filled from defaults
    assert props["economic_signal"] == "redacted"    # filled from defaults


def test_properties_load_from_parent_dir(tmp_path):
    # units live in <out>/units; properties sit one level up (adapter layout)
    units = tmp_path / "units"
    units.mkdir()
    (tmp_path / "corpus_properties.yaml").write_text(yaml.safe_dump({
        "substrate_class": "S2", "licence_tier": "public-domain",
        "speaker_attribution": "none", "economic_signal": "present",
        "ivr_structure": "absent"}), encoding="utf-8")
    assert load_corpus_properties(units)["substrate_class"] == "S2"


def test_run_records_substrate_in_manifest(tmp_path, monkeypatch, capsys):
    import cix.cli as cli
    corpus = tmp_path / "corpus"
    shutil.copytree(FIX / "corpus_g2", corpus)
    (corpus / "corpus_properties.yaml").write_text(yaml.safe_dump({
        "substrate_class": "S2", "licence_tier": "public-domain",
        "speaker_attribution": "none", "economic_signal": "present",
        "ivr_structure": "absent"}), encoding="utf-8")
    client = CountingClient({**build_mapping(corpus), **synthesis_mapping(corpus)})
    monkeypatch.setattr(cli, "make_client", lambda cfg: client)
    monkeypatch.setattr(cli, "make_second_client",
                        lambda cfg: ScriptedClient(mapping={'"applies"': '{"applies": true}'}))
    out = tmp_path / "run"
    rc = main(["run", str(corpus), "--rubric", "configs/mini_rubric_v0.yaml",
               "--out", str(out)])
    assert rc == 0
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["substrate_class"] == "S2"
    assert manifest["corpus_properties"]["licence_tier"] == "public-domain"
