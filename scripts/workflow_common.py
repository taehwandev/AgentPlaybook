"""Shared constants and helpers for workflow routing."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, TypeVar


ROOT = Path(__file__).resolve().parents[1]
QUESTION_ROUTE_COMMANDS = {"triage", "ambiguity"}
ANSWER_ONLY_CLARITY = "direct-question"
RETRY_LIMIT = 1
ATTEMPT_LIMIT = RETRY_LIMIT + 1
RETRY_SCOPE = "first_missed_gate"
SIGNAL_DISPLAY = {
    "SUCCESS": "\U0001f431\U0001f7e2 SUCCESS",
    "FAIL": "\U0001f431\U0001f534 FAIL",
}

T = TypeVar("T")


def unique(items: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    result: list[T] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def display_signal(signal: object) -> str:
    return SIGNAL_DISPLAY.get(str(signal), str(signal))
