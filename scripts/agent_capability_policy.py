"""Runtime-neutral capability and sandbox policy for AgentPlaybook tasks."""

from __future__ import annotations

from typing import Any


READ_ONLY_WORK_KINDS = frozenset({"analysis", "repetitive"})
SANDBOX_MODES = frozenset({"read-only", "workspace-write", "isolated-write"})


def capability_profile(work_kind: str, *, isolation_required: bool = False) -> dict[str, Any]:
    if work_kind in READ_ONLY_WORK_KINDS:
        return {
            "work_kind": work_kind,
            "authoring_policy": "read-only non-authoring",
            "sandbox_mode": "read-only",
            "filesystem": "read-only",
            "network": "deny",
            "child_process": "deny",
        }
    return {
        "work_kind": work_kind,
        "authoring_policy": "code authoring allowed",
            # The runtime sandbox remains workspace-write for compatibility;
            # isolation is enforced by the separate filesystem capability and
            # worker evidence boundary.
            "sandbox_mode": "workspace-write",
        "filesystem": "isolated-write" if isolation_required else "workspace-write",
        "network": "runtime-policy",
        "child_process": "explicit-isolation-only",
    }


def validate_capability_profile(profile: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if profile.get("sandbox_mode") not in SANDBOX_MODES:
        failures.append("sandbox_mode must be read-only, workspace-write, or isolated-write")
    if profile.get("sandbox_mode") == "read-only" and profile.get("authoring_policy") != "read-only non-authoring":
        failures.append("read-only sandbox requires non-authoring policy")
    if profile.get("sandbox_mode") == "isolated-write" and profile.get("filesystem") != "isolated-write":
        failures.append("isolated-write sandbox requires isolated filesystem capability")
    return failures
