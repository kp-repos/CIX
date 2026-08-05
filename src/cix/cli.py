import argparse
import json
import sys
from pathlib import Path
import yaml
from cix.differential import delete_subset, duplicate_chains, splice_instances, score_delta
from cix.aggregate import rollup
from cix.audits import apply_prompts_hash, drop_rate_check, escape_audit, label_self_agreement, paraphrase_audit, second_lab_audit, split_half
from cix.calgen import generate_corpus, load_cal_spec
from cix.servicegen import generate_service_corpus, load_service_spec
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
from cix.normalize import CorpusValidationError, load_corpus, load_corpus_properties
from cix.catalogue import load_catalogue, join_swaps, leverage_grid
from cix.priced import priced_view
from cix.report import render_report
from cix.rubric import DependencyError, load_paraphrase_set, load_rubric, split_by_corpus_fit
from cix.runconfig import load_run_config, load_thresholds
from cix.scrub import load_privacy_protocol, scrub_corpus, audit_privacy_gate
from cix.selftest import load_selftest_spec, self_test
from cix.query import find_quote, resolve_item, resolve_metric
from cix.briefing import load_presentation
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

def _detect(store, units, rubric, client, chash, schema_version, model):
    """Pass-A detection (labels -> rubric hits -> rollup). The ONE detection code path,
    shared by `cix run` and `cix differential` (G5 rehearsal spec §2.3)."""
    la = label_corpus(store, units, client, chash, schema_version, model)
    ha = run_rubric(store, units, rubric, la, client, model)
    hits = store.hits_for(ha)
    return la, ha, hits, rollup(hits, eligible_interactions=len(units))

def _cmd_run(args) -> int:
    try:
        units = load_corpus(Path(args.corpus))
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    corpus_props = load_corpus_properties(Path(args.corpus))
    vocab = load_vocabulary(VOCAB_PATH)
    schema_version = yaml.safe_load(Path("configs/label_schema_v1.yaml").read_text())["version"]
    try:
        rubric = load_rubric(Path(args.rubric), schema_version, vocab["version"])  # AC-5: before any model call
    except DependencyError as e:
        print(f"dependency refusal: {e}", file=sys.stderr)
        return 2
    # R-SPK-3 / §2.3-S: gate the rubric on corpus properties BEFORE any model call, so
    # speaker-dependent items on a speakerless corpus never reach detection (they are
    # skipped-and-reported below, once the store exists, and excluded from denominators).
    rubric, skipped_items = split_by_corpus_fit(rubric, corpus_props)
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
    for it in skipped_items:
        store.write_validation("CORPUS-FIT", it.id, "skipped",
                               f"requires_speaker=true but corpus speaker_attribution="
                               f"{corpus_props.get('speaker_attribution')} — skipped per §2.3-S, "
                               "excluded from coverage denominators")
    chash = manifest_corpus_hash(units)

    la, ha, hits, roll = _detect(store, units, rubric, client, chash, schema_version, config.model)

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

    # T-PARA (stability tier) — pick the frozen paraphrase set bound to this rubric;
    # honest not_run when none covers it (see rubric.load_paraphrase_set).
    paras = load_paraphrase_set(Path(args.rubric), rubric.version)
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

    # Pass B — catalogue join + priced view (R-ARCH-2: never suppresses Pass A above).
    # A unit-incompatible join drops that claim and is logged; the rest still price (R-CAT-3).
    # swap_ref is single-valued today (1 remedy per item); multi-remedy alternatives is a G5+ path.
    cat_path = Path(args.catalogue) if getattr(args, "catalogue", None) else None
    catalogue_loaded = False
    catalogue_version = None
    priced_section = {"plays": [], "note": "No catalogue loaded — no priced view in this run."}
    leverage_section = None
    if cat_path and cat_path.exists():
        cat = load_catalogue(cat_path)
        catalogue_version = cat.version
        crosswalk = {i.id: i.swap_ref for i in rubric.items}
        joined = join_swaps(roll["items"], crosswalk, cat)
        for d in joined["dropped"]:
            store.log_drop("priced-view", "unit-compatibility", d["reason"])
            store.write_validation("PASS-B", d["item_id"], "unit_incompat", d["reason"])
        grid = leverage_grid(joined["priced"], cat)
        priced_section = priced_view(joined["priced"])
        leverage_section = {"grid": grid["cells"], "shelf": joined["shelf"],
                            "class_d": grid["class_d"], "note": f"catalogue {cat.version}"}
        catalogue_loaded = True

    manifest = build_manifest(units, canonical_hash(db), vocab["version"],
                              privacy_gate=privacy["status"], corpus_clearance=args.clearance, salt=salt)
    manifest.update({"label_schema_version": schema_version, "rubric_version": rubric.version,
                     "rubric_file": Path(args.rubric).name,
                     "model_versions": {"primary": config.model},
                     "prompt_hashes": {"labels": labels_ph(), "hits": hits_ph(), "synthesis": synth_ph(),
                                       "apply": apply_prompts_hash()},
                     "seeds": {"run": config.seed}, "thresholds_version": thresholds_version,
                     "corpus_properties": corpus_props,
                     # promoted mirror of corpus_properties.substrate_class for downstream gating
                     "substrate_class": corpus_props["substrate_class"],
                     "skipped_items": [i.id for i in skipped_items],
                     "artifacts": {"labels": la, "hits": ha}})
    manifest["privacy_scan"] = {"residual_scope": privacy["scan_scope"], "ner": privacy["ner"]}
    manifest["catalogue_version"] = catalogue_version
    write_manifest(manifest, out)
    render_report({"findings": gated["findings"], "rollup": roll,
                   "validations": store.validations(),
                   "drop_summary": {k: gated[k] for k in ("candidate_claims", "quote_drops", "stat_drops")},
                   "manifest": manifest, "catalogue_loaded": catalogue_loaded,
                   "drops": store.drops(),
                   "priced_plays": priced_section,
                   "leverage": leverage_section or {"grid": [], "shelf": [], "class_d": [], "note": ""}},
                  out)
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

