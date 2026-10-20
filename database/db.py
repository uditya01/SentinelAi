"""
database/db.py

SQLite database for storing known malicious SHA-256 hashes.
Schema is intentionally minimal — one table, one index, fast lookups.

Usage
-----
    from database.db import HashDatabase

    db = HashDatabase()
    db.setup()

    result = db.lookup("abc123...")
    # returns {"sha256": ..., "malware_name": ..., "source": ...} or None

    db.insert_many([
        {"sha256": "abc...", "malware_name": "Trojan.X", "source": "MalwareBazaar"},
    ])
"""

import sqlite3
import os
from typing import Optional

# Default DB path: <project_root>/database/hashes.db
_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "hashes.db"
)


class HashDatabase:
    def __init__(self, db_path: str = _DEFAULT_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    # ── Connection management ─────────────────────────────────────────────────

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    # ── Schema ────────────────────────────────────────────────────────────────

    def setup(self):
        """Create tables and indexes if they don't exist."""
        self.connect()
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS malware_hashes (
                sha256       TEXT PRIMARY KEY,
                malware_name TEXT NOT NULL DEFAULT '',
                source       TEXT NOT NULL DEFAULT '',
                added_at     TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # Index already exists as PRIMARY KEY, but add explicit one for safety
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sha256
            ON malware_hashes (sha256)
        """)
        self._conn.commit()

  

    def lookup(self, sha256: str) -> Optional[dict]:
        """
        Check if a SHA-256 hash is in the database.
        Returns a dict with keys sha256, malware_name, source — or None.
        """
        self.connect()
        row = self._conn.execute(
            "SELECT sha256, malware_name, source FROM malware_hashes WHERE sha256 = ?",
            (sha256.lower(),)
        ).fetchone()
        return dict(row) if row else None

    def total_hashes(self) -> int:
        self.connect()
        return self._conn.execute(
            "SELECT COUNT(*) FROM malware_hashes"
        ).fetchone()[0]

    # ── Write ─────────────────────────────────────────────────────────────────

    def insert_many(self, records: list[dict], batch_size: int = 5000):
        """
        Bulk insert hashes. Each record must have 'sha256'.
        Optional keys: 'malware_name', 'source'.
        Skips duplicates (INSERT OR IGNORE).
        """
        self.connect()
        rows = [
            (
                r["sha256"].lower(),
                r.get("malware_name", ""),
                r.get("source", ""),
            )
            for r in records
        ]
        for i in range(0, len(rows), batch_size):
            self._conn.executemany(
                "INSERT OR IGNORE INTO malware_hashes (sha256, malware_name, source) VALUES (?, ?, ?)",
                rows[i : i + batch_size],
            )
        self._conn.commit()

    def clear(self):
        """Wipe all hashes — useful for re-seeding."""
        self.connect()
        self._conn.execute("DELETE FROM malware_hashes")
        self._conn.commit()