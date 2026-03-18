from __future__ import annotations

from datetime import datetime

from app.services.db_utils import get_connection


def append_history(entry: dict) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO history (timestamp, task, summary) VALUES (?, ?, ?)",
        (entry.get("timestamp", ""), entry.get("task", ""), entry.get("summary", "")),
    )
    conn.commit()


def load_recent(limit: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT timestamp, task, summary FROM history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    items = [{"timestamp": row["timestamp"], "task": row["task"], "summary": row["summary"]} for row in rows]
    return list(reversed(items))


def load_all() -> list[dict]:
    conn = get_connection()
    cursor = conn.execute("SELECT timestamp, task, summary FROM history ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    return [{"timestamp": row["timestamp"], "task": row["task"], "summary": row["summary"]} for row in rows]


def clear_history() -> int:
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) AS count FROM history")
    count = int(cursor.fetchone()["count"])
    conn.execute("DELETE FROM history")
    conn.commit()
    return count


def build_entry(task: str, summary: str) -> dict:
    timestamp = datetime.now().isoformat(timespec="seconds")
    return {"timestamp": timestamp, "task": task, "summary": summary}
