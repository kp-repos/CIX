# CIX PRD Patch — Handoff for the build instance · v2

**Date:** 2026-08-03 (v2 same day) · **Author:** Claude (Cowork) · **For:** the Claude Code instance working in `github.com/kp-repos/CIX`
**Status:** ✅ RATIFIED BY KP 2026-08-05 — applied to PRD v1.3 in the same pass.
**Target:** `CIX_PRD_v1_2026-07-31.md` (v1.2, ratified 2026-07-31)
**Design record requiring back-propagation:** `Projects_gh/CIX/docs/CIX_BRAINSTORM_OUTPUT_2026-07-31.md` (rev 2.3)
**Evidence base:** `CIX_Corpus_Sourcing_Memo_2026-08-03.md` **v3** (Cowork folder, `agentic-build/cix/`)

---

## Scope note — read first

**KP narrowed the objective on 2026-08-03: demonstrate tech capability and overcome tech risk. Nothing else.**

- **O1 (external demo), commercial licensing, and the standing-asset job are PARKED.** Do not pick them up as live work.
- **The synthetic-corpus build continues unchanged, in parallel.** Nothing in this patch pauses, replaces, or reprioritises it. Synthetic proves the instrument is calibrated; real data proves the claim. Both run.
- A real corpus is now **acquired and inspected** — see §A. Several amendments below are consequences of what it actually contains.

---

## §A · Corpus facts (resolves D-1)

**Acquired:** `AIxBlock/CallCenterEN` — 91,706 real BPO call transcripts, CC BY-NC-4.0.
**Location:** `~/corpora/nc-quarantine/callcenter-en` (quarantined, `.gitignore`d out of the repo).
**Extracted:** 9.2 GB, 93,454 JSON files across 9 domain folders.

**The usable slice: `medicare_inbound` — 61,513 conversations.** Despite the folder name it contains **no Medicare**; it is healthcare / dental / veterinary **practice** inbound calls. Median duration 387s, range 182–907s. Genuine service interactions with visible failure demand, including repeat-contact chains.

**Five of nine folders are lead-generation, not service, and must not be used:** `insurance_outbound` (Medicare Advantage fraud lead-gen), `medical_equipment_outbound`, `customer_service_general_inbound` (mislabelled — insurance transfers), `automotive_and_healthcare_insurance_inbound`, `auto_insurance_customer_service_inbound`. These are operations working as designed where the design is the pathology; a rubric run against them surfaces the business model.

**Also genuine, available as secondary slices:** `home_service_inbound` (11,407), `automotive_inbound` (6,044), `home_ervice&telecom _outbound` (3,239).

### §A.2 Two further corpora acquired (2026-08-03)

**CFPB Consumer Complaints — `~/corpora/open/cfpb/cfpb_narratives_filtered.csv`, 1,500,436 rows, PUBLIC DOMAIN.**
Substrate class **S2**. Derived from 16,906,905 raw rows by stripping the three credit bureaus (77.6% of volume, bulk-filed disputes) and keeping only narrative-bearing records (22.7%). Median narrative 779 chars, p90 2,455. Spans 2015-03-19 to 2026-07-14. **28 companies exceed 10,000 narratives; 27 exceed 5,000 within the 2024+ window.**

**This corpus carries an outcome label the model never sees** — `Company response to consumer`, whose `Closed with monetary relief` class runs 6.4% overall and varies 270× between named operations (Bank of America 29.64%, Block Inc. 0.11%, 2024+). **Use it as semi-ground-truth**, not as a rubric input. Dollar figures survive redaction in `{$250.00}` notation, so this is the only acquired corpus supporting economic baselining.

⚠️ **Two ingest hazards.** (a) `Date received` is **mixed-format** — full ISO 8601 timestamps on recent records, bare dates on older — so `pd.to_datetime` without `format="ISO8601"` silently coerces 99.9% of rows to NaT. (b) `Consumer disputed?` **does not exist** (discontinued 2017) and `Timely response?` is 99.6% one class; neither is a usable label.

**Twitter Customer Support — `~/corpora/nc-quarantine/twitter-cs/`, 794,335 conversations, CC BY-NC-SA.**
Substrate class **S1**, `speaker_attribution: native`. Re-threaded by a third party from the Kaggle original; conversation count consistent with canonical ~800K from 2,811,774 tweets. **109 named companies, un-masked** — AmazonHelp 81,092, AppleSupport 76,639, Uber_Support 41,185, and vertical clusters (4 airlines, 4 telecoms, 3 gaming). Speaker prefixes inline (`Customer:` / `Support:`). Median 3 turns, 299 chars — thin per unit, but 794K units. `created_at` was dropped in re-threading, so **no response-latency analysis**. `summary` column is 100% empty; ignore it.

