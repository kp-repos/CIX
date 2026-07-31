# CIX Opportunity Library v1 — known pathologies, value at risk, and remedy classes

**Purpose:** the source material CIX detects against, and the seed for building the menu out. Not a scope doc — this is the evidence base.
**Built:** 2026-07-27 · **Owner:** PO (interim PM, G4/KR 5.1j) · **Companion:** `CIX_MVP_Scope_v2.md`
**Scope of this pass:** Alexander Group article (PO-supplied) treated as *one* example among many · the RevOps SME's Exponentiv maturity deck mined as the structural spine · web research across CX and RevOps · competitive reality check.

---

## 1. The frame

CIX v1 does four things in sequence, and only the first three are detection:

```
1. NATURE of interactions   — what kind of work is actually flowing through this operation
2. DRIVERS of interactions  — why does this work exist at all, and who/what causes it
3. VALUE AT RISK / UPSIDE   — what each pattern is plausibly worth, in the customer's own terms
4. WHAT TO ADDRESS FIRST    — ranked, with the remedy class named
```

**The load-bearing principle (PO, 2026-07-27):** *not every finding needs to be solved by AI, or by us.* Knowing is what makes it valuable. A report that says "these three things are worth the most, one is ours, one is a process-discipline fix you can do next week, one belongs to your billing team" is more credible — and more sellable — than one that routes every finding to our own offer. The objectivity is the product. the RevOps SME makes the same point from the consulting side: the findings create the opening, and it only works *"provided objectivity is preserved so it never reads as a pitch."*

### Remedy classes (every finding gets exactly one)

| Class | Meaning | Who delivers |
|---|---|---|
| **A — AI/software** | Genuinely automatable or AI-augmentable work | Our software |
| **B — Delivery/service** | Needs people doing the work differently at scale | Our BPO side (or theirs) |
| **C — Process discipline** | The process is fine; adherence isn't. "Better people following the process." | Them, with our monitoring |
| **D — Not ours / not now** | Belongs to another function, or fails the frequency test — worth naming, not worth fixing | Them, or nobody |

**Class C is strategically underrated and should not be treated as a consolation prize.** It is often the fastest value, it requires no technology change, and it is where the AI's *second* job lives: **detecting the opportunity, then confirming compliance to the new process once it's adopted.** That converts a one-shot assessment into a monitored, recurring engagement — the "did the fix actually stick" loop — which is a far better commercial shape than a report that lands and dies. Class C is also the honest answer for most operations, and saying so early buys credibility for the Class A findings that follow.

**Class D exists because of the RevOps SME's frequency test:** *"how many times a year does this happen? Once. Okay, we're not gonna go to transformative for that one."* Naming what to leave alone is part of the deliverable.

---

## 2. The structural spine — the RevOps SME's lifecycle

CIX should not invent its own taxonomy. the RevOps SME's Exponentiv **RevOps Capability Maturity Assessment** already provides the skeleton, it is field-shaped, and it's the front end we're jointly positioned on:

**Attracting → Closing → Onboarding → Serving → Retaining → Expanding**, with an **Enablement** layer beneath, each pillar drilling to process → subprocess → task → data field, scored **Lagging / Basic / Leading / Transformative**, with current-state and future-state produced in the same motion.

**The integration thesis:** their framework is the skeleton; **CIX is the evidence engine that fills it from the corpus.** Today those scores come from interviews and workshops. CIX scores them from what the organisation's own conversations actually show. That is a meaningfully better instrument, and it's the join between the Scan (hers) and the Remediate/Run (ours).

Two of their design choices should be inherited directly:
- **Frequency-based prioritization** — not everything goes to Transformative (→ our Class D).
- **The "quick wins" column** in their companion model — they already has a slot for exactly the mundane, non-transformational fixes PO is pointing at (→ our Class C).

⚠️ **Known scope caveat (logged 2026-07-21):** the matrix was designed macro and *without an outsourcing lens* — modelled on Accenture-style transformation engagements. Reusing their spine inherits that gap; the outsourcing lens has to be added deliberately (open item A21J-07).

---

## 3. The library — CX / service side