def _cmd_cfpb_ingest(args) -> int:
    """CFPB CSV -> corpus adapter (spec 2026-08-05 §3). Writes <out>/units + sealed
    holdout_labels.json + corpus_properties.yaml. The outcome label never enters units."""
    from cix.cfpb import read_filtered, dedup_rows, sample_stratified, write_corpus, parse_received
    try:
        since = parse_received(args.since)
    except ValueError:
        print(f"ingest aborted: --since must be YYYY-MM-DD, got {args.since!r}", file=sys.stderr)
        return 2
    rows, drops = read_filtered(Path(args.csv), company=args.company, since=since)
    rows, n_dupes = dedup_rows(rows)
    picked = sample_stratified(rows, n=args.n, seed=args.seed)
    try:
        res = write_corpus(picked, Path(args.out), company=args.company,
                           since=since, seed=args.seed, source_csv=str(args.csv))
    except FileExistsError:
        print(f"ingest aborted: {args.out} already contains a corpus (use a fresh --out)",
              file=sys.stderr)
        return 3
    print(json.dumps({"written": res["units"], "eligible": len(rows),
                      "duplicates_collapsed": n_dupes, "drops": drops,
                      "out": res["out"]}))
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

def _cmd_query(args) -> int:
    """Live evidence resolution for the demo (R-OUT-2). Read-only over the run store:
    resolve a finding's count to its source interactions, or a pasted quote to its snippet."""
    run = Path(args.run)
    store = open_store(run / "run.db", read_only=True)  # writes impossible, not merely avoided
    if args.quote is not None:
        matches = find_quote(store, args.quote)
        if not matches:
            print(f'quote does NOT resolve to any stored source:\n  "{args.quote}"')
            return 1
        print(f'quote resolves to {len(matches)} snippet(s):')
        for s in matches:
            print(f"  {s['id']}  (interaction {s['interaction_id']}, seq {s['seq']})")
        return 0
    if getattr(args, "metric", None) is not None:
        report = json.loads((run / "report.json").read_text(encoding="utf-8"))
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        eligible = report["sections"]["distribution"]["eligible_interactions"]
        presentation = load_presentation(Path(args.presentation))
        res = resolve_metric(store, manifest, presentation, args.metric, eligible)
        if not res["found"]:
            print(f'metric "{args.metric}" does NOT resolve — unknown headline metric')
            return 1
        print(f"{res['metric']}: {res['value']} / {res['denominator']} "
              f"(members: {', '.join(res['members'])})")
        for iid in res["interaction_ids"]:
            print(f"  {iid}")
        return 0
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    res = resolve_item(store, report, manifest, args.item)
    if not res["found"]:
        print(f'finding "{args.item}" does NOT resolve — no such item in this run\'s highlights')
        return 1
    print(f"{res['item_id']}: count {res['count']} (share {res['share']})")
    print(f"  {res['narrative']}")
    for h in res["hits"]:
        print(f"  hit {h['snippet_ids']}:")
        for s in h["snippets"]:
            print(f"    [{s['id']}] {s['text']}")
    for q in res["quotes"]:
        mark = "verbatim OK" if q["verbatim"] else "does NOT resolve"
        print(f"  quote ({mark}): \"{q['text']}\"")
    return 0

