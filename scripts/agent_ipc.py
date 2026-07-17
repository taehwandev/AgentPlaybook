"""Content-free local IPC/event channel shared by AgentPlaybook layers."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json, read_json_object


SCHEMA_VERSION = 1
EVENTS_FILENAME = "events.json"
MAX_EVENTS = 500
SAFE_ENUM = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


def events_path(project: Path) -> Path:
    return project.resolve() / ".agentplaybook" / EVENTS_FILENAME


def emit_event(
    project: Path,
    event_type: str,
    *,
    run_id: str | None = None,
    task_id: str | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    for label, value in (("event_type", event_type), ("state", state)):
        if value is not None and not SAFE_ENUM.fullmatch(value):
            raise ValueError(f"{label} must be a safe enum")
    event = {
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "run_id": run_id,
        "task_id": task_id,
        "state": state,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path = events_path(project)
    payload = read_json_object(path)
    events = payload.get("events") if payload.get("schema_version") == SCHEMA_VERSION else []
    if not isinstance(events, list):
        events = []
    events.append(event)
    atomic_write_json(path, {"schema_version": SCHEMA_VERSION, "events": events[-MAX_EVENTS:]})
    return event


def read_events(project: Path, *, event_type: str | None = None) -> list[dict[str, Any]]:
    payload = read_json_object(events_path(project))
    events = payload.get("events") if payload.get("schema_version") == SCHEMA_VERSION else []
    if not isinstance(events, list):
        return []
    if event_type is None:
        return [event for event in events if isinstance(event, dict)]
    return [event for event in events if isinstance(event, dict) and event.get("event_type") == event_type]


def summarize_events(project: Path) -> dict[str, int]:
    summary: dict[str, int] = {}
    for event in read_events(project):
        event_type = str(event.get("event_type") or "unknown")
        summary[event_type] = summary.get(event_type, 0) + 1
    return summary

