from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


UTC = timezone.utc


@dataclass(frozen=True)
class ReviewStrategy:
    name: str
    label: str
    curve_minutes: list[int]
    focus_minutes: list[int]


CRAM_STRATEGY = ReviewStrategy(
    name="cram",
    label="冲刺模式",
    curve_minutes=[10, 30, 120, 720, 1440],
    focus_minutes=[30, 60, 90],
)

STANDARD_STRATEGY = ReviewStrategy(
    name="standard",
    label="常规模式",
    curve_minutes=[30, 1440, 4320, 10080],
    focus_minutes=[30, 75, 120],
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def to_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def choose_strategy(review_mode: str, explanation_mode: str, question_text: str, difficulty: str) -> ReviewStrategy:
    if review_mode == "cram":
        return CRAM_STRATEGY
    if review_mode == "standard":
        return STANDARD_STRATEGY

    combined = f"{question_text} {difficulty} {explanation_mode}".lower()
    exam_signals = ["考", "冲刺", "期末", "明天", "今晚", "exam", "quiz", "hard", "难"]
    if any(signal in combined for signal in exam_signals):
        return CRAM_STRATEGY
    return STANDARD_STRATEGY


def get_strategy(name: str) -> ReviewStrategy:
    if name == CRAM_STRATEGY.name:
        return CRAM_STRATEGY
    return STANDARD_STRATEGY


def compute_due_stage(elapsed_minutes: int, checkpoints: list[int]) -> int:
    return sum(1 for minute in checkpoints if elapsed_minutes >= minute)


def next_checkpoint_time(started_at: datetime, checkpoints: list[int], ack_stage: int) -> datetime | None:
    if ack_stage >= len(checkpoints):
        return None
    return started_at + timedelta(minutes=checkpoints[ack_stage])