def _cmd_briefing(args) -> int:
    """Business briefing (model-free presentation layer). Read-only over a persisted run:
    build briefing.json + briefing.html (+ briefing.pdf unless --no-pdf)."""
    from cix.briefing import build_briefing, render_briefing_html, render_briefing_pdf
    run = Path(args.run)
    for req in ("run.db", "report.json", "manifest.json"):
        if not (run / req).exists():
            print(f"briefing failed closed: missing persisted artifact {run / req}")
            return 1
    store = open_store(run / "run.db", read_only=True)  # writes impossible, not merely avoided
    cfg = load_presentation(Path(args.presentation))
    try:
        # A present-but-corrupt/incompatible artifact (bad JSON -> ValueError, missing
        # structure -> KeyError, honesty-rule violation -> ValueError) fails closed with a
        # message, not a traceback (spec §3.3). JSONDecodeError is a ValueError subclass.
        report = json.loads((run / "report.json").read_text(encoding="utf-8"))
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        briefing = build_briefing(report, manifest, cfg, store)
    except (ValueError, KeyError) as e:
        print(f"briefing failed closed: {e}")
        return 1
    (run / "briefing.json").write_text(json.dumps(briefing, indent=2, ensure_ascii=False), encoding="utf-8")
    html = render_briefing_html(briefing)
    (run / "briefing.html").write_text(html, encoding="utf-8")
    if not args.no_pdf:
        try:
            render_briefing_pdf(html, run / "briefing.pdf")
        except (OSError, ImportError) as e:
            # briefing.json + briefing.html are already written and valid; only the PDF needs
            # WeasyPrint's system libraries. Fail closed with a hint instead of crashing.
            print(f"briefing failed closed: PDF render unavailable ({e}); "
                  "briefing.json + briefing.html written — re-run with --no-pdf to skip the PDF")
            return 1
    metrics = {k: v["value"] for k, v in briefing["headline"].items()
               if isinstance(v, dict) and "value" in v and k != "automatable_opportunity"}
    print(json.dumps({"run": str(run), "headline": metrics, "pdf": (not args.no_pdf)}))
    return 0

def _cmd_generate_calibration(args) -> int:
    spec = load_cal_spec(Path(args.spec))
    slc = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    truth = generate_corpus(spec, args.split, make_second_client(slc), Path(args.out),
                            model_name=slc.model, lab=slc.lab)
    print(json.dumps({"split": args.split, "out": str(args.out), "interactions": len(truth),
                      "planted": sum(1 for t in truth.values() if t)}))
    return 0