### CX-1 · Failure demand (avoidable contact)
**What it is:** demand created by the organisation's own failure to do something, or do it right — the single largest and most under-measured category of contact volume. The term is established (Seddon), which helps: buyers who know it take it seriously, and buyers who don't get a memorable frame.
**Evidence base (weaker than it first looks — see §6):** reported ranges of **20–60% in financial services and up to 80% in public sector/utilities**, tracing to Seddon/Vanguard demand-analysis work (consultancy-derived, not peer-reviewed); Sabio / Customer Contact Association research putting **25–40% of UK contact centre calls as unnecessary or avoidable** — but that study is **from 2012**. The often-quoted **2–3× downstream cost multiplier** appears in industry-association glossary material with no underlying study attached: anchor only. A frequently-cited "57% of inbound calls caused by website findability failure" **could not be traced to any primary source — do not use it.**
**How it shows in a corpus:** contacts whose stated reason is an internal defect, a prior interaction, a broken promise, an unclear policy, or a self-service dead end.
**Value at risk:** volume share × fully-loaded cost per contact × the 2–3× downstream multiplier.
**Remedy classes:** mostly **D** (belongs to product/billing/web) and **C**; some **A** where deflection is real.
**Verification signal:** driver share falls after the upstream fix — directly measurable in the next corpus. This is the cleanest "did it stick" metric in the library.

### CX-2 · Repeat contact & resolution failure
**What it is:** the same issue coming back. The strongest effort driver and the most reliable proxy for broken process.
**Evidence base:** customers who contact more than once for the same issue rate the experience high-effort **81% of the time regardless of eventual resolution** — a genuine CEB finding (*The Effortless Experience*) and the solid anchor here. FCR benchmarks per SQM Group: **~70–79% is "good," 80%+ is world-class.** ⚠️ The widely-circulated "+88% repurchase intent / −76% churn risk" pair **could not be traced to a primary Forrester or Gartner publication** — it appears only in secondary aggregator content. Do not cite it.
**How it shows:** repeat-contact chains on one issue, "I've called about this before," reopened threads, transfer sequences.
**Value at risk:** repeat volume × cost per contact, **plus** churn-linked revenue — this one lands on both money axes at once, which makes it the best single opener for a revenue-oriented buyer.
**Remedy classes:** **C** (adherence, knowledge use) and **B** (resolution authority at the front line) more often than **A**.
**Verification signal:** repeat rate on the targeted driver.

### CX-3 · Self-service and channel misallocation
**What it is:** work sitting in the most expensive channel that didn't need to be there — and, inversely, self-service that fails and manufactures failure demand.
**Evidence base:** Gartner press release **19 Aug 2024** (survey of 5,728 customers fielded Dec 2023) — **only 14% of customer service issues are fully resolved in self-service**, while **73% of customers use self-service at some point**. Separately, from Gartner's customer-service cost benchmarks: median cost per contact **$1.84 self-service vs $13.50 assisted**. *(Two different Gartner assets — don't present as one study. Carry the date; by 2026 this is ~2.5-year-old data.)*
**How it shows:** contacts that reference a failed self-service attempt; intents that are fully deterministic yet arrive assisted.
**Value at risk:** deflectable volume × the assisted-minus-self-service cost delta. The published spread makes this arithmetic unusually easy to show a buyer.
**Remedy classes:** **A** where the intent is genuinely deterministic; **D** where the fix belongs to the web/product team.
**Verification signal:** channel mix shift on the targeted intents, *with* repeat rate held flat — the guard against deflecting work into failure demand.

### CX-4 · Knowledge failure and process non-adherence
**What it is:** the process exists; people can't find it, can't follow it, or don't. Consistently named among the top root causes of contact-centre performance problems — alongside poor routing, tool fragmentation, burnout, thin coaching and understaffing.
**How it shows:** long silences and hold patterns, inconsistent answers to the same question across agents, workaround language, escalations for things that shouldn't escalate.
**Value at risk:** handle-time delta between adherent and non-adherent handling × volume; plus the FCR/repeat linkage.
**Remedy classes:** **C** overwhelmingly — and this is the flagship Class C pathology. Some **A** (retrieval at the point of need).
**Verification signal:** adherence rate to the revised process, measured continuously from the corpus. **This is the compliance-monitoring product** — required, but note §5: competitors already ship close-the-loop tracking, so this is parity work, not a moat.
**Note:** this is where BPO-delivered operations are structurally most exposed — outsourced agents lack the institutional context to paper over incomplete knowledge, making the pathology both more severe and more detectable on the acquisition side. (SentiSum already scores BPO partners against in-house benchmarks, so the *detection* isn't novel; owning the BPO being scored is the part they can't copy.)

