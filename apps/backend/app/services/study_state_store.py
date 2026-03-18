from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from app.services.db_utils import get_connection
from app.services.review_strategy import (
    choose_strategy,
    compute_due_stage,
    get_strategy,
    next_checkpoint_time,
    to_timestamp,
    utc_now,
    parse_timestamp,
)


def build_session_key(course: str, question_text: str) -> str:
    normalized = f"{course.strip().lower()}::{question_text.strip().lower()}"
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


@dataclass
class SessionView:
    session_key: str
    course: str
    question_text: str
    topic_label: str
    knowledge_points: list[str]
    mini_quiz: list[str]
    memory_tips: list[str]
    review_mode: str
    strategy_name: str
    started_at: str
    last_activity_at: str
    focused_seconds: int
    wall_elapsed_minutes: int
    focused_minutes: int
    curve_ack_stage: int
    focus_ack_stage: int
    curve_due_count: int
    focus_due_count: int
    next_curve_due_at: str | None
    next_focus_due_at: str | None
    next_curve_prompt: str | None
    next_focus_prompt: str | None


def _row_to_session_view(row) -> SessionView:
    started_at = parse_timestamp(row["started_at"]) or utc_now()
    now = utc_now()
    wall_elapsed_minutes = max(0, int((now - started_at).total_seconds() // 60))
    focused_seconds = int(row["focused_seconds"] or 0)
    focused_minutes = max(0, focused_seconds // 60)
    strategy = get_strategy(row["strategy_name"])
    curve_due_count = compute_due_stage(wall_elapsed_minutes, strategy.curve_minutes)
    focus_due_count = compute_due_stage(focused_minutes, strategy.focus_minutes)

    mini_quiz = json.loads(row["mini_quiz"])
    knowledge_points = json.loads(row["knowledge_points"])
    memory_tips = json.loads(row["memory_tips"])

    next_curve_due_at = next_checkpoint_time(started_at, strategy.curve_minutes, row["curve_ack_stage"])
    next_focus_due_at = None
    next_focus_prompt = None
    if row["focus_ack_stage"] < len(strategy.focus_minutes):
        minute = strategy.focus_minutes[row["focus_ack_stage"]]
        next_focus_due_at = f"{minute} 分钟专注里程碑"
        next_focus_prompt = f"累计专注 {minute} 分钟后，抽一道小题自测。"

    next_curve_prompt = None
    if row["curve_ack_stage"] < len(strategy.curve_minutes):
        minute = strategy.curve_minutes[row["curve_ack_stage"]]
        hours = minute / 60
        if minute < 60:
            next_curve_prompt = f"{minute} 分钟后回顾刚学内容。"
        elif hours < 24:
            next_curve_prompt = f"{int(hours)} 小时后再回顾一次。"
        else:
            next_curve_prompt = f"{int(hours // 24)} 天后进入下一轮复习。"

    return SessionView(
        session_key=row["session_key"],
        course=row["course"],
        question_text=row["question_text"],
        topic_label=row["topic_label"],
        knowledge_points=knowledge_points,
        mini_quiz=mini_quiz,
        memory_tips=memory_tips,
        review_mode=row["review_mode"],
        strategy_name=row["strategy_name"],
        started_at=row["started_at"],
        last_activity_at=row["last_activity_at"],
        focused_seconds=focused_seconds,
        wall_elapsed_minutes=wall_elapsed_minutes,
        focused_minutes=focused_minutes,
        curve_ack_stage=row["curve_ack_stage"],
        focus_ack_stage=row["focus_ack_stage"],
        curve_due_count=max(0, curve_due_count - int(row["curve_ack_stage"] or 0)),
        focus_due_count=max(0, focus_due_count - int(row["focus_ack_stage"] or 0)),
        next_curve_due_at=to_timestamp(next_curve_due_at) if next_curve_due_at else None,
        next_focus_due_at=next_focus_due_at,
        next_curve_prompt=next_curve_prompt,
        next_focus_prompt=next_focus_prompt,
    )


def _select_session(session_key: str):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM study_sessions WHERE session_key = ?", (session_key,)).fetchone()
        return row
    finally:
        conn.close()


def start_or_resume_session(
    *,
    course: str,
    question_text: str,
    topic_label: str,
    knowledge_points: list[str],
    mini_quiz: list[str],
    memory_tips: list[str],
    review_mode: str,
    explanation_mode: str,
    difficulty: str,
) -> SessionView:
    now = utc_now()
    session_key = build_session_key(course, question_text)
    strategy = choose_strategy(review_mode, explanation_mode, question_text, difficulty)
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM study_sessions WHERE session_key = ?", (session_key,)).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO study_sessions (
                    session_key, course, question_text, topic_label, knowledge_points, mini_quiz, memory_tips,
                    review_mode, strategy_name, started_at, last_activity_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_key,
                    course,
                    question_text,
                    topic_label,
                    json.dumps(knowledge_points, ensure_ascii=False),
                    json.dumps(mini_quiz, ensure_ascii=False),
                    json.dumps(memory_tips, ensure_ascii=False),
                    review_mode,
                    strategy.name,
                    to_timestamp(now),
                    to_timestamp(now),
                ),
            )
        else:
            conn.execute(
                """
                UPDATE study_sessions
                SET course = ?, question_text = ?, topic_label = ?, knowledge_points = ?, mini_quiz = ?, memory_tips = ?,
                    review_mode = ?, strategy_name = ?, last_activity_at = ?
                WHERE session_key = ?
                """,
                (
                    course,
                    question_text,
                    topic_label,
                    json.dumps(knowledge_points, ensure_ascii=False),
                    json.dumps(mini_quiz, ensure_ascii=False),
                    json.dumps(memory_tips, ensure_ascii=False),
                    review_mode,
                    strategy.name,
                    to_timestamp(now),
                    session_key,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return get_session(session_key)


def get_session(session_key: str) -> SessionView:
    row = _select_session(session_key)
    if row is None:
        raise KeyError(session_key)
    return _row_to_session_view(row)


def heartbeat_session(session_key: str, active_seconds: int) -> SessionView:
    clamped = max(0, min(active_seconds, 180))
    now = to_timestamp(utc_now())
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE study_sessions
            SET focused_seconds = focused_seconds + ?, last_activity_at = ?
            WHERE session_key = ?
            """,
            (clamped, now, session_key),
        )
        conn.commit()
    finally:
        conn.close()
    return get_session(session_key)


def acknowledge_review(session_key: str, trigger_type: str) -> SessionView:
    current = get_session(session_key)
    conn = get_connection()
    try:
        if trigger_type == "focus":
            max_stage = len(get_strategy(current.strategy_name).focus_minutes)
            next_stage = min(max_stage, current.focus_ack_stage + max(1, current.focus_due_count or 1))
            conn.execute(
                """
                UPDATE study_sessions
                SET focus_ack_stage = ?, last_focus_review_at = ?
                WHERE session_key = ?
                """,
                (next_stage, to_timestamp(utc_now()), session_key),
            )
        else:
            max_stage = len(get_strategy(current.strategy_name).curve_minutes)
            next_stage = min(max_stage, current.curve_ack_stage + max(1, current.curve_due_count or 1))
            conn.execute(
                """
                UPDATE study_sessions
                SET curve_ack_stage = ?, last_curve_review_at = ?
                WHERE session_key = ?
                """,
                (next_stage, to_timestamp(utc_now()), session_key),
            )
        conn.commit()
    finally:
        conn.close()
    return get_session(session_key)


def list_due_sessions(limit: int = 10) -> list[SessionView]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM study_sessions ORDER BY last_activity_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    sessions = [_row_to_session_view(row) for row in rows]
    return [session for session in sessions if session.curve_due_count > 0 or session.focus_due_count > 0]
