from __future__ import annotations

import json

from app.services.db_utils import get_connection
from app.services.review_strategy import to_timestamp, utc_now


def add_study_note(course: str, question_text: str, session_key: str | None, result: dict) -> None:
    conn = get_connection()
    try:
        timestamp = to_timestamp(utc_now())
        result_json = json.dumps(result, ensure_ascii=False)
        if session_key:
            existing = conn.execute(
                "SELECT id FROM study_notes WHERE session_key = ? ORDER BY id DESC LIMIT 1",
                (session_key,),
            ).fetchone()
        else:
            existing = None

        if existing is None:
            conn.execute(
                """
                INSERT INTO study_notes (timestamp, course, question_text, session_key, result_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, course, question_text, session_key, result_json),
            )
        else:
            conn.execute(
                """
                UPDATE study_notes
                SET timestamp = ?, course = ?, question_text = ?, result_json = ?
                WHERE id = ?
                """,
                (timestamp, course, question_text, result_json, existing["id"]),
            )
        conn.commit()
    finally:
        conn.close()


def recent_study_notes(limit: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT timestamp, course, question_text, session_key, result_json
            FROM study_notes
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    items: list[dict] = []
    for row in rows:
      items.append(
          {
              "timestamp": row["timestamp"],
              "course": row["course"],
              "question_text": row["question_text"],
              "session_key": row["session_key"],
              "result": json.loads(row["result_json"]),
          }
      )
    return list(reversed(items))