---

## 4. The library — RevOps / revenue side

### RO-1 · Seller time lost to non-selling work
**What it is:** the admin tax. The clearest makes-money finding in the library and the one every revenue leader already believes.
**Evidence base:** Salesforce *State of Sales* — **40% of seller time actively selling** (7th ed., pub. Feb 2026, fielded Aug–Sep 2025, n=4,050); **30%** (6th ed., 2024); **28%** (5th ed., pub. Dec 2022). ⚠️ **These are three editions across four years with differing question wording — the apparent 28%→40% "improvement" is not interpretable as a trend.** SPOTIO *State of Field Sales 2026* (n=452) is the cleaner cut: **43% selling** (37% in-person + 6% virtual), **21% administrative** (10% admin + 11% data entry) ≈ **8 hours per rep per week**; **B2B 33% vs B2C 49%**.
**How it shows:** meeting and email evidence of manual data entry, status-chasing, internal coordination, quote assembly, CRM hygiene work.
**Value at risk:** hours recovered × fully-loaded seller cost, or hours × revenue-per-selling-hour. Frame both ways — the second is the one that moves a CRO.
**Remedy classes:** **A** (capture/automation) and **C** (stop doing work nobody reads).
**Verification signal:** measured share of seller time on non-selling activity, re-measured from the same corpus.
⚠️ **Source caution:** these figures circulate widely with inconsistent attribution and definitions. Use them to frame the *shape* of the problem; measure the actual number from the customer's own corpus. Never present a benchmark as their result.

### RO-2 · Process step and system sprawl (the Alexander Group pathology)
**What it is:** work that requires too many systems and too many steps because nobody owns the process end to end. AGI's case: sellers working through **five different systems and over 30 steps to generate a renewal quote**, over multiple days — with the organisation "papering over" it by adding support headcount instead of fixing root cause.
**Why it matters structurally:** AGI's remedy is to stand up two *human* functions — **Commercial Process Excellence** (document current and future state, define process measures, design improvements; Six Sigma-shaped) and **Commercial Process Operations** (own gaps and risks, maintain a prioritized needs list, drive execution against a roadmap). **That first function is a consulting engagement CIX can substantially perform from the record** — current-state reconstruction is exactly what a corpus supports. Treat this as one worked example of a general shape: *named, buyer-recognized functions whose inputs are process evidence.*
**How it shows:** system-hop and step counts reconstructed from conversation and email; cycle-time drag on quoting, renewal, onboarding; headcount added adjacent to a broken process.
**Value at risk:** cycle time × deal velocity effect; support headcount attached to papering-over.
**Remedy classes:** **A**, **C**, and **D** (much of it is an IT/systems roadmap, not ours).
**Verification signal:** step count and cycle time on the target process.

### RO-3 · Revenue leakage at handoffs
**What it is:** money lost in the seams — between marketing and sales, sales and finance, CRM and billing.
**Evidence base:** commonly reported that **~42% of companies experience revenue leakage costing 3–7% of top-line annually**, with **1–5% attributed to quote-to-cash inaccuracy**. Root causes cluster on disconnected CRM/ERP forcing handoffs through spreadsheets and email, data re-entry, unauthorized discounting, misconfigured bundles, unbilled contract changes.
**How it shows:** threads where a commitment is made and not carried forward; discount approvals negotiated in email outside the system; leads and expansion signals with no owner; renewals that lapse without a conversation.
**Value at risk:** leaked deal value; the published 3–7% band is a useful anchor for scale, never a substitute for measurement.
**Remedy classes:** **A** (detect the seam), **C** (work the process), **D** (systems integration).
**Verification signal:** handoff-loss rate on the targeted seam.
⚠️ **Source caution:** the 3–7% figure appears mostly in vendor material with unclear provenance. Anchor only; measure locally.

### RO-4 · Coverage and work-allocation mis-siting
**What it is:** the right work in the wrong place — field doing what centre should do, expensive resource on low-value motion, centralisation opportunities unexploited. the RevOps SME's real anchor case sits precisely here: a never-run field-sales transformation assessment, the Google centralisation precedent, and the incubate-Toronto → prove → migrate-offshore recommendation.
**How it shows:** who is doing what kind of revenue work, at what cost tier, in what location, on which account segments.
**Value at risk:** cost delta of re-siting × volume, plus the capacity released to higher-value motion.
**Remedy classes:** **B** primarily — this is the BPO-side offer, and the most direct bridge from assessment to delivery contract.
**Verification signal:** allocation mix post-change.
**Note:** this is the detector that most directly serves the locked G1 buyer (the exec who owns the revenue cost line *and* can move headcount between field and centre) and the acquisition lane simultaneously.

