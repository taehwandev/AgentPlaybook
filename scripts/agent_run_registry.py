"""Content-free local registry for AgentPlaybook run lifecycle state."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json, read_json_object
from agent_route_state import request_fingerprint, route_fingerprint
from agent_ipc import emit_event


SCHEMA_VERSION = 1
REGISTRY_FILENAME = "run-registry.json"
RUN_STATES = frozenset({"running", "paused", "failed", "completed", "cancelled"})
MAX_RUNS = 100


def registry_path(project: Path) -> Path:
    return project.resolve() / ".agentplaybook" / REGISTRY_FILENAME


def register_run(
    project: Path,
    evidence_path: Path,
    route: dict[str, Any],
    request_intake: dict[str, Any] | None,
) -> dict[str, Any]:
    """Register a new run without persisting request text or local paths."""

    now = datetime.now(timezone.utc).isoformat()
    run = {
        "run_id": uuid.uuid4().hex,
        "project_id": _opaque_project_id(project),
        "evidence_name": evidence_path.name,
        "command": str(route.get("command") or "task"),
        "route_fingerprint": route_fingerprint(route),
        "request_fingerprint": request_fingerprint(request_intake),
        "state": "running",
        "started_at": now,
        "updated_at": now,
    }
    payload = _read_registry(registry_path(project))
    payload["runs"].append(run)
    payload["runs"] = payload["runs"][-MAX_RUNS:]
    _write_registry(registry_path(project), payload)
    _safe_event(project, "run.started", run_id=run["run_id"], state="running")
    return run


def transition_run(
    project: Path,
    evidence_path: Path,
    state: str,
) -> dict[str, Any] | None:
    """Transition the newest run bound to an evidence file."""

    if state not in RUN_STATES:
        raise ValueError(f"unsupported run state: {state}")
    path = registry_path(project)
    payload = _read_registry(path)
    candidates = [
        run for run in payload["runs"] if run.get("evidence_name") == evidence_path.name
    ]
    if not candidates:
        return None
    target = candidates[-1]
    target["state"] = state
    target["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_registry(path, payload)
    _safe_event(project, "run.transitioned", run_id=target["run_id"], state=state)
    return target


def active_runs(project: Path) -> list[dict[str, Any]]:
    payload = _read_registry(registry_path(project))
    return [run for run in payload["runs"] if run.get("state") in {"running", "paused"}]


def latest_run_id(project: Path, evidence_path: Path) -> str | None:
    payload = _read_registry(registry_path(project))
    matches = [run for run in payload["runs"] if run.get("evidence_name") == evidence_path.name]
    return str(matches[-1]["run_id"]) if matches and matches[-1].get("run_id") else None


def recover_stale_runs(project: Path, *, stale_after_seconds: int = 3600) -> list[dict[str, Any]]:
    """Fail stale active runs so a later scheduler invocation can recover them."""

    if stale_after_seconds < 1:
        raise ValueError("stale_after_seconds must be positive")
    path = registry_path(project)
    payload = _read_registry(path)
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_after_seconds)
    recovered: list[dict[str, Any]] = []
    for run in payload["runs"]:
        if run.get("state") not in {"running", "paused"}:
            continue
        try:
            updated = datetime.fromisoformat(str(run["updated_at"]))
        except (KeyError, TypeError, ValueError):
            continue
        if updated < cutoff:
            run["state"] = "failed"
            run["updated_at"] = datetime.now(timezone.utc).isoformat()
            recovered.append(run)
            _safe_event(project, "run.recovered", run_id=str(run["run_id"]), state="failed")
    if recovered:
        _write_registry(path, payload)
    return recovered


def resume_run(project: Path, run_id: str) -> dict[str, Any] | None:
    path = registry_path(project)
    payload = _read_registry(path)
    for run in payload["runs"]:
        if run.get("run_id") == run_id and run.get("state") in {"failed", "paused"}:
            run["state"] = "running"
            run["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_registry(path, payload)
            _safe_event(project, "run.resumed", run_id=run_id, state="running")
            return run
    return None


def _read_registry(path: Path) -> dict[str, Any]:
    payload = read_json_object(path)
    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("runs"), list):
        return {"schema_version": SCHEMA_VERSION, "runs": []}
    return payload


def _write_registry(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def _opaque_project_id(project: Path) -> str:
    return hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()


def _safe_event(project: Path, event_type: str, *, run_id: str, state: str) -> None:
    try:
        emit_event(project, event_type, run_id=run_id, state=state)
    except (OSError, ValueError):
        return
