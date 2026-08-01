import hashlib
import json
import sqlite3
from pathlib import Path

_LOGICAL_QUERIES = [
    ("interactions", "SELECT id, source_type, date, account_id, thread_id, participants FROM interactions ORDER BY id"),
    ("snippets", "SELECT id, interaction_id, seq, speaker, text, content_hash FROM snippets ORDER BY id"),
    ("snippet_tags", "SELECT snippet_id, tag, value FROM snippet_tags ORDER BY snippet_id, tag, value"),
    ("interaction_tags", "SELECT interaction_id, tag, value FROM interaction_tags ORDER BY interaction_id, tag, value"),
    ("run_meta", "SELECT key, value FROM run_meta ORDER BY key"),
]

def canonical_hash(db_path: Path) -> str:
    """Logical-content equality (R-IDX-4): hash canonical JSON of ordered logical rows.
    Excludes drop_log (runtime events) and any physical/byte-level detail."""
    h = hashlib.sha256()
    con = sqlite3.connect(db_path)
    try:
        for name, query in _LOGICAL_QUERIES:
            h.update(name.encode())
            for row in con.execute(query):
                h.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    finally:
        con.close()
    return h.hexdigest()
