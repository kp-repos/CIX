# A11 — Privacy Threat Model + Scrub-Audit Protocol · v1

**Owner:** PO · **Status:** pending ratification (Checkpoint P of the G4 plan)
**Machine-readable half:** `configs/privacy_protocol_v1.yaml`
**Governs:** R-PII-1…4, PRD §8 privacy release gate · **Runs on:** every corpus, cleared or not (R-PII-4)

## Threat model

The corpus carries customer-identifying detail (names, emails, phones, account references)
that must never persist unscrubbed in the store, logs, traces, or manifest (R-PII-1). The
measurable signal — counts, amounts, dates, process shape — must survive; identity must not.
Linkage identifiers (who spoke, which account, which thread) are pseudonymized rather than
deleted so chain/account-unit items remain computable (R-PII-2).

## Scrub stages (deterministic, ingest-time)

1. **Deterministic patterns** — emails and phone numbers are redacted to fixed tokens.
   Currency amounts, dates, and quantities are deliberately *kept*.
2. **Name/linkage pseudonymization** — known participants, `account_id`, and `thread_id`
   are replaced by salted-hash stable tokens (`PERSON-xxxxxxxx`, `ACCT-xxxxxxxx`,
   `THREAD-xxxxxxxx`). The salt is per-run and recorded in the manifest.
3. **NER pass (opt-in, model-backed)** — residual person/org/location entities the rules
   miss. Off by default so the pipeline is fully testable offline; the rules pass is the
   G4 default on synthetic/cleared data.

## Audit (R-PII-1)

Two layers. **Automated residual re-scan** runs on 100% of scrubbed snippets (text and
speaker fields): any leftover email/phone pattern is a residual hit. **Sampled human audit**
draws a seeded sample of scrubbed snippets for a reviewer to confirm no residual identity.

The manifest `privacy_gate` status:
- `pass` — zero automated residual hits (email/phone scan). At G4 this is automated clearance
  only; the human-sample layer is defined here but its sign-off is recorded out-of-band.
- `audit-pending` — a human sample has been drawn but sign-off is outstanding (used once human
  review is operational on real data).
- `fail` — one or more automated residual hits. A `fail` is a release gate (PRD §8), stopping
  the run, not the thesis.

The `privacy_gate` value is deliberately narrow: the automated scan covers email/phone patterns
only, and name/linkage scrubbing relies on the rules pass. The manifest therefore also records
`privacy_scan: {residual_scope: "email+phone", ner: "rules-only"}` so a `pass` is never mistaken
for a full-PII clearance.

## Known limitations of the rules pass (accepted for G4 synthetic scope)

The deterministic rules pass does not resolve realistic name populations perfectly:
two participants sharing a first name can cross-link, and lowercase re-mentions of a name
are missed (`str.replace` is case-sensitive). These bite only on real name populations;
G4 runs on synthetic/cleared data. The model-backed NER pass (opt-in) is the answer for
the post-G4 real-data scrub, where it supplements the rules pass.
Two real-data follow-on notes: the per-run salt is currently derived from the run seed (fine for
synthetic data, but on real data the salt must be a per-run secret not stored beside the tokens,
with a longer token); and exact dates are kept as measurable signal but are a re-identification
vector on real data. Both are addressed in the post-G4 real-data scrub, not here.

## Honesty

The scrub stage ships and runs even on cleared test data (R-PII-4): the capability is the
point. G4 exercises it on synthetic corpora; the first real-data scrub is the post-G4 follow-on.
