# CIX POC B — The Sniffer (capability validation) · v2

**Owner:** PO · **Decoupled from the contractor build track** · **Runs in parallel with POC A**
**Sibling:** `CIX_POC_Scope_v3.md` (POC A — validates a *segment*) · **Depends on:** `CIX_Swap_Catalogue_v0.md` (upstream of the rubric) · **Evidence base:** `CIX_Opportunity_Library_v1.md` · **Architecture detail:** `CIX_MVP_Scope_v2.md`
**Target:** ASAP, sized to PO's plate. **Status:** v2, 2026-07-31 — supersedes v1 after the Technical-Advisor working session (7/28).

---

## 1 · What it does

Take an organisation's record of its customer-facing interactions and produce a **customer intelligence read**: what they're doing well, where they can improve, where the greatest leverage sits, and what it's worth.

Four outputs, in order:

1. **What's working** — patterns that succeed, worth spreading.
2. **Where it's failing** — pathologies, with counts.
3. **Where the leverage is** — ranked by **effort × outcome**.
4. **What it's worth** — occurrence counts attached to the plays that address them.

**The corpus claim** (unchanged, still the unproven part): reading a *sample* tells you what problems exist. Analysing the *whole corpus* gives completeness (three drivers or thirty), frequency (how often), and rank (which first). That holds even for findings a person could spot by hand — quantifying and ranking a known problem is most of the work.

**Framing concept: zero call resolution.** First call resolution asks whether you solved it on the first contact. Zero call resolution asks why the contact happened at all — an interaction the customer had to initiate is a service failure that wasn't anticipated. That reframe is what separates this from conversation-effectiveness tooling, which optimises the interaction rather than questioning it.

## 2 · The rubric is the product's main surface — and it swaps

**A rubric is loaded configuration, not code.** It defines what this run is hunting for. The pipeline is rubric-agnostic; swapping the rubric re-points the whole instrument.

This is the extensibility mechanism: **different rubrics for sales vs. service, per customer, per menu item.** Proving a second rubric loads cleanly is a v1 success condition, not a later feature.

**Rubric item structure:**

| Field | Purpose |
|---|---|
| `id`, `description` | what we're hunting |
| `polarity` | **positive** (working — spread it) or **negative** (pathology — fix it) |
| `detection` | what it looks like in an interaction; deterministic pre-filters where they exist |
| `unit_of_count` | what gets tallied (interactions, minutes, occurrences, accounts) |
| `remedy_class` | A = AI/software · B = delivery/service · C = process discipline · D = not ours / not worth it |
| `swap_ref` | link to the swap catalogue entry, where one exists |
| `effort`, `outcome` | estimates carried into ranking |

**One mechanism, two polarities.** "What's working" isn't a separate subsystem — it's positive-polarity rubric items running through the same machinery. Spreading a winning pattern is a Class C remedy.

**Open for the brainstorm:** the relationship between the *rubric* (what we hunt) and the *label schema* (how units get structured) is currently conflated. They're distinct and the boundary isn't settled. Don't decide it here.

## 3 · Pipeline

```
ingest → normalize → index → classify → aggregate → synthesize → validate → report
```

1. **Ingest** — mixed-format text; identify source type.
2. **Normalize** — common interaction unit: `{id, source_type, participants[], date?, segments:[{speaker?, ts?, text}]}`.
3. **Index** — **new in v2, and load-bearing.** Split into snippets, assign stable IDs, tag deterministically, build a retrievable provenance store. Two jobs: (a) every downstream claim resolves to a snippet ID, (b) deterministic pre-selection narrows the field *before* LLM spend.
4. **Classify** — LLM assigns labels + rubric hits. High volume, cheap-model shaped.
5. **Aggregate** — roll into corpus statistics: distributions, shares, co-occurrence, repeat chains. **Findings live here, as quantities.**
6. **Synthesize** — stronger model writes narrative findings from the rollup plus sampled snippets.
7. **Validate** — see §5.
8. **Report** — §4.

**Why the index stage exists.** From PO's S211 and sustainability-reporting experience: throw a corpus at an LLM and you get an answer; ask again and you get a different one, with no way to trace either. The fix isn't better prompting — it's abstracting the corpus into a tagged, addressable store first, so provenance is structural rather than requested. It also cuts cost, since deterministic filters run before tokens are spent.

