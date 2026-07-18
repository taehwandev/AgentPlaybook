"""Best-effort adapters for successful-task skill learning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_global_lessons import state_home
from agent_skill_learning import (
    curate_observations,
    record_observation,
    review_candidate,
)
from agent_skill_maintenance import complete_verified_skill_maintenance
from agent_skill_retention import prune_skill_learning_state


def record_skill_feedback(
    *,
    evidence_path: Path,
    outcome: str,
    skill_id: str,
    signal: str,
) -> tuple[dict[str, Any], list[str]]:
    """Record an observation, never an agent-approved patch candidate."""

    normalized_outcome = outcome.strip().lower()
    if normalized_outcome == "no_change":
        return {"created": False, "reason": "no_change"}, [
            "skill observation check completed with no reusable signal"
        ]
    if normalized_outcome != "observed":
        return {"created": False, "reason": "invalid_observation_outcome"}, [
            "skill observation skipped: invalid outcome; task completion is unchanged"
        ]

    result = record_observation(
        state_home(),
        occurrence_id=_occurrence_id(evidence_path),
        skill_id=skill_id,
        signal=signal,
    )
    if result.get("idempotent"):
        return result, [
            "successful-task skill observation replay was deduplicated",
            "task completion is unchanged",
        ]
    if not result.get("created"):
        reason = str(result.get("reason") or "not_recorded")
        return result, [f"skill observation skipped: {reason}; task completion is unchanged"]

    details = [
        "successful-task skill observation recorded",
        f"observation status: {result.get('status', 'observed')}",
    ]
    return result, details


def record_skill_curation() -> tuple[dict[str, Any], list[str]]:
    try:
        result = curate_observations(state_home())
        result["retention"] = prune_skill_learning_state(state_home())
    except (OSError, ValueError) as error:
        return {"updated": False, "reason": "curation_failed", "error": error.__class__.__name__}, [
            "skill curation skipped; completed tasks and runtime maintenance are unchanged"
        ]
    details = [
        f"skill observations scanned: {result['scanned']}",
        f"new review items queued: {result['ready_count']}",
    ]
    return result, details


def record_skill_review(
    *,
    candidate_id: str,
    decision: str,
    gap_type: str,
    change_type: str,
    promotion_target: str,
) -> tuple[dict[str, Any], list[str]]:
    try:
        result = review_candidate(
            state_home(),
            candidate_id=candidate_id,
            decision=decision,
            gap_type=gap_type,
            change_type=change_type,
            promotion_target=promotion_target,
        )
    except (OSError, ValueError) as error:
        result = {"updated": False, "reason": "review_failed", "error": error.__class__.__name__}
    if not result.get("updated"):
        reason = str(result.get("reason") or "not_updated")
        return result, [f"bounded skill review skipped: {reason}; completed tasks are unchanged"]
    return result, [
        f"bounded skill review recorded: {result['status']}",
        "canonical skill guidance was not edited by the review recorder",
    ]


def record_skill_maintenance(
    *,
    project: Path,
    rules: Path,
    candidate_id: str,
    outcome: str,
    verification_kind: str,
    target: str,
    test_selector: str,
) -> tuple[dict[str, Any], list[str]]:
    try:
        result = complete_verified_skill_maintenance(
            state_home(),
            project=project,
            rules=rules,
            candidate_id=candidate_id,
            outcome=outcome,
            verification_kind=verification_kind,
            target=target,
            test_selector=test_selector,
        )
    except (OSError, ValueError) as error:
        result = {"updated": False, "reason": "maintenance_failed", "error": error.__class__.__name__}
    if not result.get("updated"):
        reason = str(result.get("reason") or "not_updated")
        return result, [f"skill maintenance status skipped: {reason}"]
    return result, [f"skill maintenance completed: {result['status']}"]


def _occurrence_id(evidence_path: Path) -> str:
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(payload.get("agent_run_id") or "")
