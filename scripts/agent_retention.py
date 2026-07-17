"""Bounded local retention policy for AgentPlaybook runtime state."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json, read_json_object
from agent_ipc import events_path
from agent_run_registry import registry_path
from agent_scheduler import scheduler_path
from agent_state_lock import state_lock


TERMINAL_STATES = {"completed", "failed", "cancelled"}


def prune_runtime_state(
    project: Path,
    *,
    retention_seconds: int = 30 * 24 * 60 * 60,
    max_records: int = 100,
) -> dict[str, int]:
    if retention_seconds < 1 or max_records < 1:
        raise ValueError("retention_seconds and max_records must be positive")
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=retention_seconds)
    return {
        "runs": _prune_file(registry_path(project), "runs", cutoff, max_records),
        "tasks": _prune_file(scheduler_path(project), "tasks", cutoff, max_records),
        "events": _prune_file(events_path(project), "events", cutoff, max_records),
    }


def _prune_file(path: Path, key: str, cutoff: datetime, max_records: int) -> int:
    with state_lock(path):
        payload = read_json_object(path)
        records = payload.get(key)
        if not isinstance(records, list):
            return 0
        kept: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            if key == "events":
                terminal = True
                timestamp = record.get("created_at")
            else:
                terminal = record.get("state") in TERMINAL_STATES
                timestamp = record.get("updated_at") or record.get("queued_at")
            try:
                old = datetime.fromisoformat(str(timestamp))
            except (TypeError, ValueError):
                old = datetime.now(timezone.utc)
            if not terminal or old >= cutoff:
                kept.append(record)
        kept = kept[-max_records:]
        removed = len(records) - len(kept)
        if removed:
            payload[key] = kept
            atomic_write_json(path, payload)
        return removed
