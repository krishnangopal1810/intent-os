"""SQLite health and durability helpers for the dogfood beta."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def checkpoint(conn: sqlite3.Connection, mode: str = "PASSIVE") -> None:
    if mode not in {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}:
        raise ValueError("unsupported SQLite checkpoint mode")
    conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchall()


def quick_check(conn: sqlite3.Connection) -> str:
    row = conn.execute("PRAGMA quick_check").fetchone()
    return str(row[0]) if row else "unknown"


def db_file_stats(db_path: str | None) -> dict[str, int | None]:
    if not db_path:
        return {"db_bytes": None, "wal_bytes": None, "shm_bytes": None}
    path = Path(db_path)
    return {
        "db_bytes": file_size(path),
        "wal_bytes": file_size(path.with_name(path.name + "-wal")),
        "shm_bytes": file_size(path.with_name(path.name + "-shm")),
    }


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0
