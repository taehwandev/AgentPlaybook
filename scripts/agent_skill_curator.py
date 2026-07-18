"""Deterministic, token-free curation of structured skill observations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json
from agent_skill_state import (
    CANDIDATE_ID_RE,
    DEFAULT_REVIEW_THRESHOLD,
    SCHEMA_VERSION,
    candidate_id,
    candidate_lock_path,
    json_count,
    now,
    observation_dir,
    read_json,
    review_queue_path,
    safe_slug,
    terminal_candidate_exists,
)
from agent_state_lock import state_lock


MAX_CURATED_GROUPS = 100
MAX_REVIEW_QUEUE = 100


def curate_observations(
    root: Path,
    *,
    min_occurrences: int = DEFAULT_REVIEW_THRESHOLD,
) -> dict[str, Any]:
    with state_lock(root / "skill-learning" / "locks" / "curator.json"):
        return _curate_observations_locked(root, min_occurrences=min_occurrences)


def _curate_observations_locked(root: Path, *, min_occurrences: int) -> dict[str, Any]:
    threshold = max(DEFAULT_REVIEW_THRESHOLD, int(min_occurrences))
    groups: dict[str, list[dict[str, Any]]] = {}
    for path in sorted((root / observation_dir()).glob("*.json")):
        payload = read_json(path)
        candidate = str(payload.get("candidate_id") or "")
        skill_id = str(payload.get("skill_id") or "")
        signal = str(payload.get("signal") or "")
        occurrence_key = str(payload.get("occurrence_key") or "")
        if (
            CANDIDATE_ID_RE.fullmatch(candidate)
            and safe_slug(skill_id)
            and safe_slug(signal)
            and candidate_id(skill_id, signal) == candidate
            and CANDIDATE_ID_RE.fullmatch(occurrence_key)
        ):
            groups.setdefault(candidate, []).append(payload)

    queued: list[str] = []
    eligible_count = 0
    queue_count = json_count(root / "skill-learning" / "review-queue")
    ordered = sorted(
        groups,
        key=lambda candidate: max(str(item.get("created_at") or "") for item in groups[candidate]),
        reverse=True,
    )
    for candidate in ordered:
        observations = groups[candidate]
        occurrence_keys = sorted({str(item["occurrence_key"]) for item in observations})
        if len(occurrence_keys) < threshold:
            continue
        eligible_count += 1
        if eligible_count > MAX_CURATED_GROUPS:
            break
        queue_path = root / review_queue_path(candidate)
        if terminal_candidate_exists(root, candidate) or queue_path.exists():
            continue
        if queue_count >= MAX_REVIEW_QUEUE:
            break
        representative = observations[0]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "candidate_id": candidate,
            "skill_id": representative["skill_id"],
            "signal": representative["signal"],
            "distinct_occurrences": len(occurrence_keys),
            "first_observed_at": min(str(item.get("created_at") or "") for item in observations),
            "last_observed_at": max(str(item.get("created_at") or "") for item in observations),
            "queued_at": now(),
            "status": "review_ready",
            "next_action": "bounded_skill_review",
            "privacy": "safe_slugs_and_opaque_ids_only",
        }
        try:
            with state_lock(root / candidate_lock_path(candidate)):
                if not queue_path.exists() and not terminal_candidate_exists(root, candidate):
                    atomic_write_json(queue_path, payload)
                    queued.append(candidate)
                    queue_count += 1
        except (OSError, ValueError):
            continue
    return {
        "scanned": sum(len(items) for items in groups.values()),
        "queued": queued,
        "ready_count": len(queued),
        "eligible_count": eligible_count,
        "threshold": threshold,
    }