**Recommended first run (see memo §0.1): CFPB, Block Inc. vs Bank of America, 2024+.** Same rubric, two operations, a 270× measured difference in remediation behaviour, ample n on both sides.

**Three ingest facts the build must handle:**

1. **`__MACOSX/._*` AppleDouble shadow files also end in `.json`.** Any glob of `*.json` must filter `._*` or the index doubles and every count is wrong.
2. **Intra-zip duplicates exist** (`_-_Copy` filenames; 93,454 extracted against 91,706 claimed, re-uploads already excluded). **Dedup before indexing** — duplicate conversations corrupt frequency, which is the core claim.
3. **No `utterances` array.** Record schema is `{text, confidence, audio_duration, words[], redacted_pii_policies[]}`; `words[]` carries `{text, start, end, confidence, speaker}` with **`speaker: null` throughout**.

---

## §B · Amendments

Five now. **P3 remains the highest-value one.** P4 and P5 are new in v2, driven by corpus facts.

---

### P1 · §10 risk 2 + D-11 — fallback and cost envelope

**Problem:** RT-8 found "FS corpus turns out unusable" disposed of in one clause with no named alternative. D-11 (cost envelope) has no figure anywhere in the document.

**Note:** with a corpus now acquired at zero cost, this is **de-prioritised** but still worth landing so the register is honest.

```markdown
**Risk 2 — corpus unusable.** Disposition: resolved. A real corpus is acquired
(AIxBlock CallCenterEN, CC BY-NC-4.0, quarantined) at zero cost. A second
complementary corpus (Twitter Customer Support, same licence tier) is identified.
Paid fallbacks remain costed should the commercial track unpark: audio + in-house
Whisper ~$930, or ready-to-run speaker-labelled transcripts ~$4,500 one-off.

**Corpus fit/no-fit gate.** Before ingest, any candidate corpus must clear:
(a) licence permits the intended outcome tier per §2.3-S; (b) substrate class is S1
for any O3-bearing run; (c) PII posture satisfies R-PII-*; (d) volume ≥ the §7
corpus-size minimum; (e) speaker-attribution availability is recorded per §2.3-S.
Failure routes to the next corpus, not to a waiver.

**D-11 corpus line: $0 for v1.** Remaining envelope items (frontier spend per run)
unaffected.
```

---

### P2 · §5 / D-1 — decouple the corpus from the gate sequence

**Problem:** D-1 resolved "before M4 ingest," *after* thresholds freeze at M3 — so thresholds governing the first real run were frozen before anyone knew the corpus shape.

**Now resolvable rather than deferrable**, since the facts exist (§A).

```markdown
| D-1 | **RESOLVED 2026-08-03.** Corpus acquired and inspected: AIxBlock
CallCenterEN, `medicare_inbound` slice, 61,513 healthcare-practice inbound
conversations, median 387s. Facts, defects and ingest hazards recorded in
`CIX_Corpus_Sourcing_Memo_2026-08-03.md` §3. FS corpus no longer on the critical
path. | KP | ✅ Closed |
```

**Check on applying:** any §8 threshold written as a function of corpus scale must now read N from the run manifest rather than a frozen assumption. Grep for thresholds assuming a known N.

---

### P3 · §2.3 — substrate rule ⭐ *(highest value; extended in v2)*

**Problem:** §2.3 says synthetic can satisfy O1 but not O2/O3, without saying why, and without extending the rule to **roleplay** corpora — which are the entire free tier. As written, nothing stops a roleplay run emitting a `material-advantage` O3 verdict that means nothing. Under abandon trigger 2 that could kill or falsely rescue the thesis for the wrong reason.

**New in v2:** the corpus-property block at the end. Speaker attribution is not universally available, and a rubric item that silently assumes it will produce confident nonsense.

