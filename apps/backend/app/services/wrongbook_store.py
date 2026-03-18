from __future__ import annotations

import json
from datetime import datetime

from app.services.db_utils import get_connection


def append_wrongbook(entry: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO wrongbook (timestamp, question_text, summary, course, difficulty, knowledge_points)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("timestamp", ""),
            entry.get("question_text", ""),
            entry.get("summary", ""),
            entry.get("course"),
            entry.get("difficulty"),
            json.dumps(entry.get("knowledge_points", []), ensure_ascii=False),
        ),
    )
    conn.commit()


def load_wrongbook(limit: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT timestamp, question_text, summary, course, difficulty, knowledge_points
        FROM wrongbook
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    items: list[dict] = []
    for row in rows:
        try:
            points = json.loads(row["knowledge_points"])
        except Exception:
            points = []
        items.append(
            {
                "timestamp": row["timestamp"],
                "question_text": row["question_text"],
                "summary": row["summary"],
                "course": row["course"],
                "difficulty": row["difficulty"],
                "knowledge_points": points,
            }
        )
    return list(reversed(items))


def build_entry(
    question_text: str,
    summary: str,
    course: str | None,
    difficulty: str | None,
    knowledge_points: list[str],
) -> dict:
    timestamp = datetime.now().isoformat(timespec="seconds")
    return {
        "timestamp": timestamp,
        "question_text": question_text,
        "summary": summary,
        "course": course,
        "difficulty": difficulty,
        "knowledge_points": knowledge_points,
    }
