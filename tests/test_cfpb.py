import csv
import json
from pathlib import Path
import pytest
import yaml
from cix.cfpb import (parse_received, read_filtered, dedup_rows, sample_stratified,
                      write_corpus)
from cix.normalize import load_corpus, load_corpus_properties
from cix.cli import main as cli_main
from cix.store import build_store

def test_parse_received_handles_both_formats():
    assert parse_received("2025-07-15T12:57:20.000Z") == "2025-07-15"
    assert parse_received("2015-03-19") == "2015-03-19"

def test_parse_received_rejects_garbage():
    with pytest.raises(ValueError):
        parse_received("07/15/2025")

FIELDS = ["Date received", "Product", "Sub-product", "Issue", "Sub-issue",
          "Consumer complaint narrative", "Company public response", "Company",
          "State", "ZIP code", "Tags", "Submitted via", "Date sent to company",
          "Company response to consumer", "Timely response?", "Complaint ID"]

def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**{k: "" for k in FIELDS}, **r})

def _row(cid, company="Block, Inc.", date="2024-06-01T10:00:00.000Z",
         narrative="I was charged twice and nobody replied.",
         response="Closed with explanation"):
    return {"Complaint ID": cid, "Company": company, "Date received": date,
            "Consumer complaint narrative": narrative,
            "Company response to consumer": response}

def test_read_filtered_by_company_and_date_with_drop_counts(tmp_path):
    p = tmp_path / "c.csv"
    _write_csv(p, [
        _row("1.0"),
        _row("2.0", company="Other Co"),                       # wrong company
        _row("3.0", date="2023-12-31"),                        # before window
        _row("4.0", narrative=""),                             # no narrative
        _row("5.0", date="not-a-date"),                        # unparseable
    ])
    rows, drops = read_filtered(p, company="Block, Inc.", since="2024-01-01")
    assert [r["complaint_id"] for r in rows] == ["1"]          # '.0' artifact stripped
    assert drops == {"wrong_company": 1, "before_window": 1,
                     "empty_narrative": 1, "bad_date": 1}
    assert rows[0]["date"] == "2024-06-01"
    assert rows[0]["outcome"] == "Closed with explanation"

def test_dedup_rows_collapses_identical_narratives():
    rows = [
        {"complaint_id": "1", "narrative": "same text", "date": "2024-01-05"},
        {"complaint_id": "2", "narrative": "same text", "date": "2024-01-06"},
        {"complaint_id": "3", "narrative": "different", "date": "2024-01-07"},
    ]
    kept, n_dupes = dedup_rows(rows)
    assert [r["complaint_id"] for r in kept] == ["1", "3"]     # first id wins
    assert n_dupes == 1

def test_sample_stratified_is_deterministic_and_month_proportional():
    rows = ([{"complaint_id": str(i), "date": "2024-01-15", "narrative": f"a{i}"} for i in range(80)]
            + [{"complaint_id": str(100 + i), "date": "2024-02-15", "narrative": f"b{i}"} for i in range(20)])
    s1 = sample_stratified(rows, n=10, seed=42)
    s2 = sample_stratified(rows, n=10, seed=42)
    assert s1 == s2                                            # same seed, same slice
    months = [r["date"][:7] for r in s1]
    assert months.count("2024-01") == 8 and months.count("2024-02") == 2
    assert sample_stratified(rows, n=10, seed=43) != s1        # seed matters

def test_sample_stratified_returns_all_when_n_exceeds_population():
    rows = [{"complaint_id": "1", "date": "2024-01-15", "narrative": "x"}]
    assert len(sample_stratified(rows, n=10, seed=1)) == 1

def _sample_rows():
    return [
        {"complaint_id": "101", "date": "2024-03-01", "narrative": "Charged twice, refund refused.",
         "product": "Money transfer", "issue": "Fraud or scam",
         "outcome": "Closed with monetary relief"},
        {"complaint_id": "102", "date": "2024-04-02", "narrative": "Account frozen for weeks.",
         "product": "Checking account", "issue": "Managing an account",
         "outcome": "Closed with explanation"},
    ]

def test_write_corpus_layout_and_units_validate(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="cfpb_narratives_filtered.csv")
    units = load_corpus(out / "units")                 # validates the corpus contract
    assert [u.id for u in units] == ["cfpb-101", "cfpb-102"]
    assert units[0].source_type == "note"
    assert units[0].segments[0].text == "Charged twice, refund refused."
    assert units[0].date == "2024-03-01"

