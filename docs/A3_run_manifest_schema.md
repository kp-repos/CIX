# A3 — Run Manifest Schema · v1

One `manifest.json` per run directory, alongside `run.db`. Fields (R-IDX-6):

| Field | Type | G1 value |
|---|---|---|
| `manifest_version` | str | "1.0.0" |
| `corpus_hash` | str | sha256 over sorted (interaction_id, canonical unit JSON) |
| `canonical_hash` | str | logical-content hash of the built store |
| `index_version` | str | from `cix.INDEX_VERSION` |
| `tag_vocab_version` | str | from A1 config |
| `label_schema_version` | str\|null | null until G2 |
| `rubric_version` | str\|null | null until G2 |
| `catalogue_version` | str\|null | null until G4 |
| `model_versions` | object | {} until G2 |
| `prompt_hashes` | object | {} until G2 |
| `seeds` | object | {} until G2 (all sampling seeded from G2 on) |
| `thresholds_version` | str\|null | null until G2 freeze |
| `privacy_gate` | str | `synthetic-fixture` \| `scrubbed` |
| `corpus_clearance` | str | provenance/clearance note (informal ruling: manifest records it) |
| `created_at` | str | ISO timestamp — excluded from canonical/corpus hashes |
