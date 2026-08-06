"""CFPB Consumer Complaints -> CIX corpus adapter (spec 2026-08-05 §3).

Converts filtered-CSV rows into the standard corpus contract (a directory of
InteractionUnit JSON files) so the calibrated pipeline stays untouched. The outcome
label `Company response to consumer` is semi-ground-truth: it is diverted to a sealed
sidecar at ingest and never enters any unit file, store, or model context (§3.2).
"""
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
import yaml

# Full ISO-8601 timestamp on recent rows, bare date on older ones (memo §4): both are
# accepted explicitly; anything else is a counted drop, never a silent NaT (R-IDX class).
_ISO_TS = re.compile(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}")
_BARE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")

# Intrinsic §2.3-S properties of the CFPB dataset (public-domain complaint narratives:
# real customer language, monologue so no speakers, dollar figures survive redaction).
_CFPB_CORPUS_PROPERTIES = {
    "substrate_class": "S2", "licence_tier": "public-domain",
    "speaker_attribution": "none", "economic_signal": "present",
    "ivr_structure": "absent",
}

def parse_received(s: str) -> str:
    for rx in (_ISO_TS, _BARE):
        m = rx.match(s or "")
        if m:
            return m.group(1)
    raise ValueError(f"unparseable Date received: {s!r}")

def _norm_id(cid: str) -> str:
    return cid[:-2] if cid.endswith(".0") else cid   # float-artifact IDs like '21890776.0'

def read_filtered(csv_path: Path, company: str, since: str) -> tuple[list[dict], dict]:
    """Rows for one company from `since` (YYYY-MM-DD), with per-reason drop counts."""
    rows, drops = [], Counter()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Company"] != company:
                drops["wrong_company"] += 1
                continue
            narrative = (r["Consumer complaint narrative"] or "").strip()
            if not narrative:
                drops["empty_narrative"] += 1
                continue
            try:
                date = parse_received(r["Date received"])
            except ValueError:
                drops["bad_date"] += 1
                continue
            if date < since:
                drops["before_window"] += 1
                continue
            rows.append({"complaint_id": _norm_id(r["Complaint ID"]), "date": date,
                         "narrative": narrative, "product": r.get("Product", ""),
                         "issue": r.get("Issue", ""),
                         "outcome": r["Company response to consumer"]})
    # Lexical (string) sort, not numeric — deterministic and reproducible, though
    # surprising for numeric IDs. Dedup "first id wins" and stratified sampling both
    # ride on this order; intentional (reproducibility over numeric intuition).
    rows.sort(key=lambda r: r["complaint_id"])
    return rows, dict(drops)

def dedup_rows(rows: list[dict]) -> tuple[list[dict], int]:
    """R-IDX-9: content-hash dedup before anything counts. First complaint_id wins."""
    seen, kept = set(), []
    for r in sorted(rows, key=lambda r: r["complaint_id"]):
        h = hashlib.sha256(r["narrative"].encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        kept.append(r)
    return kept, len(rows) - len(kept)

def sample_stratified(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Deterministic month-stratified sample: proportional allocation (largest remainder),
    seeded draw within each stratum, output sorted by complaint_id."""
    if n >= len(rows):
        return sorted(rows, key=lambda r: r["complaint_id"])
    strata: dict[str, list[dict]] = {}
    for r in rows:
        strata.setdefault(r["date"][:7], []).append(r)
    total = len(rows)
    quotas = {m: (n * len(v)) / total for m, v in strata.items()}
    alloc = {m: int(q) for m, q in quotas.items()}
    remainder = n - sum(alloc.values())
    for m in sorted(strata, key=lambda m: (-(quotas[m] - alloc[m]), m))[:remainder]:
        alloc[m] += 1
    rng = random.Random(seed)
    out = []
    for m in sorted(strata):
        pool = sorted(strata[m], key=lambda r: r["complaint_id"])
        out.extend(rng.sample(pool, min(alloc[m], len(pool))))
    return sorted(out, key=lambda r: r["complaint_id"])

# Sentence boundary: a `.`/`?`/`!` followed by whitespace and the start of the next
# sentence. The lookahead requires an alphanumeric/quote/paren opener so mid-sentence dots
# — `{$1,234.00}`, `XX/XX/XXXX`, abbreviations — do NOT split (their '.' is followed by a
# digit or '}' , not whitespace+opener).
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_MAX_SNIPPET_CHARS = 600

def segment_narrative(text: str, max_chars: int = _MAX_SNIPPET_CHARS) -> list[str]:
    """Split a monologue complaint into sentence-level segments (one per snippet at
    chunking, R-IDX-1). The frozen evidence gate matches a quote against a WHOLE snippet;
    a single-segment narrative is one giant snippet no excerpt can equal, so synthesis
    quotes all drop (T-DROP release_block). Sentence granularity restores the short,
    quotable-unit shape the gate was built for (a conversational turn). Content is
    preserved in order; over-long run-ons are hard-capped so every snippet stays quotable."""
    segs: list[str] = []
    for part in _SENT_SPLIT.split(text.strip()):
        part = part.strip()
        if not part:
            continue
        while len(part) > max_chars:
            cut = part.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            segs.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            segs.append(part)
    return segs or [text.strip()]

def write_corpus(rows: list[dict], out_dir: Path, company: str, since: str,
                 seed: int, source_csv: str) -> dict:
    """Write the standard corpus layout:
        <out>/units/cfpb-<id>.json      InteractionUnit files (the ONLY thing the pipeline reads)
        <out>/holdout_labels.json       withheld outcome label, sealed sidecar (§3.2)
        <out>/corpus_properties.yaml    §2.3-S record + sampling provenance
    The units dir holds nothing but unit JSON — load_corpus globs *.json in that dir."""
    units_dir = Path(out_dir) / "units"
    units_dir.mkdir(parents=True, exist_ok=False)   # refuse to clobber an existing corpus
    labels = {}
    for r in rows:
        uid = f"cfpb-{r['complaint_id']}"
        labels[uid] = r["outcome"]
        # WITHHOLDING BOUNDARY (§3.2): build the unit from a fixed key set — never spread
        # `r`, or `outcome`/`product`/`issue` would leak into what the pipeline & models read.
        # Segment the monologue into sentences so each becomes one quotable snippet (see
        # segment_narrative) — otherwise the evidence gate can't match excerpt quotes.
        unit = {"id": uid, "source_type": "note", "participants": [],
                "date": r["date"], "account_id": None, "thread_id": None,
                "segments": [{"speaker": None, "ts": None, "text": s}
                             for s in segment_narrative(r["narrative"])]}
        (units_dir / f"{uid}.json").write_text(
            json.dumps(unit, indent=2, ensure_ascii=False), encoding="utf-8")
    (Path(out_dir) / "holdout_labels.json").write_text(
        json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")
    props = {**_CFPB_CORPUS_PROPERTIES,
             "source": {"dataset": "CFPB Consumer Complaint Database (filtered)",
                        "csv": source_csv},
             "sampling": {"company": company, "since": since, "seed": seed,
                          "n": len(rows)}}
    (Path(out_dir) / "corpus_properties.yaml").write_text(
        yaml.safe_dump(props, sort_keys=False), encoding="utf-8")
    return {"units": len(rows), "out": str(out_dir)}
