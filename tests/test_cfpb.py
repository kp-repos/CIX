import csv
from pathlib import Path
import pytest
from cix.cfpb import (parse_received, read_filtered, dedup_rows, sample_stratified)

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
