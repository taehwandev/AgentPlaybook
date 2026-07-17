"""Local Context File System snapshot for route-required documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_execution_capsule_docs import current_required_docs, required_doc_failures
from agent_execution_capsule_state import atomic_write_json, read_json_object
from agent_route_state import route_fingerprint


SCHEMA_VERSION = 1
CONTEXT_FILENAME = "context-snapshot.json"


def context_snapshot_path(project: Path) -> Path:
    return project.resolve() / ".agentplaybook" / CONTEXT_FILENAME


def refresh_context_snapshot(project: Path, rules: Path, route: dict[str, Any]) -> dict[str, Any]:
    docs = current_required_docs(rules.resolve(), route)
    if docs is None:
        raise ValueError("required context documents are unavailable")
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "route_fingerprint": route_fingerprint(route),
        "required_docs": docs,
    }
    atomic_write_json(context_snapshot_path(project), snapshot)
    return snapshot


def validate_context_snapshot(project: Path, rules: Path, route: dict[str, Any]) -> list[str]:
    snapshot = read_json_object(context_snapshot_path(project))
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        return ["context snapshot schema is missing or invalid"]
    if snapshot.get("route_fingerprint") != route_fingerprint(route):
        return ["context snapshot route fingerprint does not match"]
    docs = snapshot.get("required_docs")
    if not isinstance(docs, list):
        return ["context snapshot required docs are missing"]
    return required_doc_failures(docs, rules.resolve(), route)

