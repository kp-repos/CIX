# CIX — Corpus Sourcing: Landscape, Acquisition, Findings · v4

**Owner:** KP · **Date:** 2026-08-03 (v4 same day) · **Status:** three corpora acquired and profiled; first-run pair identified
**Serves:** `CIX_PRD_v1_2026-07-31.md` §2.3 (O2/O3), §10 open register D-1 + D-11, red-team **RT-8**
**Scope (KP, 2026-08-03):** narrowed to **demonstrating tech capability and overcoming tech risk**. External demo (O1), commercial licensing and the standing-asset job are **parked**.
**Synthetic track:** **continues unchanged, in parallel.** Nothing here displaces it — this memo answers "what real options exist," not "what replaces synthetic."
**Companion:** `CIX_PRD_Patch_HANDOFF_2026-08-03.md`

---

## 0 · State of the collection *(new in v4)*

Three real corpora acquired, extracted and profiled. Provenance and integrity anchors recorded in `~/corpora/PROVENANCE.md`.

| Corpus | Units | Speaker | Median length | Company | Economic signal | Outcome labels | Licence |
|---|---|---|---|---|---|---|---|
| **CFPB filtered** | **1,500,436** | ❌ monologue | 779 ch | ✅ named, 28 ≥10K | ✅ `{$250.00}` preserved | ✅ **yes** | ✅ **public domain** |
| **Twitter CS** (TNE-AI) | 794,335 | ✅ native inline | 299 ch | ✅ 109 named | ❌ | ❌ | NC-SA |
| **AIxBlock** healthcare | 61,513 | ❌ `null` | ~2,800 ch | ❌ redacted | ❌ | ❌ | NC |

Plus permissive roleplay sets for O1 and control use (NatCS, ABCD, MultiDoGO, TweetSumm) and S&P 500 earnings transcripts as the synthetic-track realism donor.

**Headline: CFPB is the strongest asset**, which inverts the ordering in v1–v3. It is the only corpus carrying outcome labels, preserved dollar figures *and* a public-domain licence — the last meaning it is the one real corpus that could serve O1 if that track ever unparks.

### 0.1 The first-run pair

CFPB's `Company response to consumer` yields a measurable, independently-recorded operational difference between named operations:

| Operation | Monetary-relief rate (2024+) | n |
|---|---|---|
| Bank of America | **29.64%** | 19,559 |
| Citibank | 22.49% | 20,289 |
| American Express | 19.55% | 10,596 |
| PayPal | 14.47% | 10,103 |
| Wells Fargo | 10.09% | 20,507 |
| JPMorgan | 7.69% | 25,185 |
| Capital One | 5.59% | 30,785 |
| **Block, Inc.** | **0.11%** | 43,550 |
| Resurgent Capital · Portfolio Recovery | 0.00% | 14,986 · 9,580 |

The structure is legible: banks and card issuers remediate at 6–30%; debt collectors at ~0% (their business model, not a failure); **Block/Square behaves like a debt collector rather than a bank**, which is a genuine non-obvious finding of exactly the shape CIX exists to produce.

**Rank order holds across the full 2015–2026 span**, so date-windowing is optional — but 27 companies still clear 5,000 narratives since 2024, so it costs nothing to window properly.

**Recommended first run: Block (43,550) vs Bank of America (19,559), 2024 onward.** A 270× difference in remediation behaviour, ample n on both sides, same sector, current. **This is semi-ground-truth for free:** if CIX's analysis of Block doesn't surface "customers don't get money back" as a dominant pattern, the pipeline is missing something a human spots in minutes. If it does, that's a hit against an outcome label the model never saw.

---

## 1 · Where this landed

**A real corpus is on disk, inspected, and fit for the tech-risk question.**

Downloaded `AIxBlock/CallCenterEN` — 91,706 real BPO call transcripts, CC BY-NC-4.0, quarantined at `~/corpora/nc-quarantine/callcenter-en`, excluded from the CIX repo. 1.3 GB compressed, 9.2 GB extracted, 93,454 files.

**The usable corpus inside it is one folder: `medicare_inbound`** — 61,513 conversations which, despite the name, contain **no Medicare at all**. They are healthcare, dental and veterinary **practice** inbound calls. Mentally rename it `healthcare_practice_inbound`.

**Two structural defects found on inspection**, neither fatal to the tech-risk question:

