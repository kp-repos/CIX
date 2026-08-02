import argparse
import json
import sys
from pathlib import Path
import yaml
from cix.aggregate import rollup
from cix.audits import apply_prompts_hash, drop_rate_check, escape_audit, label_self_agreement, paraphrase_audit, second_lab_audit, split_half
from cix.calgen import generate_corpus, load_cal_spec
from cix.calscore import HoldoutError, guard_holdout, log_cycle, record_holdout, score_calibration, score_null
from cix.second_lab import OpenAIClient, load_second_lab_config
from cix.canonical import canonical_hash
from cix.evidence import gate_claims
from cix.gate2 import gate_synthesis
from cix.hits import prompts_hash as hits_ph
from cix.hits import run_rubric
from cix.labels import label_corpus
from cix.labels import prompts_hash as labels_ph
from cix.manifest import build_manifest, write_manifest
from cix.manifest import corpus_hash as manifest_corpus_hash
from cix.model import AnthropicClient
from cix.normalize import CorpusValidationError, load_corpus
from cix.report import render_report
from cix.rubric import DependencyError, load_rubric
from cix.runconfig import load_run_config, load_thresholds
from cix.scrub import load_privacy_protocol, scrub_corpus, audit_privacy_gate
from cix.store import build_store, open_store
from cix.synthesize import prompts_hash as synth_ph
from cix.synthesize import synthesize_findings
from cix.tags import load_vocabulary

# Resolve config relative to the package (repo root), not the process cwd,
# so the installed `cix` command works from any directory.
VOCAB_PATH = Path(__file__).resolve().parents[2] / "configs" / "tag_vocabulary_v1.yaml"

def make_client(config):
    return AnthropicClient(config)

def make_second_client(config):
    return OpenAIClient(config)

def _find_provenance(corpus_dir: Path) -> dict | None:
    for cand in (Path(corpus_dir) / "provenance.yaml", Path(corpus_dir).parent / "provenance.yaml"):
        if cand.exists():
            return yaml.safe_load(cand.read_text(encoding="utf-8"))
    return None

