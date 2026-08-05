# CIX O1 demo runbook — `runs/svc-run/`

The exact walkthrough for an internal O1 demo. Everything runs on the existing synthetic
artifacts in `runs/svc-run/` — no model spend. This is **O1 only** (pipeline demo-ready);
never presented as O2 or O3. See `docs/method.md` for the one-page trust story and
`CIX_PRD_v1_2026-07-31.md` §2.3 for the honesty ladder.

**Before the room:** open `runs/svc-run/report.pdf`, and have a terminal at the repo root.
Do a silent dry-run of the two `cix query` commands below so nothing surprises you live.

---

## 1. Open the report (`report.pdf`)

Narrate the six sections in attention order (PRD §4.8, R-OUT-1):

1. **Highlights** — the headline findings and their counts.
2. **What's working** — the positive-polarity findings.
3. **Leverage** — the leverage grid + shelf (this run has no catalogue loaded, so
   everything sits on the "no known remedy yet" shelf — say so; it's honest).
4. **Priced plays** — none in this run (no catalogue), noted in place.
5. **Distribution + coverage** — the full item distribution and interaction coverage.
6. **Method** — the per-run audit trail: validations, drop summary, manifest.

## 2. Live traceability — count resolves to source

This is the R-OUT-2 moment: a claim resolves to its scrubbed source in under a minute.

```
uv run cix query runs/svc-run --item first_contact_resolution
```

It prints the finding (count **82**, share 0.82) and then the **actual source
interactions behind that count** — real scrubbed transcript text, snippet by snippet,
from the `hits` table. The command is read-only (the store is opened `mode=ro`), so it
cannot alter the run.

Backup item if you want a second one: `--item manual_after_call_work` (count 87).

## 2b. The business briefing — same run, commercial view

```
uv run cix briefing runs/svc-run
```

Opens `runs/svc-run/briefing.html` (and `briefing.pdf`): one headline number — **33 of 100
contacts matched at least one avoidable pattern** (a distinct-interaction union, resolvable
with `cix query runs/svc-run --metric avoidable_contact_rate`), the three low-effort automatable
plays with an indicative **$4,040–$12,120/yr** band (inferred, not operator-confirmed), and the
same O1 honesty banner. The technical `report.pdf` remains the audit deliverable; this is the
first-engagement view rendered from the same persisted run.

## 3. The gate is real — a bad quote fails closed

```
uv run cix query runs/svc-run --quote "text that is not in the corpus"
```

Prints `quote does NOT resolve to any stored source` and exits non-zero. The evidence gate
is drop-don't-flag (PRD §4.6): text that isn't verbatim in the store gets nothing.

Then resolve a real line to show the other direction:

```
uv run cix query runs/svc-run --quote "No, that's it. Thanks for the quick help."
```

Prints the snippet ID(s) it matches verbatim.

## 4. The instrument measures something

- **Self-test** — `runs/svc-run/selftest_report.json` has `state: material-advantage`:
  the whole-corpus reading beats the 10% sample, exactly what a real signal looks like
  (PRD §7, R-VAL-5).
- **Differential** — `runs/svc-run/differential_report.json` shows all three predeclared
  variants passing: **V1-delete, V2-duplicate, V3-splice** (design version 1.0.1). Inject
  a known delta, the readings track it (R-VAL-7).

## 5. The honesty script (say this out loud)

> "This is **O1** on synthetic service language — the manifest says
> `synthetic service rehearsal corpus — O1 only, never O2/O3`. Two honest footnotes.
> First, **T-PARA reads `not_run`** in the report's Method section (the validations list)
> because these artifacts predate the service paraphrase freeze (PR #8); the next run
> lights it up.
> Second, **these findings carry no quote-level evidence** — demo prep uncovered an
> evidence-sampling defect where snippet ranges never reached the synthesis model, so it
> was handed nothing and honestly claimed nothing (that's why the drop log is empty —
> nothing fabricated got through). The defect is fixed; the next run's findings will carry
> gated quotes. What you just saw resolve live is the **count → source** path through the
> hits table, which is solid today.
> **O2 and O3** — the real gated run and the hypothesis test — are one real run away,
> blocked only on the FS corpus (OD-1). The instrument itself is frozen and calibrated:
> **6/6 T-CAL, 0/100 T-NULL** (PRD changelog, G3 exit)."

---

## Verification checklist (run before the demo)

- [ ] `uv run cix query runs/svc-run --item first_contact_resolution` prints scrubbed
      snippet text; spot-check one line against
      `sqlite3 "file:runs/svc-run/run.db?mode=ro" "SELECT text FROM snippets WHERE id='svc-000:0006'"`.
- [ ] Bogus `--quote` exits non-zero with `does NOT resolve`; a real transcript line resolves.
- [ ] `sqlite3 "file:runs/svc-run/run.db?mode=ro" "SELECT count(*) FROM drop_log"` is `0`
      before and after all queries (read-only guarantee).
- [ ] `report.pdf` opens and its six sections match the narration above.
