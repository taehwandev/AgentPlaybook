"""Build safe Codex subtask handoffs from workflow execution profiles."""

from __future__ import annotations

import subprocess
from pathlib import Path
from shlex import join
from typing import Callable, Mapping

from workflow_dispatch_profiles import (
    ORCHESTRATOR_PROFILE,
    WORK_KINDS,
    profile_for_work_kind,
    select_work_kind,
)
from workflow_request import classify_request, route_block_reason


def build_dispatch_manifest(
    command: str,
    request: str,
    project: Path,
    *,
    work_kind: str = "auto",
    complexity_evidence: str = "",
    route: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Create an inspectable Codex handoff for one bounded task stage."""
    classification = classify_request(request)
    block_reason = route_block_reason(command, classification)
    if block_reason:
        raise ValueError(block_reason)

    selected_kind, selection_reason = select_work_kind(
        command,
        classification,
        work_kind,
        complexity_evidence,
    )
    profile = profile_for_work_kind(selected_kind)
    non_authoring = selected_kind == "repetitive"
    sandbox_mode = "read-only" if non_authoring else "workspace-write"
    project = project.expanduser().resolve()
    evidence_directory = project / ".agentplaybook"
    handoff_state = {
        "route_command": command,
        "required_docs": list(route.get("required_docs", [])) if route else [],
        "gates": list(route.get("gates", [])) if route else [],
        "evidence_directory": str(evidence_directory),
        "preflight_evidence": str(evidence_directory / "preflight.json"),
        "docs_read_receipt": str(evidence_directory / "route-docs-read.json"),
        "gate_ledger": str(evidence_directory / "gate-evidence.json"),
        "verification_plan": "run the nearest verification required by the parent route",
    }
    handoff_prompt = build_handoff_prompt(
        command,
        request,
        selected_kind,
        handoff_state,
        non_authoring=non_authoring,
    )
    codex_argv = [
        "codex",
        "exec",
        "--model",
        profile["codex_model"],
        "--config",
        f'model_reasoning_effort="{profile["reasoning_effort"]}"',
        "--sandbox",
        sandbox_mode,
        "--cd",
        str(project),
        handoff_prompt,
    ]

    return {
        "schema_version": 1,
        "project": str(project),
        "command": command,
        "request_classification": classification,
        "orchestrator_profile": ORCHESTRATOR_PROFILE,
        "work_profile": profile,
        "authoring_policy": "read-only non-authoring" if non_authoring else "code authoring allowed",
        "sandbox_mode": sandbox_mode,
        "selection_reason": selection_reason,
        "handoff_state": handoff_state,
        "codex_exec_argv": codex_argv,
        "codex_exec_command": join(codex_argv),
        "execution_policy": (
            "The manifest is inspectable by default. The orchestrator runs the generated command "
            "with dispatch --execute only at a task or subagent boundary."
        ),
    }


def build_handoff_prompt(
    command: str,
    request: str,
    work_kind: str,
    handoff_state: Mapping[str, object],
    *,
    non_authoring: bool,
) -> str:
    required_docs = ", ".join(str(doc) for doc in handoff_state["required_docs"])
    gates = ", ".join(str(gate) for gate in handoff_state["gates"])
    instructions = [
        "You are a delegated Codex worker for one bounded task stage.",
        "Do not delegate another Codex child from this worker.",
        "Read the target repository instructions before changing files and preserve existing user changes.",
    ]
    if non_authoring:
        instructions.append(
            "This is a read-only non-authoring stage. Do not modify files, write code, generate patches, or create tests."
        )
    instructions.extend(
        [
            f"Workflow command: {command}",
            f"Work kind: {work_kind}",
            f"Required docs from the parent route: {required_docs or 'resolve from the route'}",
            f"Parent route gates: {gates or 'resolve from the route'}",
            f"Parent preflight evidence: {handoff_state['preflight_evidence']}",
            f"Parent docs-read receipt: {handoff_state['docs_read_receipt']}",
            f"Parent gate ledger: {handoff_state['gate_ledger']}",
            f"Verification plan: {handoff_state['verification_plan']}",
            "Read existing parent evidence when present. Do not overwrite parent receipts or gate ledger entries.",
            "User request:",
            request,
        ]
    )
    return "\n".join(instructions)


def execute_dispatch_manifest(
    manifest: Mapping[str, object],
    *,
    runner: Callable[[list[str]], int] | None = None,
) -> int:
    """Run a previously selected worker profile at the explicit handoff boundary."""
    argv = manifest.get("codex_exec_argv")
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        raise ValueError("Dispatch manifest is missing a valid codex_exec_argv")

    if runner:
        return runner(argv)
    try:
        completed = subprocess.run(argv, check=False)
    except OSError as error:
        raise RuntimeError("Unable to start the delegated Codex worker") from error
    return completed.returncode


def print_dispatch_manifest(manifest: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        import json

        print(json.dumps(manifest, indent=2, sort_keys=True))
        return

    profile = manifest["work_profile"]
    assert isinstance(profile, Mapping)
    print("# AgentPlaybook Codex Handoff")
    print()
    print(f"- Work kind: `{profile['work_kind']}`")
    print(f"- Model tier: `{profile['model_tier']}`")
    print(f"- Codex model: `{profile['codex_model']}`")
    print(f"- Reasoning effort: `{profile['reasoning_effort']}`")
    print(f"- Authoring policy: `{manifest['authoring_policy']}`")
    print(f"- Selection: {manifest['selection_reason']}")
    print()
    print("## Handoff Command")
    print(f"`{manifest['codex_exec_command']}`")
    print()
    print(manifest["execution_policy"])
