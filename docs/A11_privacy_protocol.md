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

Two layers. **Automated residual re-scan** runs on 100% of scrubbed snippets: any leftover
email/phone pattern is a residual hit. **Sampled human audit** draws a seeded sample of
scrubbed snippets for a reviewer to confirm no residual identity. The manifest `privacy_gate`
is `pass` (zero residual hits in the sample), `audit-pending` (sample drawn, human sign-off
outstanding), or `fail` (residual hits) — a `fail` is a release gate (PRD §8), stopping the
run, not the thesis.

## Honesty

The scrub stage ships and runs even on cleared test data (R-PII-4): the capability is the
point. G4 exercises it on synthetic corpora; the first real-data scrub is the post-G4 follow-on.
