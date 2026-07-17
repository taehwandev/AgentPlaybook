"""Content-free queue and capacity primitives for the AgentPlaybook scheduler."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json, read_json_object
from agent_ipc import emit_event
from agent_state_lock import state_lock


SCHEMA_VERSION = 1
SCHEDULER_FILENAME = "scheduler.json"
TASK_STATES = frozenset({"queued", "running", "completed", "failed", "cancelled"})
MAX_TASKS = 200


def scheduler_path(project: Path) -> Path:
    return project.resolve() / ".agentplaybook" / SCHEDULER_FILENAME


def choose_capacity(independent_slices: int, requested_workers: int = 1) -> int:
    """Choose a bounded worker capacity; small or dependent work stays serial."""

    if independent_slices < 2:
        return 1
    return max(2, min(3, requested_workers))


def enqueue_task(
    project: Path,
    run_id: str,
    *,
    priority: int = 0,
    independent_slices: int = 1,
    max_retries: int = 0,
) -> dict[str, Any]:
    if not run_id or not isinstance(run_id, str):
        raise ValueError("run_id is required")
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "task_id": uuid.uuid4().hex,
        "run_id": run_id,
        "project_id": _opaque_project_id(project),
        "priority": int(priority),
        "independent_slices": max(0, int(independent_slices)),
        "attempt": 1,
        "max_attempts": max(1, int(max_retries) + 1),
        "state": "queued",
        "queued_at": now,
        "updated_at": now,
    }
    path = scheduler_path(project)
    with state_lock(path):
        payload = _read_scheduler(path)
        payload["tasks"].append(task)
        payload["tasks"] = payload["tasks"][-MAX_TASKS:]
        _write_scheduler(path, payload)
    _safe_event(project, "task.queued", run_id=run_id, task_id=task["task_id"], state="queued")
    return task


def claim_next(project: Path, *, capacity: int = 1) -> dict[str, Any] | None:
    """Claim the highest-priority queued task when capacity is available."""

    if capacity < 1:
        raise ValueError("capacity must be positive")
    path = scheduler_path(project)
    with state_lock(path):
        payload = _read_scheduler(path)
        running = [task for task in payload["tasks"] if task.get("state") == "running"]
        if len(running) >= capacity:
            return None
        queued = [task for task in payload["tasks"] if task.get("state") == "queued"]
        if not queued:
            return None
        target = max(queued, key=lambda task: (int(task.get("priority", 0)), task.get("queued_at", "")))
        target["state"] = "running"
        target["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_scheduler(path, payload)
    _safe_event(project, "task.claimed", run_id=str(target["run_id"]), task_id=str(target["task_id"]), state="running")
    return target


def claim_task(project: Path, task_id: str, *, capacity: int = 1) -> dict[str, Any] | None:
    """Claim one specific queued task without allowing another task to win the race."""

    if capacity < 1:
        raise ValueError("capacity must be positive")
    path = scheduler_path(project)
    with state_lock(path):
        payload = _read_scheduler(path)
        running = [task for task in payload["tasks"] if task.get("state") == "running"]
        if len(running) >= capacity:
            return None
        for task in payload["tasks"]:
            if task.get("task_id") != task_id or task.get("state") != "queued":
                continue
            task["state"] = "running"
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_scheduler(path, payload)
            break
        else:
            return None
    _safe_event(project, "task.claimed", run_id=str(task["run_id"]), task_id=task_id, state="running")
    return task


def transition_task(project: Path, task_id: str, state: str) -> dict[str, Any] | None:
    if state not in TASK_STATES:
        raise ValueError(f"unsupported task state: {state}")
    path = scheduler_path(project)
    with state_lock(path):
        payload = _read_scheduler(path)
        for task in payload["tasks"]:
            if task.get("task_id") == task_id:
                task["state"] = state
                task["updated_at"] = datetime.now(timezone.utc).isoformat()
                _write_scheduler(path, payload)
                break
        else:
            return None
    _safe_event(project, "task.transitioned", run_id=str(task["run_id"]), task_id=task_id, state=state)
    return task


def retry_task(project: Path, task_id: str) -> dict[str, Any] | None:
    """Requeue a failed task only while its bounded retry budget remains."""

    path = scheduler_path(project)
    with state_lock(path):
        payload = _read_scheduler(path)
        for task in payload["tasks"]:
            if task.get("task_id") != task_id or task.get("state") != "failed":
                continue
            if int(task.get("attempt", 1)) >= int(task.get("max_attempts", 1)):
                return None
            task["attempt"] = int(task.get("attempt", 1)) + 1
            task["state"] = "queued"
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_scheduler(path, payload)
            break
        else:
            return None
    _safe_event(project, "task.requeued", run_id=str(task["run_id"]), task_id=task_id, state="queued")
    return task


def _read_scheduler(path: Path) -> dict[str, Any]:
    payload = read_json_object(path)
    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("tasks"), list):
        return {"schema_version": SCHEMA_VERSION, "tasks": []}
    return payload


def _write_scheduler(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def _opaque_project_id(project: Path) -> str:
    return hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()


def _safe_event(project: Path, event_type: str, *, run_id: str, task_id: str, state: str) -> None:
    try:
        emit_event(project, event_type, run_id=run_id, task_id=task_id, state=state)
    except (OSError, ValueError):
        return
