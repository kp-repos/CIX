# CIX Swap Catalogue v0 — labour units with known substitutes

**Status:** v0 stub, 2026-07-31 · **Owner:** PO · **Upstream of:** the rubric in `CIX_POC_B_Sniffer_Scope_v2.md`
**Why it exists:** the corpus can show that work is happening. It cannot tell you the work has a substitute. That has to be known in advance.

---

## 1 · The gap this closes

From the 7/28 working session, PO's own framing:

> *"The things we need to do don't live inside this. The data isn't going to tell us that — it can tell us whether it's available to be there, but we have to know."*

The worked example: a rep drives to a store to eyeball inventory. The corpus reveals the visit happened and roughly what it cost. It does **not** reveal that a camera scan, a warehouse delivery record, or a photo from the store owner could replace the trip. Someone has to already know that swap exists.

**So the sniffer's rubric can only hunt for things we already know how to replace.** Without this catalogue, the output is a list of observations. With it, every observation carries a candidate remedy and a price.

## 2 · What a catalogue entry is

**Not a sales wedge.** The 8-item menu is how we package and sell. This is the operational layer beneath it: a discrete **unit of human labour** paired with a **known substitute** — digital, process, or delivery.

| Field | Purpose |
|---|---|
| `id` | stable reference for `swap_ref` in rubric items |
| `labour_unit` | the work as it actually happens — concrete, observable |
| `signal` | how it shows up in an interaction record (what the rubric hunts) |
| `substitute` | what replaces it |
| `remedy_class` | A = AI/software · B = delivery/service · C = process discipline · D = not ours |
| `effort` | what it takes to make the swap |
| `outcome` | what the swap returns |
| `preconditions` | what has to be true for the swap to work |
| `evidence` | have we seen this work, or is it inferred? |

`effort` and `outcome` feed the leverage ranking directly — this catalogue is where those two numbers originate.

## 3 · Seed entries (illustrative — not validated)

| Labour unit | Substitute | Class | Notes |
|---|---|---|---|
| Rep drives to a store to check inventory levels | Visual scan, warehouse delivery record, or customer-supplied photo | A | PO's worked example. Precondition: someone/something at the store can capture it. |
| Rep manually enters visit notes into CRM after the fact | Capture at the interaction → structured extraction | A | Also improves the corpus for everything else — compounding. |
| Contact-centre agent handles a fully deterministic request | Self-service or automated resolution | A | The password-reset archetype. Countable and priceable. |
| Repeat contact on an issue already raised | Fix the upstream defect — often another department's | D | Class D on purpose: naming it is the value, fixing it isn't ours. |
| Same question answered inconsistently across reps | Knowledge at the point of need + adherence monitoring | C | The flagship Class C: process exists, adherence doesn't. |
| High-cost field resource covering low-value accounts | Re-site to centre-based coverage | B | The coverage arbitrage — where our delivery arm earns. |
| Winning pattern used by one rep, unknown to the rest | Codify and spread it | C | **Positive polarity** — a swap that amplifies rather than removes. |

⚠️ **These are illustrative.** They came from reasoning about the problem, not from an operator confirming the swap works. Treat as a schema demonstration, not a validated catalogue.

## 4 · How this gets filled

**Primary source: the RevOps SME.** PO, same session — the menu of improvement plays *"is not in my body of knowledge. I know the person whose body of knowledge it's in."* Their RevOps lifecycle already decomposes to task and data-field level, which is the right granularity. The extraction is a structured session, not a document request.

**Suggested method:** walk their lifecycle pillar by pillar; at each subprocess ask *"what does a person do here, and what have you seen replace it?"* Record the substitute, the preconditions, and whether they have seen it work or is inferring. Their frequency test does double duty — a swap that fires once a year is Class D regardless of how clean it is.

**Secondary sources:** the Alexander Group process-excellence pattern (system-hop and step-count reduction); the pathology library's remedy classes; anything from an actual engagement, which will outrank all of the above.

**Bar for promotion out of v0:** an entry graduates from illustrative to real when someone who has run the operation confirms the substitute works and names its preconditions.

## 5 · Open questions

- **Granularity.** How fine is a "labour unit"? Too coarse and it's unactionable; too fine and the catalogue never converges.
- **Where do effort and outcome numbers come from**, and how honest can they be before an engagement?
- **Industry-specificity.** Most of the seeds above are cross-industry. Real catalogues are probably vertical — a DSD field rep's units differ from a contact-centre agent's.
- **Does the catalogue double as the menu's operational spine**, or stay a separate internal artifact?

## Changelog

- **2026-07-31** — v0 stub created. Identified during the 7/28 the Technical Advisor session as the gap that blocks the rubric: the corpus reveals opportunity, not remedy, so the substitutes have to be catalogued in advance. Schema defined, seven illustrative seeds, the RevOps SME named as the extraction source. — Claude (Cowork)
