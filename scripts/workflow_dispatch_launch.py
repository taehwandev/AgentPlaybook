"""Launch-time validation and inspect-only rendering for Codex dispatch."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Callable, Mapping

from agent_gate_evidence import gate_evidence_path_for_preflight
from agent_run_registry import latest_run_id
from agent_scheduler import claim_next, choose_capacity, enqueue_task, transition_task
from agent_worker_evidence import create_worker_reservation, worker_reservation_matches
from workflow_dispatch_handoff import execution_policy


def execute_dispatch_manifest(
    manifest: Mapping[str, object],
    *,
    runner: Callable[[list[str]], int] | None,
    execution_capsule_state: Callable[..., dict[str, object]],
    isolated_worker_evidence: Callable[..., Path],
    codex_argv: Callable[[Path, Mapping[str, object], str, str], list[str]],
    build_handoff_prompt: Callable[..., str],
) -> int:
    if manifest.get("execution_mode") == "inline":
        raise ValueError(
            "Inline dispatch is a decision only and cannot execute work in the parent process; "
            "omit --execute or require isolation."
        )
    handoff = manifest.get("handoff_state")
    profile = manifest.get("work_profile")
    if not isinstance(handoff, Mapping) or not isinstance(profile, Mapping):
        raise ValueError("Dispatch manifest is missing handoff state or work profile")
    prepared = prepare_launch_handoff(
        manifest,
        handoff,
        execution_capsule_state=execution_capsule_state,
        isolated_worker_evidence=isolated_worker_evidence,
    )
    prompt = build_handoff_prompt(
        str(manifest["command"]),
        str(manifest.get("request", "")),
        str(manifest["work_kind"]),
        prepared,
        non_authoring=str(manifest.get("authoring_policy", "")).startswith("read-only"),
    )
    argv = codex_argv(
        Path(str(manifest["project"])), profile, str(manifest["sandbox_mode"]), prompt
    )
    project = Path(str(manifest["project"])).resolve()
    scheduler_task = _claim_scheduler_task(manifest, prepared, project)
    if runner:
        return _run_scheduled_worker(argv, runner, project, scheduler_task)
    try:
        completed = subprocess.run(argv, check=False, env=worker_environment(prepared))
    except OSError as error:
        transition_task(project, str(scheduler_task["task_id"]), "failed")
        raise RuntimeError("Unable to start the delegated Codex worker") from error
    transition_task(
        project,
        str(scheduler_task["task_id"]),
        "completed" if completed.returncode == 0 else "failed",
    )
    return completed.returncode


def _claim_scheduler_task(
    manifest: Mapping[str, object], prepared: Mapping[str, object], project: Path
) -> dict[str, object]:
    parent_evidence = Path(str(prepared["preflight_evidence"])).resolve()
    run_id = latest_run_id(project, parent_evidence) or uuid.uuid4().hex
    independent_slices = int(manifest.get("independent_slices") or 1)
    capacity = choose_capacity(independent_slices, int(manifest.get("requested_workers") or 1))
    task = enqueue_task(
        project,
        run_id,
        priority=int(manifest.get("priority") or 0),
        independent_slices=independent_slices,
    )
    claimed = claim_next(project, capacity=capacity)
    if not claimed or claimed.get("task_id") != task.get("task_id"):
        raise RuntimeError("scheduler capacity is exhausted; worker remains queued")
    return task


def _run_scheduled_worker(
    argv: list[str], runner: Callable[[list[str]], int], project: Path, task: Mapping[str, object]
) -> int:
    try:
        result = runner(argv)
    except BaseException:
        transition_task(project, str(task["task_id"]), "failed")
        raise
    transition_task(project, str(task["task_id"]), "completed" if result == 0 else "failed")
    return result


def prepare_launch_handoff(
    manifest: Mapping[str, object],
    handoff: Mapping[str, object],
    *,
    execution_capsule_state: Callable[..., dict[str, object]],
    isolated_worker_evidence: Callable[..., Path],
) -> dict[str, object]:
    prepared = dict(handoff)
    project = Path(str(manifest["project"])).resolve()
    rules = Path(str(prepared["rules"])).resolve()
    parent_evidence = Path(str(prepared["preflight_evidence"])).resolve()
    route = prepared.get("route_manifest")
    if not isinstance(route, Mapping):
        raise ValueError("Dispatch manifest is missing the parent route manifest")
    prepared["execution_capsule"] = execution_capsule_state(
        project,
        rules,
        parent_evidence,
        route,
        parent_context_reusable=prepared.get("parent_context_reusable") is True,
    )
    capsule = prepared["execution_capsule"]
    if isinstance(capsule, Mapping) and capsule.get("reusable"):
        return prepared
    worker_evidence = Path(str(prepared["worker_preflight_evidence"])).resolve()
    token = prepared.get("worker_reservation_token")
    if prepared.get("worker_evidence_reserved"):
        if not token or not worker_reservation_matches(worker_evidence.parent, str(token)):
            raise ValueError("Fallback worker reservation token does not match the reserved evidence path.")
    else:
        worker_evidence = isolated_worker_evidence(
            project, parent_evidence, worker_evidence, reserve=True
        )
        token = create_worker_reservation(worker_evidence.parent)
    prepared["worker_preflight_evidence"] = str(worker_evidence)
    prepared["worker_gate_ledger"] = str(gate_evidence_path_for_preflight(worker_evidence))
    prepared["worker_evidence_reserved"] = True
    prepared["worker_reservation_token"] = token
    return prepared


def worker_environment(handoff: Mapping[str, object]) -> dict[str, str]:
    environment = dict(os.environ)
    capsule = handoff.get("execution_capsule")
    if isinstance(capsule, Mapping) and capsule.get("reusable"):
        environment["AGENTPLAYBOOK_PARENT_EVIDENCE_READONLY"] = "1"
        return environment
    environment["AGENTPLAYBOOK_WORKER_EVIDENCE"] = str(handoff["worker_preflight_evidence"])
    environment["AGENTPLAYBOOK_WORKER_RESERVATION_TOKEN"] = str(
        handoff["worker_reservation_token"]
    )
    return environment


def print_dispatch_manifest(manifest: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        output = dict(manifest)
        output["codex_exec_argv"] = []
        output["codex_exec_command"] = ""
        output["execution_policy"] = execution_policy(str(manifest.get("execution_mode")))
        print(json.dumps(output, indent=2, sort_keys=True))
        return
    profile = manifest["work_profile"]
    assert isinstance(profile, Mapping)
    capsule = manifest["handoff_state"]["execution_capsule"]
    assert isinstance(capsule, Mapping)
    print("# AgentPlaybook Codex Handoff\n")
    print(f"- Work kind: `{profile['work_kind']}`")
    print(f"- Codex model: `{profile['codex_model']}`")
    print(f"- Reasoning effort: `{profile['reasoning_effort']}`")
    print(f"- Authoring policy: `{manifest['authoring_policy']}`")
    print(f"- Execution mode: `{manifest['execution_mode']}`")
    print(f"- Execution capsule reusable: `{str(bool(capsule['reusable'])).lower()}`")
    print(f"- Selection: {manifest['selection_reason']}\n")
    print("## Execution Boundary")
    print(execution_policy(str(manifest.get("execution_mode"))))