1. **No speaker labels anywhere.** Diarization was never run — the `speaker` field exists on every word and is `null` throughout.
2. **Over-redaction damages economic and IVR signal.** `money_amount`, `statistics`, `number_sequence` and `organization` are all scrubbed; `press 1` is inconsistently redacted as `[PHONE_NUMBER]`.

Full findings in §3.

---

## 2 · The open-tier deadlock (unchanged, now confirmed empirically)

> Every corpus that is **real production customer-service data** is non-commercially licensed, gated, or share-alike encumbered. Every corpus that is **cleanly commercially licensed** is crowdworker roleplay or synthetic. There is no open corpus that is both.

**Why this doesn't block the current scope.** Licence permission maps onto the PRD's own outcome split by *who sees the result*:

| Outcome | Who sees it | NC data usable? |
|---|---|---|
| **O1** — pipeline demo-ready | External party | ❌ No — and O1 is parked |
| **O2** — real-run release-ready | Internal run artifact | ⚠️ Defensible while it stays in the building |
| **O3** — whole-corpus hypothesis test | **Internal verdict** | ✅ Strongest case |

Since the scope is tech capability and tech risk, **the NC licence stops being a constraint.** The containment rule (quarantine path, `.gitignore`, no O1 artifact derived from it) is what keeps that true.

*Creative Commons' own guidance: NC turns on the nature of the use, not the nature of the user. Not legal advice; obtain a qualified read before anything leaves the building.*

---

## 3 · What the acquired corpus actually contains *(new in v3 — empirical)*

### 3.1 Folder-by-folder reality

Five of nine folders are **lead-generation, not customer service** — and the labels don't tell you which:

| Folder | Count | Reality |
|---|---|---|
| `insurance_outbound` | 4,005 | ⛔ **Medicare Advantage fraud lead-gen.** Scripted, offshore, elderly targets, DOB/zip harvesting with scripted consent theatre. |
| `medical_equipment_outbound` | 738 | ⛔ DME telemarketing, same shape |
| `customer_service_general_inbound` | 1,217 | ⛔ **Mislabelled** — final-expense insurance transfers |
| `automotive_and_healthcare_insurance_inbound` | 1,793 | ⛔ Warm-transfer lead-gen |
| `auto_insurance_customer_service_inbound` | 1,749 | ⛔ Insurance quote-comparison transfers |
| `home_service_inbound` | 11,407 | ✅ Glass repair — genuine inbound service |
| `automotive_inbound` | 6,044 | ✅ Dealership service — genuine |
| `home_ervice&telecom _outbound` | 3,239 | ✅ Appliance service — genuine |
| **`medicare_inbound`** | **61,513** | ✅ **Healthcare / dental / veterinary practice inbound. The corpus.** |

⚠️ The fraud folders are unusable not merely on taste but on premise: they are operations working **exactly as designed**, where the design is the pathology. A rubric run against them surfaces the business model, not inefficiency.

### 3.2 Why `medicare_inbound` is the right slice

25 random draws, zero Medicare, and every draw a genuine service interaction.

- **Scale:** 61,513 — six times everything else combined
- **Length:** median **387s (6.5 min)**, range 182–907s. Substantial conversations.
- **Shape:** appointment-driven practices — bounded, coherent, analysable
- **Operational surface present:** IVR menus, hold-time announcements, queue position, language routing

**Failure demand is visible in a 25-draw sample** — which is the encouraging signal:

- *"it me again for the dog in for the cat… I was just talking to you. Sorry."* → **repeat contact within minutes.** Textbook zero-call-resolution. You cannot estimate its *rate* from a sample; you can count it across 61,513. That is the corpus claim, in miniature.
- *"You just answered two of my questions."* → information the customer had to phone for
- *"I was going to your office when it was [ORG]."* → practice changed hands, customer confused
- *"Your call is now first in line… estimated hold time is currently [DURATION]."* → queue structure, countable even redacted

### 3.3 Defect 1 — no speaker attribution

`{"text": "Hello?", "start": 2400, "end": 2720, "confidence": 0.76, "speaker": null}`

The schema slot exists; diarization never ran. `text` is one undifferentiated blob with both sides interleaved. Audio was not released, so re-diarization is impossible.

**What survives:** word-level `start`/`end` in ms, per-word `confidence`, `audio_duration`.