def _cmd_generate_service(args) -> int:
    spec = load_service_spec(Path(args.spec))
    slc = load_second_lab_config(Path("configs/second_lab_config_v1.yaml"))
    truth = generate_service_corpus(spec, make_second_client(slc), Path(args.out),
                                    model_name=slc.model, lab=slc.lab)
    print(json.dumps({"out": str(args.out), "interactions": len(truth),
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

def _cmd_selftest(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir} (is this a cix run output dir?)", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in manifest:
        print("error: run manifest has no 'artifacts' key — re-run with the current cix version", file=sys.stderr)
        return 2
    spec = load_selftest_spec(Path(args.spec))
    store = open_store(run_dir / "run.db")
    hits = store.hits_for(manifest["artifacts"]["hits"])
    all_ids = store.labeled_interactions(manifest["artifacts"]["labels"])
    catalogue = crosswalk = None
    if args.catalogue and args.rubric:
        catalogue = load_catalogue(Path(args.catalogue))
        rubric = load_rubric(Path(args.rubric), manifest["label_schema_version"],
                             manifest["tag_vocab_version"])
        crosswalk = {i.id: i.swap_ref for i in rubric.items}
    res = self_test(all_ids, hits, spec, catalogue=catalogue, crosswalk=crosswalk)
    outcome_level = {"S1": "O3-eligible",
                     "S2": "O3-corpus-level-items-only"}.get(
        manifest.get("substrate_class"), "O1-synthetic")
    store.write_validation("T-SST", None, res["state"],
                           f"material_fraction={res['material_fraction']} "
                           f"layers={','.join(res['layers_compared'])} spec={spec.version} "
                           f"outcome_level={outcome_level}")
    report = {"spec_version": spec.version, **res}
    (run_dir / "selftest_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"state": res["state"], "material_fraction": res["material_fraction"],
                      "layers_compared": res["layers_compared"],
                      "report": str(run_dir / "selftest_report.json")}))
    return 0

def _target_contribution(t_hits: list[dict], unit_basis: str, interaction_ids: set[str]) -> int:
    """Count the target-item contribution of a set of interactions, respecting the item's
    unit_of_count (interaction: distinct flagged interactions; occurrence: hit rows)."""
    if unit_basis == "interaction":
        return len({h["interaction_id"] for h in t_hits} & interaction_ids)
    return sum(1 for h in t_hits if h["interaction_id"] in interaction_ids)

def _cmd_differential(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json in {run_dir} (is this a cix run output dir?)", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in manifest:
        print("error: run manifest has no 'artifacts' key — re-run with the current cix version", file=sys.stderr)
        return 2
    try:
        units = load_corpus(Path(args.corpus))
    except CorpusValidationError as e:
        print(f"corpus validation failed: {e}", file=sys.stderr)
        return 2
    # Reload + integrity check (rehearsal spec §3.3 step 0): re-scrub with the persisted
    # salt, refuse unless the recomputed hash matches the base run's manifest.
    proto = load_privacy_protocol(Path("configs/privacy_protocol_v1.yaml"))
    units, _ = scrub_corpus(units, proto, salt=manifest["scrub_salt"])
    if manifest_corpus_hash(units) != manifest["corpus_hash"]:
        print("refused: corpus_hash mismatch — --corpus is not the corpus the base run saw", file=sys.stderr)
        return 2
    # Fail fast before any variant work: per-variant stores are built under differential/,
    # and build_store refuses an existing path — a re-run over a stale dir would crash mid-loop
    # and leave duplicated T-DIFF rows. Match the _cmd_index guard: refuse up front.
    diff_dir = run_dir / "differential"
    if diff_dir.exists():
        print(f"error: {diff_dir} already exists — delete it to re-run differential", file=sys.stderr)
        return 2
    store = open_store(run_dir / "run.db")
    base_hits = store.hits_for(manifest["artifacts"]["hits"])
    design = yaml.safe_load(Path(args.design).read_text(encoding="utf-8"))
    rubric = load_rubric(Path(args.rubric), manifest["label_schema_version"],
                         manifest["tag_vocab_version"])
    unit_basis_of = {i.id: i.unit_of_count for i in rubric.items}
    config = load_run_config(Path("configs/run_config_v1.yaml"))
    client = make_client(config)
    base_roll = rollup(base_hits, eligible_interactions=len(units))
    rows = []
    for v in design["variants"]:
        item = v["target_item"]
        unit_basis = unit_basis_of[item]
        base_count = base_roll["items"].get(item, {}).get("count", 0)
        t_hits = [h for h in base_hits if h["item_id"] == item]
        flagged = sorted({h["interaction_id"] for h in t_hits})
        if not flagged:
            store.write_validation("T-DIFF", v["id"], "not_run",
                                   f"no {item} hits in the base run — variant not constructible")
            rows.append({"id": v["id"], "status": "not_run", "expected": None, "observed": None})
            continue
        if v["perturbation"] == "delete_subset":
            ids = set(flagged[:v["delete_count"]])
            variant_units, _meta = delete_subset(units, ids)
            expected = _target_contribution(t_hits, unit_basis, ids)      # count drops by this
        elif v["perturbation"] == "duplicate_chains":
            tid_of = {u.id: u.thread_id for u in units}
            per_thread: dict[str, set[str]] = {}
            for h in t_hits:
                tid = tid_of.get(h["interaction_id"])
                if tid:
                    per_thread.setdefault(tid, set()).add(h["interaction_id"])
            if not per_thread:
                store.write_validation("T-DIFF", v["id"], "not_run",
                                       f"no {item} hits inside any thread — variant not constructible")
                rows.append({"id": v["id"], "status": "not_run", "expected": None, "observed": None})
                continue
            thread_id = max(sorted(per_thread), key=lambda t: len(per_thread[t]))
            member_ids = {u.id for u in units if u.thread_id == thread_id}
            variant_units, _meta = duplicate_chains(units, thread_id)
            expected = _target_contribution(t_hits, unit_basis, member_ids)  # count rises by this
        elif v["perturbation"] == "splice_instances":
            per_donor = {uid: _target_contribution(t_hits, unit_basis, {uid}) for uid in flagged}
            donor_id = max(sorted(per_donor), key=lambda u: per_donor[u])
            donor = next(u for u in units if u.id == donor_id)
            variant_units, _meta = splice_instances(units, donor, v["splice_copies"])
            expected = per_donor[donor_id] * v["splice_copies"]           # count rises by this
        else:
            print(f"error: unknown perturbation {v['perturbation']!r} in design", file=sys.stderr)
            return 2
        vdir = run_dir / "differential" / v["id"]
        vdir.mkdir(parents=True, exist_ok=True)
        build_store(variant_units, VOCAB_PATH, vdir / "run.db")
        vstore = open_store(vdir / "run.db")
        chash_v = manifest_corpus_hash(variant_units)
        _la, _ha, _vhits, vroll = _detect(vstore, variant_units, rubric, client,
                                          chash_v, manifest["label_schema_version"], config.model)
        variant_count = vroll["items"].get(item, {}).get("count", 0)
        observed = abs(variant_count - base_count)
        direction_ok = (variant_count < base_count) if v["perturbation"] == "delete_subset" \
            else (variant_count > base_count) if expected else (variant_count == base_count)
        res = score_delta({"count": expected}, {"count": observed}, v["tolerance"])
        if not direction_ok:
            res["status"] = "fail"
        detail = (f"{item} base={base_count} variant={variant_count} expected_delta={expected} "
                  f"rel_err={res['rel_error']} direction_ok={direction_ok} outcome_level=O1-synthetic")
        store.write_validation("T-DIFF", v["id"], res["status"], detail)
        rows.append({"id": v["id"], "status": res["status"], "expected": expected,
                     "observed": observed, "rel_error": res["rel_error"],
                     "tolerance": v["tolerance"], "detail": detail})
    report = {"design_version": design["version"], "variants": rows}
    (run_dir / "differential_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    failing = sum(1 for r in rows if r["status"] == "fail")
    print(json.dumps({"variants": len(rows), "failing": failing,
                      "report": str(run_dir / "differential_report.json")}))
    return 1 if failing else 0

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cix")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_index = sub.add_parser("index", help="build a run store from a corpus directory")
    p_index.add_argument("corpus")
    p_index.add_argument("--out", required=True)
    p_index.add_argument("--clearance", default="n/a: synthetic fixtures")
    p_index.set_defaults(fn=_cmd_index)
    p_cfpb = sub.add_parser("cfpb-ingest",
                            help="CFPB filtered CSV -> corpus dir (units/ + sealed labels + S2 properties)")
    p_cfpb.add_argument("csv")
    p_cfpb.add_argument("--company", required=True, help='exact CSV value, e.g. "Block, Inc."')
    p_cfpb.add_argument("--since", required=True, help="YYYY-MM-DD window start")
    p_cfpb.add_argument("--n", type=int, required=True, help="sample size")
    p_cfpb.add_argument("--seed", type=int, required=True)
    p_cfpb.add_argument("--out", required=True)
    p_cfpb.set_defaults(fn=_cmd_cfpb_ingest)
    p_hash = sub.add_parser("hash", help="print the canonical hash of a run")
    p_hash.add_argument("run")
    p_hash.set_defaults(fn=_cmd_hash)
    p_verify = sub.add_parser("verify", help="run the evidence gate over a claims file")
    p_verify.add_argument("run")
    p_verify.add_argument("--claims", required=True)
    p_verify.set_defaults(fn=_cmd_verify)
    p_query = sub.add_parser("query", help="resolve a finding's count or a pasted quote to its scrubbed source (read-only)")
    p_query.add_argument("run")
    q_grp = p_query.add_mutually_exclusive_group(required=True)
    q_grp.add_argument("--item", help="rubric item_id: show every source snippet behind the finding's count")
    q_grp.add_argument("--quote", help="reverse lookup: which stored snippet(s) match this text verbatim")
    q_grp.add_argument("--metric", help="headline metric name: list the interaction set behind it")
    p_query.add_argument("--presentation", default="configs/briefing_presentation_v1.yaml",
                         help="presentation config used by --metric (declares metric membership)")
    p_query.set_defaults(fn=_cmd_query)
    p_brief = sub.add_parser("briefing", help="render a business-facing briefing from a persisted run (read-only)")
    p_brief.add_argument("run")
    p_brief.add_argument("--presentation", default="configs/briefing_presentation_v1.yaml")
    p_brief.add_argument("--no-pdf", action="store_true", help="skip the PDF (no WeasyPrint needed)")
    p_brief.set_defaults(fn=_cmd_briefing)
    p_run = sub.add_parser("run", help="full corpus -> report run")
    p_run.add_argument("corpus")
    p_run.add_argument("--rubric", required=True)
    p_run.add_argument("--out", required=True)
    p_run.add_argument("--clearance", default="n/a: synthetic fixtures")
    p_run.add_argument("--dev-null-control", action="store_true")
    p_run.add_argument("--no-audit-seat", action="store_true")
    p_run.add_argument("--catalogue", default=None, help="path to swap catalogue (A5); enables Pass B")
    p_run.set_defaults(fn=_cmd_run)
    p_gen = sub.add_parser("generate-calibration", help="generate a calibration split via the second lab (live)")
    p_gen.add_argument("--spec", required=True)
    p_gen.add_argument("--split", required=True, choices=["dev", "holdout", "null"])
    p_gen.add_argument("--out", required=True)
    p_gen.set_defaults(fn=_cmd_generate_calibration)
    p_svc = sub.add_parser("generate-service-corpus",
                           help="generate the synthetic FS-shaped service corpus via the second lab (O1-only)")
    p_svc.add_argument("--spec", required=True)
    p_svc.add_argument("--out", required=True)
    p_svc.set_defaults(fn=_cmd_generate_service)
    p_cal = sub.add_parser("calibrate", help="score a run against a calibration truth registry")
    p_cal.add_argument("run")
    p_cal.add_argument("--calibration", required=True, help="split dir containing truth.json")
    p_cal.add_argument("--split", required=True, choices=["dev", "holdout", "null"])
    p_cal.add_argument("--spec", default="configs/calibration_spec_v1.yaml")
    p_cal.add_argument("--rubric", default="configs/sales_rubric_v1.yaml")
    p_cal.add_argument("--final", action="store_true")
    p_cal.set_defaults(fn=_cmd_calibrate)
    p_st = sub.add_parser("self-test", help="full-vs-10% self-test (§7, R-VAL-5) over a completed run")
    p_st.add_argument("run")
    p_st.add_argument("--spec", default="configs/selftest_spec_v1.yaml")
    p_st.add_argument("--catalogue", default=None, help="enables the band_movement layer (with --rubric)")
    p_st.add_argument("--rubric", default=None, help="supplies the swap_ref crosswalk for band_movement")
    p_st.set_defaults(fn=_cmd_selftest)
    p_diff = sub.add_parser("differential",
                            help="construct the predeclared variants, re-run detection, score vs T-DIFF (R-VAL-7)")
    p_diff.add_argument("run", help="base run dir (output of cix run)")
    p_diff.add_argument("--corpus", required=True, help="the corpus dir the base run ingested")
    p_diff.add_argument("--design", default="configs/differential_design_v1.yaml")
    p_diff.add_argument("--rubric", required=True)
    p_diff.set_defaults(fn=_cmd_differential)
    args = p.parse_args(argv)
    return args.fn(args)

if __name__ == "__main__":
    raise SystemExit(main())