def _cmd_run(args) -> int:
    try:
        units = load_corpus(Path(args.corpus))
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    vocab = load_vocabulary(VOCAB_PATH)
    schema_version = yaml.safe_load(Path("configs/label_schema_v1.yaml").read_text())["version"]
    try:
        rubric = load_rubric(Path(args.rubric), schema_version, vocab["version"])  # AC-5: before any model call
    except DependencyError as e:
        print(f"dependency refusal: {e}", file=sys.stderr)
        return 2
    config = load_run_config(Path("configs/run_config_v1.yaml"))
    thresholds = load_thresholds(Path("configs/thresholds_v1.yaml"))
    thresholds_version = yaml.safe_load(Path("configs/thresholds_v1.yaml").read_text())["version"]
    client = make_client(config)

    # Scrub at ingest — nothing unscrubbed reaches the store (R-PII-1). Runs on cleared/synthetic
    # data too (R-PII-4). Salt is per-run, derived from the run seed for reproducibility.
    proto = load_privacy_protocol(Path("configs/privacy_protocol_v1.yaml"))
    salt = f"cix-{config.seed}"
    units, scrub_report = scrub_corpus(units, proto, salt=salt)
    privacy = audit_privacy_gate(units, proto)
    if privacy["status"] == "fail":
        print(f"privacy gate FAIL: {privacy['residual_hits']} residual PII hits", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "run.db"
    build_store(units, VOCAB_PATH, db)
    store = open_store(db)
    chash = manifest_corpus_hash(units)

    la = label_corpus(store, units, client, chash, schema_version, config.model)
    ha = run_rubric(store, units, rubric, la, client, config.model)
    hits = store.hits_for(ha)
    roll = rollup(hits, eligible_interactions=len(units))

    for r in escape_audit(store, units, rubric, client, thresholds["T-ESC"], seed=config.seed):
        store.write_validation("T-ESC", r["item_id"], r["status"], r["detail"])
    for r in label_self_agreement(store, units, la, client, thresholds["T-AGR"], seed=config.seed,
                                  fields=["motion", "driver_origin", "automatability", "outcome"]):
        store.write_validation("T-AGR", r["field"], r["status"], r["detail"])
    sh = split_half(hits, [u.id for u in units], thresholds["T-SPLIT"], seed=config.seed)
    store.write_validation("T-SPLIT", None, sh["status"], sh["detail"])
    if args.dev_null_control:
        store.write_validation("NULL-CONTROL", None, "dev_only",
                               "development fixture - excluded from threshold-setting and acceptance")

    # T-PARA (stability tier) — honest not_run when no paraphrase set covers this rubric
    para_path = Path("configs/paraphrases_v1.yaml")
    paras = {}
    if para_path.exists():
        pdoc = yaml.safe_load(para_path.read_text(encoding="utf-8"))
        if pdoc.get("rubric_version") == rubric.version:
            paras = pdoc["paraphrases"]
    if paras:
        for r in paraphrase_audit(store, units, rubric, paras, ha, client,
                                  thresholds["T-PARA"], seed=config.seed):
            store.write_validation("T-PARA", r["item_id"], r["status"], r["detail"])
    else:
        store.write_validation("T-PARA", None, "not_run",
                               f"no paraphrase set for rubric {rubric.version}")

    # Second-lab audit seat (adjudication tier) with F4 recusal
    prov = _find_provenance(Path(args.corpus))
    sl_path = Path("configs/second_lab_config_v1.yaml")
    if args.no_audit_seat or not sl_path.exists():
        store.write_validation("SECOND-LAB-SEAT", None, "not_run", "audit seat disabled or unconfigured")
    else:
        slc = load_second_lab_config(sl_path)
        seat_client = None if (prov and prov.get("generator_lab") == slc.lab) else make_second_client(slc)
        r = second_lab_audit(store, units, rubric, ha, seat_client, slc, seed=config.seed,
                             provenance_lab=(prov or {}).get("generator_lab"), seat_lab=slc.lab)
        store.write_validation("SECOND-LAB-SEAT", None, r["status"], r["detail"])

    sid = synthesize_findings(store, roll, hits, client, config.model, seed=config.seed)
    gated = gate_synthesis(store, sid, roll)
    dr = drop_rate_check(gated["candidate_claims"], gated["quote_drops"], gated["stat_drops"],
                         thresholds["T-DROP"])
    store.write_validation("T-DROP", None, dr["status"], dr["detail"])

    polarity = {i.id: i.polarity for i in rubric.items}
    for f in gated["findings"]:
        row = roll["items"].get(f["item_id"], {})
        f["polarity"] = polarity.get(f["item_id"])
        f["unit"], f["share"], f["denominator"] = row.get("unit"), row.get("share"), row.get("denominator")

    manifest = build_manifest(units, canonical_hash(db), vocab["version"],
                              privacy_gate=privacy["status"], corpus_clearance=args.clearance, salt=salt)
    manifest.update({"label_schema_version": schema_version, "rubric_version": rubric.version,
                     "model_versions": {"primary": config.model},
                     "prompt_hashes": {"labels": labels_ph(), "hits": hits_ph(), "synthesis": synth_ph(),
                                       "apply": apply_prompts_hash()},
                     "seeds": {"run": config.seed}, "thresholds_version": thresholds_version,
                     "artifacts": {"labels": la, "hits": ha}})
    write_manifest(manifest, out)
    render_report({"findings": gated["findings"], "rollup": roll,
                   "validations": store.validations(),
                   "drop_summary": {k: gated[k] for k in ("candidate_claims", "quote_drops", "stat_drops")},
                   "manifest": manifest, "catalogue_loaded": False}, out)
    print(json.dumps({"run": str(out), "interactions": len(units),
                      "findings": len(gated["findings"]), "drops": gated["quote_drops"] + gated["stat_drops"],
                      "validations": len(store.validations())}))
    return 0

def _cmd_index(args) -> int:
    try:
        units = load_corpus(Path(args.corpus))          # validates BEFORE any write (R-RUN-1)
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "run.db"
    try:
        build_store(units, VOCAB_PATH, db)          # a run store is written once; never clobbered
    except FileExistsError as e:
        print(f"index aborted: {e} (use a fresh --out directory)", file=sys.stderr)
        return 3
    chash = canonical_hash(db)
    vocab = load_vocabulary(VOCAB_PATH)
    manifest = build_manifest(units, chash, vocab["version"],
                              privacy_gate="synthetic-fixture",
                              corpus_clearance=args.clearance)
    write_manifest(manifest, out)
    print(json.dumps({"run": str(out), "interactions": len(units), "canonical_hash": chash}))
    return 0

def _cmd_hash(args) -> int:
    print(json.dumps({"canonical_hash": canonical_hash(Path(args.run) / "run.db")}))
    return 0

def _cmd_verify(args) -> int:
    store = open_store(Path(args.run) / "run.db")
    claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    result = gate_claims(store, claims)
    dropped = len(store.drops())
    print(json.dumps({"passed": {"quotes": len(result["quotes"]), "stats": len(result["stats"])},
                      "dropped": dropped}))
    return 1 if dropped else 0

def _cmd_generate_calibration(args) -> int:
    spec = load_cal_spec(Path(args.spec))
    slc = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    truth = generate_corpus(spec, args.split, make_second_client(slc), Path(args.out),
                            model_name=slc.model, lab=slc.lab)
    print(json.dumps({"split": args.split, "out": str(args.out), "interactions": len(truth),
                      "planted": sum(1 for t in truth.values() if t)}))
    return 0

def _cmd_calibrate(args) -> int:
    run_dir, cal_dir = Path(args.run), Path(args.calibration)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir} (is this a cix run output dir?)", file=sys.stderr)
        return 2
    truth_path = cal_dir / "truth.json"
    if not truth_path.exists():
        print(f"error: truth.json not found at {truth_path} (wrong --calibration path?)", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in manifest:
        print("error: run manifest has no 'artifacts' key — re-run with the current cix version", file=sys.stderr)
        return 2
    store = open_store(run_dir / "run.db")
    hits = store.hits_for(manifest["artifacts"]["hits"])
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    spec = load_cal_spec(Path(args.spec))
    thresholds = load_thresholds(Path("configs/thresholds_v1.yaml"))
    vocab = load_vocabulary(VOCAB_PATH)
    schema_version = yaml.safe_load(Path("configs/label_schema_v1.yaml").read_text())["version"]
    rubric = load_rubric(Path(args.rubric), schema_version, vocab["version"])
    crosswalk = {p.key: p.maps_to_item for p in spec.pathologies}
    item_units = {i.id: i.unit_of_count for i in rubric.items}
    if args.split == "null":
        res = score_null(sorted(truth), hits, set(crosswalk.values()), thresholds["T-NULL"])
        store.write_validation("T-NULL", None, res["status"], res["detail"])
        report = {"split": "null", "T-NULL": res}
    else:
        if args.split == "holdout":
            try:
                guard_holdout(cal_dir, args.final)
            except HoldoutError as e:
                print(f"refused: {e}", file=sys.stderr)
                return 2
        rows = score_calibration(truth, hits, crosswalk, item_units, thresholds["T-CAL"])
        for r in rows:
            store.write_validation("T-CAL", r["pathology"], r["status"], r["detail"])
        report = {"split": args.split, "T-CAL": rows}
        if args.split == "dev":
            cycle = log_cycle(cal_dir.parent, {"statuses": {r["pathology"]: r["status"] for r in rows}},
                              thresholds["T-ITER"]["max_dev_cycles"])
            report["cycle"] = cycle
            if cycle >= thresholds["T-ITER"]["max_dev_cycles"]:
                print(f"T-ITER: dev cycle {cycle} of {thresholds['T-ITER']['max_dev_cycles']} — "
                      "budget reached; next evaluation is the one-shot holdout (PO decision)", file=sys.stderr)
        else:
            record_holdout(cal_dir, report)
    (run_dir / "calibration_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    failing = [k for k in report.get("T-CAL", []) if k["status"] != "pass"] if args.split != "null" \
        else ([report["T-NULL"]["status"]] if report["T-NULL"]["status"] != "pass" else [])
    print(json.dumps({"split": args.split, "report": str(run_dir / "calibration_report.json"),
                      "failing": len(failing)}))
    return 0

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cix")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_index = sub.add_parser("index", help="build a run store from a corpus directory")
    p_index.add_argument("corpus")
    p_index.add_argument("--out", required=True)
    p_index.add_argument("--clearance", default="n/a: synthetic fixtures")
    p_index.set_defaults(fn=_cmd_index)
    p_hash = sub.add_parser("hash", help="print the canonical hash of a run")
    p_hash.add_argument("run")
    p_hash.set_defaults(fn=_cmd_hash)
    p_verify = sub.add_parser("verify", help="run the evidence gate over a claims file")
    p_verify.add_argument("run")
    p_verify.add_argument("--claims", required=True)
    p_verify.set_defaults(fn=_cmd_verify)
    p_run = sub.add_parser("run", help="full corpus -> report run")
    p_run.add_argument("corpus")
    p_run.add_argument("--rubric", required=True)
    p_run.add_argument("--out", required=True)
    p_run.add_argument("--clearance", default="n/a: synthetic fixtures")
    p_run.add_argument("--dev-null-control", action="store_true")
    p_run.add_argument("--no-audit-seat", action="store_true")
    p_run.set_defaults(fn=_cmd_run)
    p_gen = sub.add_parser("generate-calibration", help="generate a calibration split via the second lab (live)")
    p_gen.add_argument("--spec", required=True)
    p_gen.add_argument("--split", required=True, choices=["dev", "holdout", "null"])
    p_gen.add_argument("--out", required=True)
    p_gen.set_defaults(fn=_cmd_generate_calibration)
    p_cal = sub.add_parser("calibrate", help="score a run against a calibration truth registry")
    p_cal.add_argument("run")
    p_cal.add_argument("--calibration", required=True, help="split dir containing truth.json")
    p_cal.add_argument("--split", required=True, choices=["dev", "holdout", "null"])
    p_cal.add_argument("--spec", default="configs/calibration_spec_v1.yaml")
    p_cal.add_argument("--rubric", default="configs/sales_rubric_v1.yaml")
    p_cal.add_argument("--final", action="store_true")
    p_cal.set_defaults(fn=_cmd_calibrate)
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
