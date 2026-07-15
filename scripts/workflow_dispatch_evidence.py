"""Parent-capsule reuse and isolated worker-evidence selection for dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from agent_execution_capsule import (
    capsule_path_for_evidence,
    read_execution_capsule,
    validate_execution_capsule,
)
from agent_worker_evidence import isolated_worker_evidence


def execution_capsule_state(
    project: Path,
    rules: Path,
    evidence_path: Path,
    route: Mapping[str, object] | None,
    *,
    parent_context_reusable: bool,
) -> dict[str, object]:
    capsule_path = capsule_path_for_evidence(evidence_path)
    state: dict[str, object] = {
        "path": str(capsule_path),
        "reusable": False,
        "invalidation_reasons": [],
    }
    if not parent_context_reusable:
        state["invalidation_reasons"] = [
            "current dispatch request does not match parent start evidence"
        ]
        return state
    if route is None:
        state["invalidation_reasons"] = ["parent route manifest was not provided"]
        return state
    if not evidence_path.exists():
        state["invalidation_reasons"] = ["parent preflight evidence is missing"]
        return state

    try:
        capsule = read_execution_capsule(capsule_path)
        reasons = validate_execution_capsule(
            capsule,
            project=project,
            rules=rules,
            evidence_path=evidence_path,
            route=dict(route),
        )
    except (OSError, RuntimeError, ValueError) as error:
        capsule = None
        reasons = [f"execution capsule validation is unavailable: {error}"]
    state["reusable"] = not reasons
    state["invalidation_reasons"] = reasons
    state["phase"] = capsule.get("phase", "missing") if capsule else "missing"
    return state
