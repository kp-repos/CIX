import argparse
import json
import sys
from pathlib import Path
from cix.canonical import canonical_hash
from cix.evidence import gate_claims
from cix.manifest import build_manifest, write_manifest
from cix.normalize import CorpusValidationError, load_corpus
from cix.store import build_store, open_store
from cix.tags import load_vocabulary

VOCAB_PATH = Path("configs/tag_vocabulary_v1.yaml")

def _cmd_index(args) -> int:
    try:
        units = load_corpus(Path(args.corpus))          # validates BEFORE any write (R-RUN-1)
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "run.db"
    build_store(units, VOCAB_PATH, db)
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
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
