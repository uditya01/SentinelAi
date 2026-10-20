
import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "threat_log.db"
)


class ThreatLog:

    def __init__(self):
        self.create_table()

    def connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS threat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    threat_name TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    sha256 TEXT,
                    source TEXT,
                    action TEXT
                )
            """)

    def add_log(
        self,
        threat_name,
        file_path,
        sha256,
        source,
        action="Detected",
    ):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO threat_logs (
                    time,
                    threat_name,
                    file_name,
                    file_path,
                    sha256,
                    source,
                    action
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                threat_name,
                os.path.basename(file_path),
                file_path,
                sha256,
                source,
                action,
            ))

    def get_logs(self):
        with self.connect() as conn:
            return conn.execute("""
                SELECT *
                FROM threat_logs
                ORDER BY id DESC
            """).fetchall()

    def delete_all(self):
        with self.connect() as conn:
            conn.execute("DELETE FROM threat_logs")

    def total_logs(self):
        with self.connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM threat_logs"
            ).fetchone()[0]
