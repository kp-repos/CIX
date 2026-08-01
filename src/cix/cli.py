import argparse
import json
import sys
from pathlib import Path
import yaml
from cix.aggregate import rollup
from cix.audits import drop_rate_check, escape_audit, label_self_agreement, split_half
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
from cix.store import build_store, open_store
from cix.synthesize import prompts_hash as synth_ph
from cix.synthesize import synthesize_findings
from cix.tags import load_vocabulary

# Resolve config relative to the package (repo root), not the process cwd,
# so the installed `cix` command works from any directory.
VOCAB_PATH = Path(__file__).resolve().parents[2] / "configs" / "tag_vocabulary_v1.yaml"

def make_client(config):
    return AnthropicClient(config)

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
    client = make_client(config)

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
                              privacy_gate="synthetic-fixture", corpus_clearance=args.clearance)
    manifest.update({"label_schema_version": schema_version, "rubric_version": rubric.version,
                     "model_versions": {"primary": config.model},
                     "prompt_hashes": {"labels": labels_ph(), "hits": hits_ph(), "synthesis": synth_ph()},
                     "seeds": {"run": config.seed}, "thresholds_version": "1.0.0"})
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
    p_run.set_defaults(fn=_cmd_run)
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
