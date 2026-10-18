"""Facts about each upload (name, size, status) in a small SQLite database.

The file itself lives in blob storage; this table only records where it is.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import UploadInfo

_SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
    upload_id         TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    size_bytes        INTEGER NOT NULL,
    content_type      TEXT NOT NULL,
    blob_name         TEXT NOT NULL,
    status            TEXT NOT NULL,
    error             TEXT,
    created_at        TEXT NOT NULL,
    uploaded_at       TEXT
)
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UploadRegistry:
    def __init__(self, database_path: Path):
        self._path = database_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, upload_id: str, original_filename: str, size_bytes: int,
               content_type: str, blob_name: str) -> UploadInfo:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO uploads (upload_id, original_filename, size_bytes, content_type,"
                " blob_name, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (upload_id, original_filename, size_bytes, content_type, blob_name, _now()),
            )
        return self.get(upload_id)

    def get(self, upload_id: str) -> UploadInfo | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM uploads WHERE upload_id = ?", (upload_id,)
            ).fetchone()
        return UploadInfo(**dict(row)) if row else None

    def mark_uploaded(self, upload_id: str) -> UploadInfo:
        with self._connect() as conn:
            conn.execute(
                "UPDATE uploads SET status = 'uploaded', error = NULL, uploaded_at = ?"
                " WHERE upload_id = ?",
                (_now(), upload_id),
            )
        return self.get(upload_id)

    def mark_failed(self, upload_id: str, error: str) -> UploadInfo:
        with self._connect() as conn:
            conn.execute(
                "UPDATE uploads SET status = 'failed', error = ? WHERE upload_id = ?",
                (error, upload_id),
            )
        return self.get(upload_id)
