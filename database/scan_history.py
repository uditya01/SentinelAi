"""
database/scan_history.py

Stores every completed scan session in SQLite.
Each session has summary stats + a list of individual file results.

Schema
------
scan_sessions   — one row per scan run
scan_files      — one row per file scanned (linked to session)
"""

import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "database", "scan_history.db"
)


# ─── Data models ──────────────────────────────────────────────────────────────

@dataclass
class ScannedFile:
    id: int
    session_id: int
    path: str
    filename: str
    sha256: str
    size_bytes: int
    verdict: str          # CLEAN | THREAT | SUSPICIOUS | UNKNOWN
    malware_name: str
    error: str

    @property
    def is_threat(self):
        return self.verdict in ("THREAT", "SUSPICIOUS")


@dataclass
class ScanSession:
    id: int
    mode: str                  # quick | full | custom
    started_at: str
    finished_at: str
    total_files: int
    scanned_files: int
    skipped_files: int
    threats_found: int
    total_mb: float
    aborted: bool
    files: list[ScannedFile] = field(default_factory=list)

    @property
    def duration(self) -> str:
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            s = datetime.strptime(self.started_at, fmt)
            e = datetime.strptime(self.finished_at, fmt)
            secs = int((e - s).total_seconds())
            if secs < 60:
                return f"{secs}s"
            return f"{secs // 60}m {secs % 60}s"
        except Exception:
            return "—"

    @property
    def status_label(self) -> str:
        if self.aborted:
            return "ABORTED"
        if self.threats_found > 0:
            return "THREATS FOUND"
        return "CLEAN"


# ─── ScanHistoryDB ────────────────────────────────────────────────────────────

class ScanHistoryDB:
    def __init__(self, db_path: str = _DEFAULT_DB):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._setup()

    def _connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

    def _setup(self):
        self._connect()
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                mode          TEXT    NOT NULL DEFAULT 'quick',
                started_at    TEXT    NOT NULL,
                finished_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                total_files   INTEGER NOT NULL DEFAULT 0,
                scanned_files INTEGER NOT NULL DEFAULT 0,
                skipped_files INTEGER NOT NULL DEFAULT 0,
                threats_found INTEGER NOT NULL DEFAULT 0,
                total_mb      REAL    NOT NULL DEFAULT 0,
                aborted       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS scan_files (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   INTEGER NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
                path         TEXT    NOT NULL,
                filename     TEXT    NOT NULL,
                sha256       TEXT    NOT NULL DEFAULT '',
                size_bytes   INTEGER NOT NULL DEFAULT 0,
                verdict      TEXT    NOT NULL DEFAULT 'UNKNOWN',
                malware_name TEXT    NOT NULL DEFAULT '',
                error        TEXT    NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_files_session
                ON scan_files (session_id);
        """)
        self._conn.commit()

    # ── Write ─────────────────────────────────────────────────────────────────

    def save_session(self, scan_result, mode: str, started_at: str) -> int:
        """
        Save a completed ScanResult to the database.
        Returns the new session id.
        """
        self._connect()
        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = self._conn.execute("""
            INSERT INTO scan_sessions
                (mode, started_at, finished_at, total_files, scanned_files,
                 skipped_files, threats_found, total_mb, aborted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mode,
            started_at,
            finished_at,
            scan_result.total_files,
            scan_result.scanned_files,
            scan_result.skipped_files,
            scan_result.threats_found,
            round(scan_result.total_mb, 2),
            int(scan_result.aborted),
        ))
        session_id = cur.lastrowid

        # Save individual file results in batches
        rows = []
        for fr in scan_result.files:
            verdict      = fr.threat.verdict      if fr.threat else "UNKNOWN"
            malware_name = fr.threat.malware_name if fr.threat else ""
            rows.append((
                session_id,
                fr.path,
                os.path.basename(fr.path),
                fr.sha256 or "",
                fr.size_bytes,
                verdict,
                malware_name,
                fr.error or "",
            ))

        self._conn.executemany("""
            INSERT INTO scan_files
                (session_id, path, filename, sha256, size_bytes, verdict, malware_name, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        self._conn.commit()
        return session_id

    # ── Read ──────────────────────────────────────────────────────────────────

    def list_sessions(self, limit: int = 50) -> list[ScanSession]:
        """Return recent scan sessions, newest first. Files not loaded."""
        self._connect()
        rows = self._conn.execute("""
            SELECT * FROM scan_sessions
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [self._row_to_session(r) for r in rows]

    def get_session(self, session_id: int) -> Optional[ScanSession]:
        """Return a session with all its files loaded."""
        self._connect()
        row = self._conn.execute(
            "SELECT * FROM scan_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        session = self._row_to_session(row)
        session.files = self._load_files(session_id)
        return session

    def get_threats(self, session_id: int) -> list[ScannedFile]:
        """Return only the threat/suspicious files from a session."""
        self._connect()
        rows = self._conn.execute("""
            SELECT * FROM scan_files
            WHERE session_id = ? AND verdict IN ('THREAT', 'SUSPICIOUS')
            ORDER BY verdict DESC
        """, (session_id,)).fetchall()
        return [self._row_to_file(r) for r in rows]

    def total_sessions(self) -> int:
        self._connect()
        return self._conn.execute(
            "SELECT COUNT(*) FROM scan_sessions"
        ).fetchone()[0]

    def total_threats_ever(self) -> int:
        self._connect()
        return self._conn.execute(
            "SELECT SUM(threats_found) FROM scan_sessions"
        ).fetchone()[0] or 0

    def delete_session(self, session_id: int):
        self._connect()
        self._conn.execute("DELETE FROM scan_sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    def clear_all(self):
        self._connect()
        self._conn.execute("DELETE FROM scan_sessions")
        self._conn.commit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_files(self, session_id: int) -> list[ScannedFile]:
        rows = self._conn.execute(
            "SELECT * FROM scan_files WHERE session_id = ? ORDER BY verdict DESC",
            (session_id,)
        ).fetchall()
        return [self._row_to_file(r) for r in rows]

    def _row_to_session(self, r) -> ScanSession:
        return ScanSession(
            id            = r["id"],
            mode          = r["mode"],
            started_at    = r["started_at"],
            finished_at   = r["finished_at"],
            total_files   = r["total_files"],
            scanned_files = r["scanned_files"],
            skipped_files = r["skipped_files"],
            threats_found = r["threats_found"],
            total_mb      = r["total_mb"],
            aborted       = bool(r["aborted"]),
        )

    def _row_to_file(self, r) -> ScannedFile:
        return ScannedFile(
            id           = r["id"],
            session_id   = r["session_id"],
            path         = r["path"],
            filename     = r["filename"],
            sha256       = r["sha256"],
            size_bytes   = r["size_bytes"],
            verdict      = r["verdict"],
            malware_name = r["malware_name"],
            error        = r["error"],
        )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None