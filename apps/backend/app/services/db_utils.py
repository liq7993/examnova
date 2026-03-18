from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.services.app_paths import ensure_data_dir, migrate_legacy_file

DB_PATH = migrate_legacy_file("examnova.db")
HISTORY_JSONL = migrate_legacy_file("history.jsonl")
WRONGBOOK_JSONL = migrate_legacy_file("wrongbook.jsonl")


def _ensure_db() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task TEXT NOT NULL,
            summary TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wrongbook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            question_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            course TEXT,
            difficulty TEXT,
            knowledge_points TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_key TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL,
            question_text TEXT NOT NULL,
            topic_label TEXT NOT NULL,
            knowledge_points TEXT NOT NULL,
            mini_quiz TEXT NOT NULL,
            memory_tips TEXT NOT NULL,
            review_mode TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            focused_seconds INTEGER NOT NULL DEFAULT 0,
            curve_ack_stage INTEGER NOT NULL DEFAULT 0,
            focus_ack_stage INTEGER NOT NULL DEFAULT 0,
            last_curve_review_at TEXT,
            last_focus_review_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            course TEXT NOT NULL,
            question_text TEXT NOT NULL,
            session_key TEXT,
            result_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _table_empty(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
    return cursor.fetchone() is None


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            items.append(json.loads(line))
        except Exception:
            continue
    return items


def _migrate_history(conn: sqlite3.Connection) -> None:
    if not HISTORY_JSONL.exists() or not _table_empty(conn, "history"):
        return
    items = _load_jsonl(HISTORY_JSONL)
    if not items:
        return
    conn.executemany(
        "INSERT INTO history (timestamp, task, summary) VALUES (?, ?, ?)",
        [(item.get("timestamp", ""), item.get("task", ""), item.get("summary", "")) for item in items],
    )
    conn.commit()


def _migrate_wrongbook(conn: sqlite3.Connection) -> None:
    if not WRONGBOOK_JSONL.exists() or not _table_empty(conn, "wrongbook"):
        return
    items = _load_jsonl(WRONGBOOK_JSONL)
    if not items:
        return
    conn.executemany(
        """
        INSERT INTO wrongbook (timestamp, question_text, summary, course, difficulty, knowledge_points)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.get("timestamp", ""),
                item.get("question_text", ""),
                item.get("summary", ""),
                item.get("course"),
                item.get("difficulty"),
                json.dumps(item.get("knowledge_points", []), ensure_ascii=False),
            )
            for item in items
        ],
    )
    conn.commit()


def get_connection() -> sqlite3.Connection:
    conn = _ensure_db()
    _migrate_history(conn)
    _migrate_wrongbook(conn)
    return conn
