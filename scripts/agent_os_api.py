"""Provider-neutral API and runtime-adapter contracts for AgentPlaybook OS."""

from __future__ import annotations

import re
from typing import Any, Mapping


CONTRACT_VERSION = 1
RUNTIME_ADAPTER_VERSION = 1
SAFE_RUNTIME = re.compile(r"^[a-z][a-z0-9_.-]{0,31}$")


def api_contract_manifest() -> dict[str, int]:
    """Return the schema versions shared by status, task, capsule, and events."""

    return {
        "contract_version": CONTRACT_VERSION,
        "status_api_version": 2,
        "task_schema_version": 1,
        "capsule_schema_version": 3,
        "evidence_schema_version": 1,
        "event_schema_version": 1,
    }


def runtime_adapter_contract(
    runtime: str,
    *,
    capabilities: Mapping[str, bool],
    enforcement: str,
) -> dict[str, Any]:
    """Describe a runtime without embedding provider-specific execution details."""

    return {
        "contract_version": RUNTIME_ADAPTER_VERSION,
        "runtime": runtime,
        "capabilities": {str(key): bool(value) for key, value in capabilities.items()},
        "enforcement": enforcement,
    }


def validate_runtime_adapter_contract(contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if contract.get("contract_version") != RUNTIME_ADAPTER_VERSION:
        failures.append("runtime adapter contract version is unsupported")
    runtime = contract.get("runtime")
    if not isinstance(runtime, str) or not SAFE_RUNTIME.fullmatch(runtime):
        failures.append("runtime adapter name is malformed")
    capabilities = contract.get("capabilities")
    if not isinstance(capabilities, Mapping) or not capabilities:
        failures.append("runtime adapter capabilities are missing")
    elif any(not isinstance(value, bool) for value in capabilities.values()):
        failures.append("runtime adapter capabilities must be boolean")
    if not isinstance(contract.get("enforcement"), str) or not contract["enforcement"]:
        failures.append("runtime adapter enforcement is missing")
    return failures


def validate_api_contract_manifest(manifest: Mapping[str, Any]) -> list[str]:
    expected = api_contract_manifest()
    return [
        f"{key} contract version mismatch"
        for key, value in expected.items()
        if manifest.get(key) != value
    ]