```markdown
**2.3-S · Substrate rule (normative).**

O3 requires a corpus with a **naturally occurring pathology distribution** — one
where patterns, frequencies and rank order arose from an actual operation rather
than from scenario design.

**Roleplay, Wizard-of-Oz and synthetic corpora do not qualify** and must never
produce an O3 verdict. The reason is structural, not a matter of quality: the
whole-corpus claim is about recovering a real distribution's tail, rank and
frequency that a sample would miss. Where the distribution was authored, the
self-test measures the authoring. A `no-material-advantage` result is
uninterpretable; a `material-advantage` result is fake confidence.

| Class | Definition | Serves |
|---|---|---|
| **S1 · Real operational** | Production interactions from a real operation | O1, O2, O3 |
| **S2 · Real non-conversational** | Real customer language, non-dialogue (e.g. complaint narratives) | O1, O2, **O3 for corpus-level items** — see below |
| **S3 · Roleplay / WoZ** | Humans performing assigned scenarios | O1 only |
| **S4 · Synthetic** | Model-generated | O1 (labelled), calibration tier |

**S2 and O3 — corrected 2026-08-03.** An earlier draft excluded S2 from O3 outright. That was wrong. The whole-corpus claim is about **recovering distribution, frequency and rank that a sample misses** — fully testable on 1.5M real complaint narratives, where the top-driver set and rank order demonstrably can differ between a 10% sample and the whole. Being monologue does not prevent it. What S2 cannot test is **conversation-dependent** rubric items (turn-taking, transfers, agent behaviour); those are skipped via the corpus-property gate below. So: **S2 serves O3 for corpus-level items, and the run artifact records which items were skipped and why.**

**Every run manifest records the substrate class.** A run whose corpus is S2, S3
or S4 emits `o3: not-applicable — substrate class {n}` rather than a verdict.
Hard behaviour, not a reporting convention.

**Licence tier is recorded independently of substrate class.** A corpus may be S1
yet non-commercially licensed, serving O2/O3 but not O1. Manifest records
`licence_tier: {commercial | non-commercial | public-domain}`; the release gate
blocks O1 publication on any non-commercial corpus.

**Corpus properties are recorded and gate rubric eligibility.** Manifest records:

| Property | Values |
|---|---|
| `speaker_attribution` | `native` · `inferred` · `none` |
| `economic_signal` | `present` · `redacted` |
| `ivr_structure` | `present` · `partial` · `absent` |

A rubric item declaring a dependency on any property the corpus lacks is **skipped
and reported as skipped** — never evaluated against absent data, never silently
degraded. Coverage denominators exclude skipped items.
```

---

### P4 · Speaker attribution — new requirement family *(new in v2)*

**Problem:** the acquired corpus has no speaker labels at all. Any rubric item assuming agent-vs-customer attribution will silently produce confident nonsense against it.

**KP's ruling (recommended, pending confirmation): option (b) for v1** — speaker-agnostic rubric only. The whole-corpus claim is fully testable without knowing who spoke; repeat-contact chains, the highest-value pattern observed, are detectable from content and metadata alone.

```markdown
**R-SPK-1.** The normalizer records `speaker_attribution` per corpus:
`native` (source provides labels) · `inferred` (derived, see R-SPK-2) · `none`.

**R-SPK-2.** Where attribution is inferred, it runs as an **explicit, separately
keyed pipeline stage** emitting a per-turn confidence, never as a silent
normalizer step. Method: pause-gap segmentation on inter-word gaps above a
configured threshold, with alternating assignment seeded from a known first
speaker. Inferred labels are marked as such in every downstream artifact and in
every rendered evidence excerpt.

**R-SPK-3.** Rubric items declare `requires_speaker: true|false`. Against a corpus
with `speaker_attribution: none`, items requiring speakers are skipped per §2.3-S
and excluded from coverage denominators.

**v1 scope:** `speaker_attribution: none` is supported and is the v1 path.
Inference (R-SPK-2) is **deferred to v1.5** — trigger: a rubric item of demonstrated
value that cannot be expressed speaker-agnostically.
```

---

### P5 · Ingest hardening — corpus-specific hazards *(new in v2)*

**Problem:** three concrete defects in the acquired corpus each corrupt counts silently. Counts are the product.

```markdown
**R-IDX-8 · Shadow-file exclusion.** Ingest excludes `__MACOSX/` paths and any
basename beginning `._`. These are AppleDouble binaries carrying `.json`
extensions; a naive glob doubles the index and invalidates every frequency claim.

**R-IDX-9 · Deduplication before indexing.** Content-hash every interaction at
ingest; identical hashes collapse to one with the duplicate count logged in the
manifest. Duplicate conversations inflate frequency, and frequency is the claim.

**R-IDX-10 · Redaction-token awareness.** Corpus text may carry PII placeholders
(`[PERSON_NAME]`, `[ORGANIZATION]`, `[MONEY_AMOUNT]`, `[DURATION]`). These are
**not content**: they must not be tokenised as vocabulary, must not appear in
rendered evidence excerpts as if spoken, and repeated adjacent placeholders
(`[ORGANIZATION] ×6` for one entity) must not inflate any count. The manifest
records the redaction policy list where the source provides one.
```

