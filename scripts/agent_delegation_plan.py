"""Structured evidence for delegated or parallel agent work."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DELEGATION_PLAN_FILENAME = "agent-delegation-plan.json"
MULTI_AGENT_ROUTE_GATES = {
    "roles",
    "write scopes",
    "agent briefs",
    "integration review",
}
PARALLEL_SIGNALS = (
    "multi-agent",
    "subagent",
    "sub-agent",
    "parallel",
    "split",
    "worker",
)
SERIAL_SIGNALS = (
    "serial",
    "single-agent",
    "single agent",
    "no subagent",
    "no sub-agent",
    "no parallel",
)


def delegation_plan_path(project: Path) -> Path:
    return project / ".agentplaybook" / DELEGATION_PLAN_FILENAME


def read_delegation_plan(project: Path) -> dict[str, Any]:
    path = delegation_plan_path(project)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"invalid_json": True, "path": str(path)}
    if isinstance(payload, dict):
        payload.setdefault("path", str(path))
        return payload
    return {"invalid_json": True, "path": str(path)}


def evidence_requires_delegation_plan(
    required_gates: list[str],
    gate_evidence: dict[str, str],
) -> bool:
    if MULTI_AGENT_ROUTE_GATES.intersection(required_gates):
        return True
    text = gate_evidence.get("multi-agent split decision", "").lower()
    parallel = any(signal in text for signal in PARALLEL_SIGNALS)
    serial = any(signal in text for signal in SERIAL_SIGNALS)
    return parallel and not serial


def validate_delegation_plan_evidence(
    required_gates: list[str],
    gate_evidence: dict[str, str],
    plan: dict[str, Any],
) -> list[str]:
    if not evidence_requires_delegation_plan(required_gates, gate_evidence):
        return []
    return validate_delegation_plan_structure(plan)


def validate_delegation_plan_structure(plan: dict[str, Any]) -> list[str]:
    """Return every recoverable delegation-plan schema failure in one pass."""

    if not plan:
        return [
            "parallel or multi-agent evidence requires structured "
            ".agentplaybook/agent-delegation-plan.json"
        ]
    if plan.get("invalid_json"):
        return ["agent delegation plan is not valid JSON"]

    failures: list[str] = []
    if plan.get("schema_version") != 1:
        failures.append("agent delegation plan has an unsupported schema_version")
    if plan.get("mode") != "parallel":
        failures.append(
            "agent delegation plan mode must be parallel for delegated or multi-agent work"
        )

    workers = plan.get("workers")
    if not isinstance(workers, list) or not workers:
        failures.append("agent delegation plan must include at least one worker")
    else:
        worker_ids: set[str] = set()
        owned_scopes: list[tuple[int, str]] = []
        for index, worker in enumerate(workers, start=1):
            if not isinstance(worker, dict):
                failures.append(f"agent delegation plan worker {index} must be an object")
                continue
            _require_text(worker, "id", f"worker {index}", failures)
            _require_text(worker, "role", f"worker {index}", failures)
            _require_string_list(worker, "owned_scope", f"worker {index}", failures)
            _require_string_list(worker, "forbidden_scope", f"worker {index}", failures)
            _require_contract(worker, f"worker {index}", failures)
            _require_string_list(worker, "acceptance", f"worker {index}", failures)
            _require_string_list(worker, "verification", f"worker {index}", failures)
            worker_id = worker.get("id")
            if isinstance(worker_id, str) and worker_id.strip():
                normalized_id = worker_id.strip()
                if normalized_id in worker_ids:
                    failures.append(f"agent delegation plan worker {index} duplicates id {normalized_id}")
                worker_ids.add(normalized_id)
            worker_scopes = worker.get("owned_scope")
            if isinstance(worker_scopes, list):
                owned_scopes.extend(
                    (index, scope.strip())
                    for scope in worker_scopes
                    if isinstance(scope, str) and scope.strip()
                )
        failures.extend(_owned_scope_overlap_failures(owned_scopes))

    integration = plan.get("integration_review")
    if not isinstance(integration, dict):
        failures.append("agent delegation plan must include integration_review")
    else:
        _require_any_text(integration, ("owner", "integration_owner"), "integration_review", failures)
        _require_text(integration, "contract_drift_check", "integration_review", failures)
        _require_string_list(integration, "final_verification", "integration_review", failures)

    return failures


def _owned_scope_overlap_failures(owned_scopes: list[tuple[int, str]]) -> list[str]:
    failures: list[str] = []
    for left_index, (left_worker, left_scope) in enumerate(owned_scopes):
        for right_worker, right_scope in owned_scopes[left_index + 1 :]:
            if left_worker == right_worker or not _scopes_overlap(left_scope, right_scope):
                continue
            failures.append(
                "agent delegation plan workers "
                f"{left_worker} and {right_worker} have overlapping owned_scope: "
                f"{left_scope} <> {right_scope}"
            )
    return failures


def _scopes_overlap(left: str, right: str) -> bool:
    left_scope = left.strip().rstrip("/")
    right_scope = right.strip().rstrip("/")
    if left_scope == right_scope:
        return True
    if not left_scope or not right_scope:
        return False
    if any(character in left_scope + right_scope for character in "*?[]"):
        return False
    if any(character.isspace() for character in left_scope + right_scope):
        return False
    return left_scope.startswith(f"{right_scope}/") or right_scope.startswith(f"{left_scope}/")


def _require_text(payload: dict[str, Any], key: str, label: str, failures: list[str]) -> None:
    if not isinstance(payload.get(key), str) or not payload[key].strip():
        failures.append(f"agent delegation plan {label} missing non-empty {key}")


def _require_any_text(
    payload: dict[str, Any],
    keys: tuple[str, ...],
    label: str,
    failures: list[str],
) -> None:
    if any(isinstance(payload.get(key), str) and payload[key].strip() for key in keys):
        return
    failures.append(f"agent delegation plan {label} missing non-empty {'/'.join(keys)}")


def _require_string_list(payload: dict[str, Any], key: str, label: str, failures: list[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        failures.append(f"agent delegation plan {label} missing non-empty {key} list")


def _require_contract(payload: dict[str, Any], label: str, failures: list[str]) -> None:
    value = payload.get("contract")
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, dict) and value:
        return
    failures.append(f"agent delegation plan {label} missing contract")