### RO-5 · Maturity gaps against the lifecycle
**What it is:** the generalized case — score each subprocess of the RevOps SME's lifecycle from corpus evidence, surface the gap to the next tier, apply the frequency test.
**Evidence base for the "why now":** Alexander Group reports **78% of executives citing AI as a leading driver of growth and efficiency**, roughly **half of sales leaders using AI for forecasting**, and **over 30% for performance analytics and quota setting**. *(AGI methodology is "conversations with 100+ executives," not a probability sample — directional.)* The buyer is already spending on AI; the open question is whether it's aimed anywhere useful. That is the assessment's actual reason to exist.
**Remedy classes:** all four, by subprocess.

---

## 5. Competitive reality check — read this before scoping further

Two vendors are already close to the CX half of CIX:

- **Operative Intelligence** — classifies root cause and intent from conversations without tagging or dispositions; surfaces what contact drivers cost, where automation pays off, and what to prioritize, **with ROI projections and a built-in business case**. Data refreshes every 15 minutes. Also ships automated QA / agent evaluation and coaching plans — so it occupies the rep-level lane too.
- **SentiSum** — reads every conversation and reports "what to fix, where you're leaking, and what each fix is worth in dollars," with recoverable opportunity split into Cost & Process, Automation, and Conversation Quality, annualized and drillable to source. Also ships an **Action Tracker** that tracks fixes and closes the loop, a Quality Agent scoring 100% of conversations continuously, anomaly alerting, and **BPO-partner scoring against in-house benchmarks**.

That is materially the CX-side product described in §3, already shipping. **This does not kill CIX, but it forecloses "we detect contact drivers" as the differentiation story.** A verification pass on the first draft of this section also knocked out two claimed moats — recorded here rather than quietly dropped:

- ❌ **"Customer owns the intelligence" is not a moat against Operative Intelligence.** Their published FAQ states every model is custom-trained on the customer's own data, never shared or used for generic models. The pooled-data assumption was wrong.
- ❌ **"They hand over a report, we monitor over time" is much thinner than assumed.** SentiSum's Action Tracker and continuous Quality Agent already do close-the-loop verification, and their BPO-partner scoring covers the acquisition-side angle in CX-4. The compliance-loop annuity is a *product requirement*, not a differentiator.

**Added 2026-07-31 — Encore AI** (gainencore.ai, formerly Insait IO): "interaction mining" — calls, emails, texts plus CRM, split into stages to find what moved the process forward and what failed, surfacing friction points and inefficiencies; then trains and deploys AI voice agents on the winning playbooks. **$30M Series A led by Team8 (29 Jul 2026)**, 40+ enterprise customers mostly in financial services, ARR up 5× in under 18 months. Closest competitor found to date — diagnosis *and* execution in one product, and enterprise/CRM-connected rather than mid-market.

*One line on the pattern, parked here rather than developed: every competitor's remedy is software. Ours can be people. Encore can only ever deliver remedy Class A — it cannot conclude that the answer is people doing the work differently, and it certainly cannot supply them.*

What actually survives:

1. **Span** — nobody is running one instrument across the *whole* revenue lifecycle, CX and RevOps together, on the RevOps SME's spine. Both competitors are service-desk-shaped. **This is the differentiation; the rest is table stakes.**
2. **We deliver the remedy** — they sell software and hand over a prioritized list; we have (or acquire) the delivery arm. **Class B findings are ours to execute, not just to name** — that's the roll-up thesis doing work no SaaS competitor can copy.
3. **Assessment-shaped, not platform-shaped** — a paid engagement with judgment attached, sold to operators who have said repeatedly they want delivery, not another tool ("address the pig before you dress the pig"). Different buying motion, different budget line.

**Adjacent category worth knowing:** classical process mining (Celonis et al.) reads system event logs and structurally cannot see the **80–90% of enterprise data that is unstructured** — the negotiation that happened over email, the exception routed through chat. CIX is best understood as **conversation-native process mining for customer-facing operations**. Celonis is moving toward unstructured data, but is enterprise-heavy with a steep adoption curve. This is a useful frame for a sophisticated buyer and a real threat vector to watch.

