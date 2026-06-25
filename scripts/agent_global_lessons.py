"""Local cross-agent lesson storage for missed workflow gates."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATE_HOME_ENV = "AGENTPLAYBOOK_STATE_HOME"
SAFE_SLUG_RE = re.compile(r"[^a-z0-9_]+")
LESSON_STATUSES = ("accepted", "promoted")


def state_home() -> Path:
    override = os.environ.get(STATE_HOME_ENV, "").strip()
    return Path(override).expanduser() if override else Path.home() / ".agentplaybook"


def lesson_summary(limit: int = 10) -> dict[str, Any]:
    root = state_home()
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "state_home": "env" if os.environ.get(STATE_HOME_ENV) else "default",
        "available": root.exists(),
        "accepted": [],
        "promoted": [],
        "candidate_count": _count_json_files(root / "lessons" / "inbox"),
    }
    for status in LESSON_STATUSES:
        summary[status] = _read_lessons(root / "lessons" / status, limit)
    return summary


def write_retrospective_candidate(finish_result: dict[str, Any]) -> dict[str, Any]:
    if not finish_result.get("retrospective_required"):
        return {"created": False, "reason": "retrospective_not_required"}

    lesson = retrospective_candidate(finish_result)
    root = state_home()
    relative_path = Path("lessons") / "inbox" / f"{lesson['created_at_compact']}-{lesson['lesson_id']}.json"
    path = root / relative_path
    try:
        _atomic_write_json(path, lesson)
        _update_index(root, relative_path, lesson)
    except OSError as error:
        return {
            "created": False,
            "reason": "write_failed",
            "error": error.__class__.__name__,
        }
    return {
        "created": True,
        "status": lesson["promotion_status"],
        "lesson_id": lesson["lesson_id"],
        "relative_path": str(relative_path),
    }


def retrospective_candidate(finish_result: dict[str, Any]) -> dict[str, Any]:
    missed_gates = [_slug(gate) for gate in finish_result.get("missed_gates", []) if gate]
    policy_failures = _policy_failure_count(finish_result)
    failure_type = _failure_type(missed_gates, policy_failures)
    root_cause = _root_cause(missed_gates, policy_failures)
    created_at = datetime.now(timezone.utc).isoformat()
    seed = {
        "failure_type": failure_type,
        "missed_gates": missed_gates,
        "policy_failure_count": policy_failures,
        "root_cause": root_cause,
        "next_action": "run_retrospective_then_retry_same_scope",
    }
    lesson_id = hashlib.sha256(json.dumps(seed, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "lesson_id": lesson_id,
        "created_at": created_at,
        "created_at_compact": created_at.replace(":", "").replace("-", "").split(".")[0].replace("T", "-"),
        "source": "agent_finish_check",
        "status": "candidate",
        "failure_type": failure_type,
        "missed_gates": missed_gates,
        "policy_failure_count": policy_failures,
        "root_cause": root_cause,
        "next_action": "run_retrospective_then_retry_same_scope",
        "retry_rule": "resume_first_missed_gate_after_retrospective",
        "promotion_target": "shared_doc_or_hook_or_test",
        "promotion_status": "candidate",
        "privacy": "safe_slugs_only",
    }


def _policy_failure_count(finish_result: dict[str, Any]) -> int:
    return sum(
        1
        for signal in finish_result.get("gate_signals", [])
        if signal.get("gate") == "gate evidence policy" and signal.get("signal") == "FAIL"
    )


def _failure_type(missed_gates: list[str], policy_failures: int) -> str:
    if missed_gates and policy_failures:
        return "missed_gate_and_policy_failure"
    if missed_gates:
        return "missed_required_gate"
    if policy_failures:
        return "gate_evidence_policy_failure"
    return "finish_gate_failure"


def _root_cause(missed_gates: list[str], policy_failures: int) -> str:
    if missed_gates:
        return "missing_required_gate_evidence"
    if policy_failures:
        return "weak_gate_evidence"
    return "finish_failed_before_completion"


def _slug(value: str) -> str:
    normalized = SAFE_SLUG_RE.sub("_", value.strip().lower().replace("-", "_")).strip("_")
    return normalized or "unknown"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _update_index(root: Path, relative_path: Path, lesson: dict[str, Any]) -> None:
    path = root / "index.json"
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        index = {"schema_version": SCHEMA_VERSION, "lessons": []}

    entry = {
        "lesson_id": lesson["lesson_id"],
        "status": lesson["status"],
        "failure_type": lesson["failure_type"],
        "root_cause": lesson["root_cause"],
        "promotion_status": lesson["promotion_status"],
        "relative_path": str(relative_path),
    }
    lessons = [item for item in index.get("lessons", []) if item.get("lesson_id") != lesson["lesson_id"]]
    lessons.append(entry)
    index = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "lessons": lessons[-100:],
    }
    _atomic_write_json(path, index)


def _read_lessons(path: Path, limit: int) -> list[dict[str, Any]]:
    lessons: list[dict[str, Any]] = []
    if not path.exists():
        return lessons
    for lesson_path in sorted(path.glob("*.json"), reverse=True)[:limit]:
        try:
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        lessons.append(
            {
                "lesson_id": lesson.get("lesson_id", ""),
                "failure_type": lesson.get("failure_type", ""),
                "root_cause": lesson.get("root_cause", ""),
                "next_action": lesson.get("next_action", ""),
                "promotion_status": lesson.get("promotion_status", ""),
            }
        )
    return lessons


def _count_json_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob("*.json"))