**Recovery is possible but costed.** Pause-gap segmentation (split on inter-word gaps >400–600 ms) reconstructs *turn boundaries*; alternating assignment from a known first speaker (the greeter is always the agent) yields *speaker identity*. It degrades on backchannels. If used, it must be an explicit labelled inference stage with its own confidence — never a silent normalizer step, or it contaminates the evidence chain.

### 3.4 Defect 2 — over-redaction

The AssemblyAI PII pass removed `money_amount`, `statistics`, `number_sequence`, `duration`, `organization`, `occupation`, `date`, `time`, `location` and more. Consequences:

- **No economic baseline from transcript content.** Spoken dollar figures are gone. The priced view cannot be built from this corpus. *(Handle time survives — word-level timestamps are intact.)*
- **IVR structure partly destroyed.** `press 1` → `[PHONE_NUMBER]` in most files but **not all** (sample #8 retained "press 1"). The inconsistency biases any count built on menu navigation.
- **Readability degraded.** `[ORGANIZATION] ×6` for one company name; `"a great [DURATION]"` for "a great day"; `[OCCUPATION] [OCCUPATION]` for "licensed agent".

### 3.5 Data-quality notes

- **ASR:** 96.1% claimed accuracy holds on average; errors concentrate in accented speech (*"De're practicing a w"*, *"WEL thank you LAIAM"*)
- **Vintage:** filenames date calls to **2020–2021** — a pre-AI-intervention baseline, arguably ideal
- **Duplicates:** 93,454 files extracted against a claimed 91,706 total, with the two re-uploads already excluded. Intra-zip duplicates exist (`_-_Copy` filenames). **Dedup before indexing** — duplicate conversations corrupt frequency counts, which is the core claim.
- **Cruft:** every zip carries `__MACOSX/._*` AppleDouble shadow files that also end `.json`. Excluded at extraction; any future ingest globbing `*.json` naively must filter them.

---

## 4 · Second-best option — Twitter Customer Support *(new in v3)*

Worth acquiring, and the reason is complementarity rather than backup.

**[Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)** — 3M+ real brand↔customer exchanges, ~800K conversations, ~20 major brands (Amazon, Apple, Uber, Delta, Spotify). CC BY-NC-SA 4.0 — **same licence tier as AIxBlock, so no new legal question and the same quarantine rule covers it.**

**It solves precisely what AIxBlock lacks:**

| | AIxBlock | Twitter CS |
|---|---|---|
| Speaker attribution | ❌ null throughout | ✅ **inherent** — `inbound` boolean per message |
| Turn structure | Must be inferred | ✅ Threaded via `in_response_to_tweet_id` |
| Company identity | Redacted to `[ORGANIZATION]` | ✅ **Un-masked** — sliceable to one brand's operation |
| Conversation length | ✅ 6.5 min median | ❌ 2–8 turns, clipped |
| Channel | ✅ Voice | ❌ Public social |
| Vintage | 2020–21 | Dec 2017 |

**The strategic argument:** CIX analyses *an operation*. Twitter CS lets you isolate a **single named brand's support operation** — something the redacted AIxBlock data structurally cannot do.

**And it proves a v1 success condition.** PRD §2.1 goal 3 requires hot-swap proven. Two structurally different corpora — long-form voice with no speaker labels vs. short-form threaded text with perfect labels — is a **far stronger test of "corpus is a slot, no source-specific logic in any stage"** than two rubrics against one corpus. This is the cheapest available proof that the design constraint holds.

**Third asset — and on the evidence it's actually first:** **[CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)**. See §0 for the acquired profile. Public domain, real customers, monologue not dialogue, but carries **outcome labels attached to real text**.

⚠️ **Correction to v2/v3:** I named `Consumer disputed?` as one of the usable labels. **That field does not exist** — CFPB discontinued it in 2017. And `Timely response?` is near-useless at 99.6% "Yes". **The usable label is `Company response to consumer`**, whose explanation-vs-relief split is a real outcome distinction with 6.4% in the monetary-relief class.

**Acquisition notes (empirical):** the raw database is **16,906,905 rows / 9.05 GB uncompressed**, of which **77.6% are three credit bureaus** (Experian, TransUnion, Equifax — bulk-filed credit disputes) and only 22.7% carry narratives. Filtering both leaves **1,500,436 usable narratives**. Dates are **mixed-format** — full ISO 8601 timestamps on recent records, bare dates on older ones — so `pd.to_datetime` silently coerces 99.9% to NaT unless `format="ISO8601"` is passed. Filter script: `scripts/cfpb_filter.py`; profiler: `scripts/cfpb_dates.py`.

---

## 5 · Synthetic — unchanged, running in parallel

Position holds from the design record (D§10): **permanent validation infrastructure, built regardless.** Nothing in this memo displaces it, and the coding effort should not pause.

The division of labour is clean:

| | Synthetic | Real (AIxBlock / Twitter CS) |
|---|---|---|
| Planted pathologies of known magnitude | ✅ Only source | ❌ No ground truth |
| Sensitivity curves by loudness | ✅ | ❌ |
| Null corpora → genre-hallucination floor | ✅ | Partially, by domain selection |
| Whole-corpus claim (O3) | ❌ Structurally cannot | ✅ Only source |
| Real distribution, tail, rank | ❌ | ✅ |

Synthetic proves the instrument is calibrated; real data proves the claim. Neither substitutes for the other, and running both is the design, not a hedge.

Tooling if useful: **[distilabel](https://github.com/argilla-io/distilabel)** (cleanest generator/audit-seat separation, provider swap is config) · **[NVIDIA NeMo Data Designer](https://docs.nvidia.com/nemo/microservices/25.9.0/about/core-concepts/synthetic-data.html)** (declarative, heavier). Second-lab generator should be Western-origin — satisfies F4 collusion-breaking and the procurement posture at once.

**Sales-side realism donor (open item #13) — partial answer found:** **[S&P 500 earnings-call transcripts](https://huggingface.co/datasets/Bose345/sp500_earnings_transcripts)**, MIT licence, 33,000+ transcripts, 685 companies. Caveat: earnings calls are investor-relations, not sales. The analyst Q&A segment is the closest public analogue to objection-handling but remains an analogue. **Partial answer, not closed.**

---

## 6 · The one open decision

**Speaker attribution.**

- **(a) Pause-gap segmentation + alternating assignment** — explicit labelled inference stage with confidence. Unlocks speaker-dependent rubric items. Costs a new stage and a documented error source.
- **(b) Speaker-agnostic rubric only** — topic distribution, repeat-contact chains, hold/queue events, duration. Less rich, zero new error, ships faster.

**Recommendation: (b) for v1.** The objective is tech risk, and the whole-corpus claim — completeness, frequency, rank — is fully testable without knowing who spoke. Repeat-contact chains, the most valuable pattern in the sample, are detectable from content and metadata alone. Add (a) at v1.5 once the spine is proven.

**Consistent with an existing ruling:** the design record already says *"Author order ≠ run order — sales rubric authored first, corpus-shaped service rubric authored second and runs first."* That ruling was written for the FS corpus. FS was financial-services inbound; this is healthcare-practice inbound. **Both service-side, so the ruling survives the substrate swap unchanged.**

---

## 7 · Landscape reference (compressed from v2)

**Free but roleplay — O1 only, structurally invalid for O3.** [DSTC11/NatCS](https://github.com/amazon-science/dstc11-track2-intent-induction) (Apache-2.0, ~1,000 banking, ~59–70 turns, speaker-labelled) · [ABCD](https://github.com/asappresearch/abcd) (MIT, agent-vs-policy conflict) · [MultiDoGO](https://github.com/awslabs/multi-domain-goal-oriented-dialogues-dataset) (CDLA-Permissive). ⚠️ NatCS licence drift: Apache-2.0 in 2022 → CC-BY-NC in 2025 for the same material. Snapshot LICENSE + commit SHA.

**Real but blocked.** [MSDialog](https://ciir.cs.umass.edu/downloads/msdialog/) (35K real MS support threads; vetted-researcher gate) · [TweetSumm](https://github.com/guyfe/Tweetsumm) (1,100 dialogues + 6,500 summaries, but text chains to the NC Kaggle file).

**Purchasable, if the commercial track ever unparks.** [WiserBrand Multisector transcripts](https://datarade.ai/data-products/customer-service-call-dataset-multisector-annotated-suppo-wiserbrand-com) ~$4,500 one-off, **speaker-labelled** · [FileMarket audio](https://datarade.ai/data-products/global-call-center-conversational-audio-dataset-multiling-filemarket) from $7/hr · [Shaip](https://www.shaip.com/offerings/call-center-dataset/) quote-only. Free samples offered by all.

**Dead end — paid academic.** LDC and ELRA fail on *domain* before licence: [Fisher](https://catalog.ldc.upenn.edu/LDC2004S13) is *"a participant… paired with another participant, whom they typically do not know, to discuss assigned topics"* — strangers on assigned topics, verified at source. ELRA holds [DECODA](https://aclanthology.org/L12-1399/), a genuine call-centre corpus, but it's French and unpriced.

---

## 8 · Confidence

| Claim | Confidence | Basis |
|---|---|---|
| AIxBlock corpus contents, defects, folder reality | **High** | Downloaded, extracted, sampled directly |
| `medicare_inbound` is healthcare practices not Medicare | **High** | 25 random draws, zero Medicare |
| No speaker labels | **High** | Word-schema inspected; `speaker: null` throughout |
| Fraud lead-gen in `insurance_outbound` | **High** | Two independent samples, identical script |
| Open-tier deadlock | **High** | ~20 candidates, licences at source |
| Twitter CS field structure | **Medium-high** | Documented schema; not yet downloaded |
| NC-for-internal-use position | **Medium** | Reflects CC guidance; **not legal advice** |

---

## Changelog

- **2026-08-03 (v4)** — Two further corpora acquired and profiled; ordering inverted. **New §0** — state of the collection: CFPB filtered (1,500,436 narratives), Twitter CS via TNE-AI (794,335 conversations), AIxBlock healthcare (61,513), plus permissive roleplay sets and the S&P earnings donor. **CFPB promoted to strongest asset** — the only corpus with outcome labels, preserved dollar figures (`{$250.00}` survives redaction, unlike AIxBlock) and a public-domain licence. **Key empirical finding:** `Company response to consumer` yields a 270× spread in monetary-relief rate between named operations (Bank of America 29.64% vs Block, Inc. 0.11%, 2024+), with legible structure — banks remediate at 6–30%, debt collectors at ~0%, and **Block behaves like a debt collector rather than a bank**. Rank order holds across 2015–2026, so windowing is optional; 27 companies clear 5,000 narratives since 2024. **First-run pair recommended: Block vs Bank of America, 2024+** — semi-ground-truth for free, since a pipeline that can't distinguish them is missing something a human sees in minutes. **Corrections:** `Consumer disputed?` does not exist (discontinued 2017) and `Timely response?` is near-useless (99.6% one class) — both were wrongly named as usable labels in v2/v3. Acquisition hazards recorded: 77.6% credit-bureau concentration, 22.7% narrative rate, mixed ISO/bare date formats that silently NaT 99.9% of rows. Scripts landed at `scripts/cfpb_filter.py` and `scripts/cfpb_dates.py`. — Claude (Cowork)
- **2026-08-03 (v3)** — Rewritten after acquiring and inspecting the corpus. Scope narrowed on KP's direction to **tech capability + tech risk**; O1, commercial licensing and standing-asset jobs parked; **synthetic track explicitly continues in parallel** (§5). **New empirical §3:** AIxBlock CallCenterEN downloaded and validated — five of nine folders are lead-generation rather than service (`insurance_outbound` is Medicare Advantage fraud), and `medicare_inbound` (61,513, 66% of corpus) contains **no Medicare** but is healthcare/dental/veterinary practice inbound and is the strongest slice in the set. Two structural defects documented: **no speaker attribution** (diarization never run; `speaker: null` throughout) and **over-redaction** stripping economic signal and IVR menu digits. Failure demand — including a repeat-contact chain — visible in a 25-draw sample. **New §4:** second-best option evaluated — Twitter Customer Support, chosen for complementarity (inherent speaker attribution, un-masked brand identity, threaded structure) and because two structurally different corpora prove the "corpus is a slot" constraint better than two rubrics on one. CFPB named as a third, public-domain asset. **New §6:** speaker-attribution decision framed, (b) speaker-agnostic recommended for v1, shown consistent with the existing author-order ruling. v2's pricing and landscape material compressed to §7 reference. — Claude (Cowork)
- **2026-08-03 (v2)** — Pricing corrected ($4,500 transcripts vs ~$930 audio+Whisper, replacing v1's erroneous $200–3,300 band). Added the NC-route reframe: NC permission maps onto the O1/O2/O3 split by who sees the result. Recommendation restructured cheapest-first. — Claude (Cowork)
- **2026-08-03 (v1)** — Created. Principal finding: open-tier deadlock (real ⊻ commercially licensed). Second finding: roleplay corpora structurally cannot test the whole-corpus claim, so RT-8 cannot be closed by naming a free fallback. Paid academic channel ruled dead on domain grounds. — Claude (Cowork)
