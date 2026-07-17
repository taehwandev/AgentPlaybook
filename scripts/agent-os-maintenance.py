#!/usr/bin/env python3
"""Run bounded AgentPlaybook OS recovery and retention maintenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_retention import prune_runtime_state
from agent_run_registry import recover_stale_runs
from agent_scheduler import recover_stale_tasks, retry_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain AgentPlaybook OS runtime state")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--stale-after-seconds", type=int, default=3600)
    parser.add_argument("--retention-seconds", type=int, default=30 * 24 * 60 * 60)
    parser.add_argument("--max-records", type=int, default=100)
    args = parser.parse_args()
    recovered = recover_stale_runs(args.project, stale_after_seconds=args.stale_after_seconds)
    recovered_tasks = recover_stale_tasks(args.project, stale_after_seconds=args.stale_after_seconds)
    requeued_tasks = [
        retry_task(args.project, str(task["task_id"]))
        for task in recovered_tasks
    ]
    requeued_count = sum(task is not None for task in requeued_tasks)
    pruned = prune_runtime_state(
        args.project,
        retention_seconds=args.retention_seconds,
        max_records=args.max_records,
    )
    print(json.dumps({
        "recovered_runs": len(recovered),
        "recovered_tasks": len(recovered_tasks),
        "requeued_tasks": requeued_count,
        "pruned": pruned,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