**Recommendation:** before the build goes far, **take demos from both.** Their outputs are the fastest available specification of the bar CIX must clear on the CX side, and the fastest way to see what they don't do. Note: neither publishes sample reports (SentiSum shows one illustrative audit summary; OI is demo-gated), so this is a calls-not-desk-research task.

---

## 6. Evidence quality — do not skip this

| Tier | Sources | Use |
|---|---|---|
| **Solid** | Gartner self-service figures (dated Aug 2024) · SQM FCR benchmarks · CEB's 81% repeat-contact/high-effort finding · AGI's own client case | Cite in buyer-facing material, with dates |
| **Directional** | Salesforce/SPOTIO seller-time figures (definitions vary by edition) · all AGI survey percentages (non-probability sample) · **failure-demand ranges** (consultancy-derived; the UK 25–40% study is from 2012) · "80–90% of enterprise data is unstructured" (decade-old analyst estimate, never re-derived) | Frame the problem; don't lean on the decimal |
| **Anchor only** | Revenue-leakage 3–7% (MGI Research, via vendor blogs) · failure demand's 2–3× downstream multiplier · various vendor-blog statistics | Scale intuition; never present as fact to a buyer |
| **Do not use** | "57% of inbound calls from website findability failure" · "+88% repurchase / −76% churn" · "61% of revenue execs piloting AI use cases" (this last one was **misattributed in draft** — AGI's 61% refers to executives citing inflation/interest rates as driving revenue *decline*) | Untraceable to primary source, or wrong |

**Hard rule for CIX output:** benchmarks orient the analysis; **every number in a customer deliverable is measured from that customer's own corpus**, or it doesn't appear. A borrowed statistic presented as a finding is the fastest way to lose a room of operators.

---

## 7. Gaps in this pass

- **the RevOps SME's underlying deck and companion model** — mined here via the annotated Jun 16 walkthrough. The source file (`RevOpsSlides.pdf`, Exponentiv) isn't in the workspace; the task-level and data-field detail is the part CIX most needs and it's currently second-hand.
- **The outsourcing lens** — inherited gap from the matrix (A21J-07). Nothing here yet is BPO-native on the *buy* side.
- **AGI's "The Future of Sales: How AI Will Transform Five Key Roles"** — directly on the "new roles" thread PO flagged; not yet retrieved.
- **Industry specificity** — every pathology above is cross-industry. Contact-driver taxonomies are highly vertical in practice.
- **No primary data** — this whole library is desk research plus one collaborator's framework. It is a hypothesis set, not validated demand.

- **Demos not taken** — Operative Intelligence and SentiSum are the live specification of the CX-side bar and neither publishes enough to assess from the outside.

## Changelog

- **2026-07-27 (fact-check pass)** — Subagent verification against primary sources. **Three corrections:** (1) the AGI "61% piloting AI use cases" figure was **misattributed** — AGI's 61% refers to inflation/interest rates driving revenue decline; removed. (2) Salesforce seller-time year labels were wrong — 28% is 2022 (5th ed.), 30% is 2024 (6th ed.), 40% is 2026 (7th ed.); the apparent trend is not interpretable. (3) Two claimed competitive moats were **contradicted by vendor material** — Operative Intelligence custom-trains per customer and doesn't pool data, and SentiSum already ships close-the-loop tracking plus BPO-partner scoring; §5 rewritten so span + owning delivery are the surviving differentiation. Also: failure-demand evidence demoted Solid→Directional (2012 study, consultancy-derived ranges), Gartner self-service figures dated, SQM world-class corrected to 80%+, and a "Do not use" tier added for three untraceable statistics. — Claude (Cowork)
- **2026-07-27** — v1. Built at PO's direction to widen past the single Alexander Group example. Sources: AGI process-excellence article (PO-supplied), the RevOps SME/Exponentiv maturity deck (annotated Jun 16 walkthrough), web research across failure demand, customer effort, seller time, revenue leakage, process mining, and the competitive set. Introduces the four remedy classes (A/B/C/D) per PO's principle that not every finding is ours or AI's, and elevates Class C (process discipline) plus compliance-verification as a deliberate product shape rather than a fallback. Flags Operative Intelligence + SentiSum as materially overlapping on the CX half. — Claude (Cowork)