**Build it as a self-contained, scalable unit.** Settled with the Technical Advisor 7/28: a unit that processes one interaction and emits structured output the next layer consumes. Not a throwaway script. Scale target is **hundreds, not millions** — enough to prove the approach without over-engineering.

**Two things are slots, not decisions:** the **corpus** (whatever lands first) and the **rubric** (whatever we load). No source-specific or rubric-specific logic in any stage.

## 4 · Output

1. **What's working** — positive-polarity hits, with frequency and where they concentrate.
2. **The full ranked distribution** — all rubric hits by volume, quantified. Proof of completeness; what a sample structurally cannot produce.
3. **The highlights** — the few findings that earn attention in the room. Different job from the distribution; both stay.
4. **Leverage ranking — effort × outcome.** Replaces severity × frequency. Effort = what it costs to fix; outcome = what you get. This is what makes it a decision rather than a list, and it gives Class D a principled home: high effort, low outcome, say so and move on.
5. **Open flags** — what the rubric didn't cover but the corpus surfaced. Evidence-cited, labelled exploratory.
6. **The priced view** — occurrence counts attached to the plays that address them. *"A third of your contacts are password resets"* becomes a number you can price against. This is what makes the output commercially load-bearing rather than merely informative.

**Tuning:** recall beats precision at the finding level — completeness is part of the claim, so a missed driver costs more than a marginal one.

**Tracked, not gated:** Tier 1 (corpus-only) vs. Tier 2 (hand-obtainable but prohibitive), plus actionability and what the corpus added (count, rate, rank). Observations to read after a few runs, not a pass/fail bar.

## 5 · The one hard gate

**Evidence integrity — pass/fail, mechanical, after synthesis:**

- Every quoted line resolves to a snippet ID and string-matches source.
- Every quantitative claim reproduces from the rollup.
- Failures are **dropped**, not flagged for adjudication.

Correctness, not polish. Reproducibility is the point: the same question asked twice must return the same answer, from the same traceable place.

## 6 · v1 scope boundaries

**In:** text (transcripts, email, chat, field notes) · sales/outbound rubric first · a second rubric loaded to prove swappability · frontier model throughout · hundreds-scale.

**Out, explicitly:** sentiment analysis · real-time anything · agent assist · model routing and cost optimisation (v1.5 — prove it works before making it cheap) · audio/Whisper (next phase) · live in-person capture (phase after).

**Why sales first:** easier door — *"we can make you more sales and pay us when the sales arrive"* is a simpler conversation than saving someone time. Service rubric is the second one loaded, which doubles as the swappability proof.

## 7 · Modality roadmap

| Phase | Input |
|---|---|
| **Now** | Text — transcripts, email, chat, written field notes |
| **Next** | Audio → transcription → same normalizer |
| **Then** | Live in-person capture (pin/card devices, glasses) — *creates* a corpus where none exists |

## 8 · Open items

| Item | Note |
|---|---|
| **Swap catalogue** | `CIX_Swap_Catalogue_v0.md` — upstream of the rubric; can't write rubric items without knowing the digital substitutes exist. Comes from the RevOps SME, not from the data. |
| **Rubric v1 (sales)** | Blocked on the catalogue |
| **Rubric vs. label schema boundary** | Brainstorm question, deliberately open |
| **Effort/outcome estimation method** | Where do the two numbers come from, and how honest can they be pre-engagement? |
| **First corpus** | Opportunistic — own record, leftover data, network ask, or synthetic |
| **PII posture** | Unresolved for the text phase, not just capture |

## Changelog

- **2026-07-31 (v2)** — Rewritten after the Technical-Advisor working session (7/28) and PO's MVP reframe. **Changes:** rubric promoted to a swappable loaded-config artifact — the product's main extensibility surface, with polarity so "what's working" runs through the same mechanism as pathology detection · **new `index` stage** for deterministic snippet-tagging and pre-selection before LLM spend, making provenance structural (PO's S211/sustainability-audit lesson) · **effort × outcome** replaces severity × frequency as the leverage ranking · **occurrence counts tied to pricing** added as an output · **build as a self-contained scalable unit** (the Technical Advisor's argument, PO conceded — corrects v1's "small and runnable, not a product") · sales/outbound named as rubric v1 with service second as the swappability proof · sentiment, real-time, agent-assist and model routing explicitly carved out · "zero call resolution" (the Commercial Principal) adopted as the framing concept. — Claude (Cowork)
- **2026-07-27 (v1)** — Split out from the single-MVP framing; superseded.
