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

def open_store(db_path: Path) -> Store:
    return Store(db_path)
