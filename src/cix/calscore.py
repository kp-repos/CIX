"""Calibration scorer (G3): planted truth vs recovered hits, null false-report rate,
holdout one-shot guard, and the T-ITER cycle log. Detector-side code — may read the
rubric; never imported by calgen."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

class HoldoutError(Exception):
    pass

def score_calibration(truth: dict, hits: list[dict], crosswalk: dict[str, str],
                      item_units: dict[str, str], cfg: dict) -> list[dict]:
    per_int: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for h in hits:
        per_int[h["interaction_id"]][h["item_id"]] += 1
    target_items = set(crosswalk.values())
    gated = {"loud", "moderate"}
    rows = []
    for pathology in sorted({t["pathology"] for t in truth.values() if t}):
        item = crosswalk[pathology]
        expected = recovered = detected_any = attributed = 0
        det = {lvl: [0, 0] for lvl in ("loud", "moderate", "camouflaged")}
        for uid, t in truth.items():
            if not t or t["pathology"] != pathology:
                continue
            got = per_int[uid].get(item, 0)
            det[t["loudness"]][0] += 1 if got else 0
            det[t["loudness"]][1] += 1
            if t["loudness"] in gated:
                expected += t["expected_occurrences"] if item_units[item] == "occurrence" else 1
                recovered += got
            hit_targets = [i for i in per_int[uid] if i in target_items]
            if hit_targets:
                detected_any += 1
                attributed += 1 if item in hit_targets else 0
        abs_err = abs(recovered - expected)
        rel_err = abs_err / expected if expected else 0.0
        count_fail = rel_err > cfg["relative_error_max"] and abs_err > cfg["absolute_error_max"]
        attr_rate = (attributed / detected_any) if detected_any else None
        mech_fail = attr_rate is not None and attr_rate < cfg["mechanism_attribution_floor"]
        status = "fail" if count_fail else ("mechanism_fail" if mech_fail else "pass")
        rows.append({
            "pathology": pathology, "item_id": item, "status": status,
            "expected": expected, "recovered": recovered,
            "abs_error": abs_err, "rel_error": round(rel_err, 3),
            "attribution": None if attr_rate is None else round(attr_rate, 3),
            "detection_by_loudness": det,
            "detail": (f"expected {expected}, recovered {recovered} (rel {rel_err:.2f}, abs {abs_err}); "
                       f"attribution {attr_rate if attr_rate is not None else 'n/a'}; "
                       f"camouflaged {det['camouflaged'][0]}/{det['camouflaged'][1]} (ungated)"),
        })
    return rows

def score_null(null_ids: list[str], hits: list[dict], target_items: set[str], cfg: dict) -> dict:
    n = len(null_ids)
    if n < cfg["min_null_interactions"]:
        return {"status": "insufficient_power", "rate_per_100": None,
                "detail": f"null set {n} < {cfg['min_null_interactions']}"}
    null_set = set(null_ids)
    flagged: set[str] = set()
    for h in hits:
        if h["interaction_id"] in null_set and h["item_id"] in target_items:
            flagged.add(h["interaction_id"])
    rate = len(flagged) / n * 100
    status = "fail" if rate > cfg["false_reports_per_100_max"] else "pass"
    return {"status": status, "rate_per_100": round(rate, 1),
            "detail": f"{len(flagged)} false-report interaction(s) in n={n} -> {rate:.1f}/100 "
                      f"(pre-registered floor {cfg['false_reports_per_100_max']}/100; empirical rate reported, floor is the gate)"}

def guard_holdout(split_dir: Path, final: bool) -> None:
    """T-ITER: exactly one predeclared holdout evaluation, mechanically enforced.
    A passing guard CLAIMS the single evaluation by writing the .evaluated marker
    immediately — so a crash before record_holdout cannot reopen the one shot.
    record_holdout later overwrites the marker with the full report."""
    marker = Path(split_dir) / ".evaluated"
    if not final:
        raise HoldoutError("holdout scoring requires --final (one predeclared evaluation, T-ITER)")
    if marker.exists():
        raise HoldoutError(f"holdout already evaluated ({marker.read_text(encoding='utf-8').splitlines()[0]}) "
                           "- T-ITER allows exactly one evaluation")
    marker.write_text(datetime.now(timezone.utc).isoformat() + "\nclaimed (evaluation in progress)\n",
                      encoding="utf-8")

def record_holdout(split_dir: Path, report: dict) -> None:
    (Path(split_dir) / ".evaluated").write_text(
        datetime.now(timezone.utc).isoformat() + "\n" + json.dumps(report, indent=2), encoding="utf-8")

def log_cycle(cal_root: Path, summary: dict, max_cycles: int) -> int:
    """Append one dev-scoring cycle to the register history; returns the cycle number."""
    path = Path(cal_root) / "cycles.json"
    log = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    log.append({"cycle": len(log) + 1, "max_cycles": max_cycles,
                "at": datetime.now(timezone.utc).isoformat(), "summary": summary})
    path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    return len(log)