---

## §C · Governance — back-propagation is mandatory

PRD §0.2: *"any PRD-ratified decision that modifies a design-record ruling triggers a design-record revision in the same pass."*

P3 and P4 modify **D§10** (corpus, privacy, authorization) by adding a substrate taxonomy, a licence-tier gate, corpus-property gating and the speaker-attribution family. On applying:

1. Bump `CIX_BRAINSTORM_OUTPUT_2026-07-31.md` **rev 2.3 → rev 2.4**
2. Amend D§10 with the substrate classes, licence/outcome separation, and corpus-property gating
3. Record the D-1 resolution against the acquired corpus
4. Dated changelog entries in **both** documents

**One existing ruling explicitly survives unchanged and should be noted, not amended:** *"Author order ≠ run order — sales rubric authored first, corpus-shaped service rubric authored second and runs first."* Written for the FS corpus (financial-services inbound); the acquired corpus is healthcare-practice inbound. **Both service-side, so the ruling holds across the substrate swap.**

---

## §D · Implementation notes

- **Substrate class, licence tier and corpus properties are manifest fields**, not documentation. §6.5 already specifies manifest contents — add them there.
- **O3 suppression must be enforced in code**, not by convention. A run with `substrate_class != S1` should be structurally unable to emit an O3 verdict — same posture as the evidence gate, which drops rather than flags.
- **Skipped rubric items are reported, never silently dropped.** A skip is information about corpus fit; silence is a coverage lie.
- **The corpus fit/no-fit gate (P1) is a human checklist**, run before ingest. Its outcome belongs in the manifest.
- **Synthetic pipeline is untouched by all of the above** except that generated corpora must set `substrate_class: S4` and therefore emit `o3: not-applicable`. That is correct behaviour, not a regression.

---

## §E · Open questions for KP — resolve before applying

1. **Confirm the speaker ruling** — option (b), speaker-agnostic for v1, inference deferred to v1.5? P4 is drafted assuming yes.
2. **Is the NC route approved for O2/O3?** P3's licence-tier gate assumes yes and contains the risk. If no, the gate becomes a hard exclusion and the acquired corpus is unusable.
3. **Acquire Twitter Customer Support as the second corpus?** Same licence tier, no new legal question, and it supplies native speaker attribution plus un-masked brand identity — making it the strongest available proof of the "corpus is a slot" constraint (§2.1 goal 3).
4. **Does S2 (CFPB-class real non-conversational) get any O3 standing** in combination with an S1 corpus? Drafted as "not O3 alone," leaving combination undefined. Deliberately open.

---

## Changelog

- **2026-08-03 (v2.1)** — **New §A.2** records two further acquired corpora: CFPB filtered (1,500,436 narratives, public domain, substrate S2, carries an outcome label varying 270× between named operations) and Twitter Customer Support (794,335 conversations, NC-SA, substrate S1 with native speaker attribution and 109 un-masked companies). **P3 corrected** — S2 was wrongly excluded from O3 outright; the whole-corpus claim is about distribution/frequency/rank recovery, which is fully testable on monologue data. S2 now serves O3 for corpus-level items, with conversation-dependent items skipped via the corpus-property gate. Two CFPB ingest hazards documented: mixed ISO/bare date formats that silently NaT 99.9% of rows, and two label columns (`Consumer disputed?`, `Timely response?`) that are respectively non-existent and useless. First-run pair recommended. — Claude (Cowork)
- **2026-08-03 (v2)** — Updated after corpus acquisition and inspection. **New §A** records corpus facts, the five unusable lead-gen folders, and three ingest hazards. **Scope note added** — KP narrowed to tech capability + tech risk; O1/commercial/standing-asset parked; **synthetic build explicitly continues in parallel and is not displaced by anything here**. **P1/P2 revised** — corpus acquired at zero cost, so the paid fallback de-prioritises and D-1 moves from deferred to resolved. **P3 extended** with corpus-property gating (`speaker_attribution`, `economic_signal`, `ivr_structure`) and a skip-and-report rule for rubric items whose dependencies the corpus lacks. **P4 new** — speaker-attribution requirement family (R-SPK-1…3), v1 path is `none`, inference deferred to v1.5. **P5 new** — ingest hardening against shadow files, duplicates and redaction tokens, each of which silently corrupts counts. Author-order ruling noted as surviving the substrate swap. — Claude (Cowork)
- **2026-08-03 (v1)** — Created from the corpus-sourcing research pass. Three paste-ready amendments plus mandatory design-record back-propagation per PRD §0.2. — Claude (Cowork)
