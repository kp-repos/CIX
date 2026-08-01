# A12 — Input Data Contract · v1

A corpus is a directory of `*.json` files, one interaction per file, each matching
the `InteractionUnit` contract (`src/cix/contracts.py`):

| Field | Req | Notes |
|---|---|---|
| `id` | yes | unique across the corpus; stable |
| `source_type` | yes | `transcript` \| `email` \| `note` |
| `participants` | no | display roles, e.g. `["agent","customer"]` |
| `date` | no | ISO `YYYY-MM-DD` |
| `account_id` | no | pseudonymized upstream for real data (R-PII-2); only legal basis for account/chain tags |
| `thread_id` | no | same |
| `segments[]` | yes, ≥1 | `{speaker?, ts?, text}` — one segment per speaker turn |

Eligibility: files failing validation abort the run before any processing
(R-RUN-1: deterministic config validation before any paid call — at G1, before any indexing).
Real corpora additionally pass the scrub stage before this contract applies (G4+;
fixtures here are synthetic, privacy gate records `synthetic-fixture`).
Filenames are arbitrary; ordering never matters (determinism is by sorted `id`).
