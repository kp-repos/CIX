import sqlite3
from pathlib import Path
from cix import INDEX_VERSION
from cix.chunker import chunk
from cix.contracts import InteractionUnit
from cix.tags import load_vocabulary, tag_interaction, tag_snippets

_SCHEMA = """
CREATE TABLE interactions (id TEXT PRIMARY KEY, source_type TEXT NOT NULL, date TEXT,
                           account_id TEXT, thread_id TEXT, participants TEXT);
CREATE TABLE snippets (id TEXT PRIMARY KEY, interaction_id TEXT NOT NULL REFERENCES interactions(id),
                       seq INTEGER NOT NULL, speaker TEXT, text TEXT NOT NULL, content_hash TEXT NOT NULL);
CREATE TABLE snippet_tags (snippet_id TEXT NOT NULL REFERENCES snippets(id), tag TEXT NOT NULL, value TEXT NOT NULL);
CREATE TABLE interaction_tags (interaction_id TEXT NOT NULL REFERENCES interactions(id), tag TEXT NOT NULL, value TEXT NOT NULL);
CREATE TABLE drop_log (n INTEGER PRIMARY KEY AUTOINCREMENT, claim_ref TEXT NOT NULL,
                       "check" TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE run_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX ix_snippet_tags ON snippet_tags (tag, value);
CREATE INDEX ix_interaction_tags ON interaction_tags (tag, value);
CREATE TABLE label_artifacts (id TEXT PRIMARY KEY, corpus_hash TEXT, schema_version TEXT,
                              model TEXT, prompts_hash TEXT);
CREATE TABLE labels (artifact_id TEXT REFERENCES label_artifacts(id), interaction_id TEXT,
                     field TEXT, value TEXT, PRIMARY KEY (artifact_id, interaction_id, field));
CREATE TABLE hit_artifacts (id TEXT PRIMARY KEY, label_artifact_id TEXT REFERENCES label_artifacts(id),
                            rubric_version TEXT, model TEXT, prompts_hash TEXT);
CREATE TABLE hits (artifact_id TEXT REFERENCES hit_artifacts(id), item_id TEXT, interaction_id TEXT,
                   unit TEXT, snippet_ids TEXT);
CREATE TABLE validation_results (n INTEGER PRIMARY KEY AUTOINCREMENT, "check" TEXT, item_id TEXT,
                                 status TEXT, detail TEXT);
CREATE TABLE synthesis (artifact_id TEXT, item_id TEXT, body TEXT, PRIMARY KEY (artifact_id, item_id));
"""

def build_store(units: list[InteractionUnit], vocab_path: Path, db_path: Path) -> None:
    """Deterministic build: units arrive sorted (normalize), all inserts in sorted order.
    A run store is written exactly once; refuse an existing path rather than append."""
    if Path(db_path).exists():
        raise FileExistsError(f"run store already exists: {db_path}")
    vocab = load_vocabulary(vocab_path)
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys = ON")  # enforce the schema's REFERENCES (off by default)
        con.executescript(_SCHEMA)
        for u in units:
            con.execute(
                "INSERT INTO interactions VALUES (?,?,?,?,?,?)",
                (u.id, u.source_type, u.date, u.account_id, u.thread_id, ",".join(u.participants)),
            )
            snippets = chunk(u)
            for s in snippets:
                con.execute(
                    "INSERT INTO snippets VALUES (?,?,?,?,?,?)",
                    (s["id"], s["interaction_id"], s["seq"], s["speaker"], s["text"], s["content_hash"]),
                )
            con.executemany("INSERT INTO snippet_tags VALUES (?,?,?)", tag_snippets(snippets, vocab))
            con.executemany("INSERT INTO interaction_tags VALUES (?,?,?)", tag_interaction(u, snippets))
        con.executemany(
            "INSERT INTO run_meta VALUES (?,?)",
            sorted({"index_version": INDEX_VERSION, "tag_vocab_version": vocab["version"]}.items()),
        )
        con.commit()
    finally:
        con.close()