def test_write_corpus_withholds_outcome_label(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    for p in (out / "units").glob("*.json"):
        text = p.read_text(encoding="utf-8")
        assert "monetary relief" not in text            # label never in a unit file
        assert "Company response" not in text
    labels = json.loads((out / "holdout_labels.json").read_text(encoding="utf-8"))
    assert labels["cfpb-101"] == "Closed with monetary relief"
    assert labels["cfpb-102"] == "Closed with explanation"

def test_write_corpus_writes_s2_properties(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    props = load_corpus_properties(out / "units")       # parent lookup
    assert props["substrate_class"] == "S2"
    assert props["licence_tier"] == "public-domain"
    assert props["speaker_attribution"] == "none"
    raw = yaml.safe_load((out / "corpus_properties.yaml").read_text(encoding="utf-8"))
    assert raw["sampling"]["seed"] == 42 and raw["sampling"]["company"] == "Block, Inc."

def test_cfpb_ingest_cli_end_to_end(tmp_path, capsys):
    p = tmp_path / "c.csv"
    _write_csv(p, [_row(str(i) + ".0", narrative=f"Complaint number {i} about a fee.")
                   for i in range(1, 8)])
    out = tmp_path / "corpus"
    rc = cli_main(["cfpb-ingest", str(p), "--company", "Block, Inc.",
                   "--since", "2024-01-01", "--n", "5", "--seed", "7",
                   "--out", str(out)])
    assert rc == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["written"] == 5
    assert summary["drops"] == {}                      # every fixture row is eligible
    assert len(list((out / "units").glob("*.json"))) == 5

def test_cfpb_ingest_rejects_bad_since(tmp_path, capsys):
    p = tmp_path / "c.csv"
    _write_csv(p, [_row("1.0")])
    rc = cli_main(["cfpb-ingest", str(p), "--company", "Block, Inc.",
                   "--since", "01/2024", "--n", "5", "--seed", "7",
                   "--out", str(tmp_path / "corpus")])
    assert rc == 2
    assert "since" in capsys.readouterr().err.lower()

def test_outcome_label_never_reaches_the_store(tmp_path):
    out = tmp_path / "corpus"
    write_corpus(_sample_rows(), out, company="Block, Inc.", since="2024-01-01",
                 seed=42, source_csv="x.csv")
    units = load_corpus(out / "units")
    db = tmp_path / "run.db"
    build_store(units, Path("configs/tag_vocabulary_v1.yaml"), db)
    blob = db.read_bytes()
    assert b"monetary relief" not in blob
    assert b"Closed with explanation" not in blob


# --- sentence segmentation (evidence-gate fix): a monologue narrative must become
# multiple short segments so the chunker yields quotable snippets. A single giant
# snippet can never equal an excerpt, so synthesis quotes would all drop (release_block).
from cix.cfpb import segment_narrative

def test_segment_narrative_splits_on_sentence_boundaries():
    text = "They closed my account without warning. I asked for evidence. Nobody replied to me."
    segs = segment_narrative(text)
    assert segs == ["They closed my account without warning.",
                    "I asked for evidence.",
                    "Nobody replied to me."]

def test_segment_narrative_single_sentence_is_one_segment():
    # Preserves the existing single-sentence fixtures' behavior.
    assert segment_narrative("Charged twice, refund refused.") == ["Charged twice, refund refused."]

def test_segment_narrative_caps_long_runons_into_quotable_chunks():
    text = ("word " * 400).strip()   # ~2000 chars, no sentence punctuation
    segs = segment_narrative(text, max_chars=600)
    assert len(segs) >= 3
    assert all(len(s) <= 600 for s in segs)

def test_segment_narrative_currency_and_redaction_do_not_oversplit():
    # {$1,234.00} has a '.' not followed by whitespace+capital -> must NOT split there.
    text = "I was charged {$1,234.00} by XXXX. That fee was never disclosed."
    segs = segment_narrative(text)
    assert segs == ["I was charged {$1,234.00} by XXXX.", "That fee was never disclosed."]

def test_write_corpus_segments_multi_sentence_narrative(tmp_path):
    rows = [{"complaint_id": "301", "date": "2024-05-01",
             "narrative": "Cash App froze my funds. I could not access my paycheck. Support never answered.",
             "product": "Money transfer", "issue": "Fraud",
             "outcome": "Closed with explanation"}]
    out = tmp_path / "corpus"
    write_corpus(rows, out, company="Block, Inc.", since="2024-01-01", seed=1, source_csv="x.csv")
    units = load_corpus(out / "units")
    assert len(units[0].segments) == 3                          # one quotable snippet per sentence
    assert all(len(s.text) < 200 for s in units[0].segments)
    assert "explanation" not in (out / "units" / "cfpb-301.json").read_text()  # outcome still withheld
