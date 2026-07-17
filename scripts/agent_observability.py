"""Read-only content-free status API for the AgentPlaybook OS layers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from agent_ipc import summarize_events
from agent_run_registry import active_runs, registry_path
from agent_scheduler import scheduler_path
from agent_execution_capsule_state import read_json_object
from agent_state_lock import state_lock


def status_snapshot(project: Path) -> dict[str, Any]:
    with state_lock(scheduler_path(project)):
        scheduler = read_json_object(scheduler_path(project))
    tasks = scheduler.get("tasks") if isinstance(scheduler.get("tasks"), list) else []
    task_counts: dict[str, int] = {}
    for task in tasks:
        state = str(task.get("state") or "unknown")
        task_counts[state] = task_counts.get(state, 0) + 1
    return {
        "api_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_runs": len(active_runs(project)),
        "task_counts": task_counts,
        "events": summarize_events(project),
        "registry_present": registry_path(project).exists(),
        "scheduler_present": scheduler_path(project).exists(),
    }