class Store:
    def __init__(self, db_path: Path):
        self.con = sqlite3.connect(db_path)
        self.con.execute("PRAGMA foreign_keys = ON")  # per-connection; enforce declared FKs
        self.con.row_factory = sqlite3.Row

    def snippet(self, snippet_id: str) -> dict | None:
        row = self.con.execute("SELECT * FROM snippets WHERE id=?", (snippet_id,)).fetchone()
        return dict(row) if row else None

    def span(self, interaction_id: str, start: int, end: int) -> list[dict]:
        rows = self.con.execute(
            "SELECT * FROM snippets WHERE interaction_id=? AND seq BETWEEN ? AND ? ORDER BY seq",
            (interaction_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]

    def snippets_for_ref(self, ref: str) -> list[dict]:
        """Resolve a hits-table snippet_ids value ("id" or "id-id" range) to snippet rows.
        Snippet ids themselves contain no '-', but interaction ids do (e.g. int-001:0000),
        so a range is split on the first '-' whose two sides are both real snippets in the
        same interaction. Unresolvable refs return [] (fail closed)."""
        one = self.snippet(ref)
        if one:
            return [one]
        for i, ch in enumerate(ref):
            if ch == "-":
                a, b = self.snippet(ref[:i]), self.snippet(ref[i + 1:])
                if a and b and a["interaction_id"] == b["interaction_id"]:
                    return self.span(a["interaction_id"], a["seq"], b["seq"])
        return []

    def snippets_with_tag(self, tag: str, value: str | None = None) -> list[str]:
        if value is None:
            rows = self.con.execute("SELECT snippet_id FROM snippet_tags WHERE tag=? ORDER BY snippet_id", (tag,))
        else:
            rows = self.con.execute(
                "SELECT snippet_id FROM snippet_tags WHERE tag=? AND value=? ORDER BY snippet_id", (tag, value)
            )
        return [r["snippet_id"] for r in rows]

    def interactions_with_tag(self, tag: str, value: str | None = None) -> list[str]:
        if value is None:
            rows = self.con.execute("SELECT interaction_id FROM interaction_tags WHERE tag=? ORDER BY interaction_id", (tag,))
        else:
            rows = self.con.execute(
                "SELECT interaction_id FROM interaction_tags WHERE tag=? AND value=? ORDER BY interaction_id", (tag, value)
            )
        return [r["interaction_id"] for r in rows]

    def log_drop(self, claim_ref: str, check: str, detail: str) -> None:
        self.con.execute('INSERT INTO drop_log (claim_ref, "check", detail) VALUES (?,?,?)', (claim_ref, check, detail))
        self.con.commit()

    def drops(self) -> list[dict]:
        return [dict(r) for r in self.con.execute("SELECT * FROM drop_log ORDER BY n")]

    def meta(self, key: str) -> str | None:
        row = self.con.execute("SELECT value FROM run_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    @staticmethod
    def _key(*parts: str) -> str:
        import hashlib
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]

    def ensure_label_artifact(self, corpus_hash: str, schema_version: str, model: str, prompts_hash: str) -> str:
        aid = self._key("labels", corpus_hash, schema_version, model, prompts_hash)
        self.con.execute("INSERT OR IGNORE INTO label_artifacts VALUES (?,?,?,?,?)",
                         (aid, corpus_hash, schema_version, model, prompts_hash))
        self.con.commit()
        return aid

    def ensure_hit_artifact(self, label_artifact_id: str, rubric_version: str, model: str, prompts_hash: str) -> str:
        aid = self._key("hits", label_artifact_id, rubric_version, model, prompts_hash)
        self.con.execute("INSERT OR IGNORE INTO hit_artifacts VALUES (?,?,?,?,?)",
                         (aid, label_artifact_id, rubric_version, model, prompts_hash))
        self.con.commit()
        return aid

    def write_labels(self, artifact_id: str, interaction_id: str, fields: dict) -> None:
        for field, value in sorted(fields.items()):
            self.con.execute("INSERT OR REPLACE INTO labels VALUES (?,?,?,?)",
                             (artifact_id, interaction_id, field, str(value)))
        self.con.commit()

    def labels_for(self, artifact_id: str, interaction_id: str) -> dict:
        rows = self.con.execute("SELECT field, value FROM labels WHERE artifact_id=? AND interaction_id=?",
                                (artifact_id, interaction_id))
        return {r["field"]: r["value"] for r in rows}

    def labeled_interactions(self, artifact_id: str) -> list[str]:
        rows = self.con.execute(
            "SELECT DISTINCT interaction_id FROM labels WHERE artifact_id=? ORDER BY interaction_id",
            (artifact_id,))
        return [r["interaction_id"] for r in rows]

    def write_hit(self, artifact_id: str, item_id: str, interaction_id: str, unit: str, snippet_ids: str) -> None:
        self.con.execute("INSERT INTO hits VALUES (?,?,?,?,?)",
                         (artifact_id, item_id, interaction_id, unit, snippet_ids))
        self.con.commit()

    def hits_for(self, artifact_id: str) -> list[dict]:
        rows = self.con.execute(
            "SELECT * FROM hits WHERE artifact_id=? ORDER BY item_id, interaction_id, snippet_ids", (artifact_id,))
        return [dict(r) for r in rows]

    def write_validation(self, check: str, item_id: str | None, status: str, detail: str) -> None:
        self.con.execute('INSERT INTO validation_results ("check", item_id, status, detail) VALUES (?,?,?,?)',
                         (check, item_id, status, detail))
        self.con.commit()

    def validations(self) -> list[dict]:
        return [dict(r) for r in self.con.execute("SELECT * FROM validation_results ORDER BY n")]

    def write_synthesis(self, artifact_id: str, item_id: str, body: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO synthesis VALUES (?,?,?)", (artifact_id, item_id, body))
        self.con.commit()

    def synthesis_for(self, artifact_id: str) -> list[dict]:
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM synthesis WHERE artifact_id=? ORDER BY item_id", (artifact_id,))]

def open_store(db_path: Path) -> Store:
    return Store(db_path)
