"""Required-document snapshot helpers for execution capsules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_execution_capsule_state import contained_doc_path, doc_hash_record
from agent_route_state import required_docs_for_route


def current_required_docs(
    rules: Path,
    route: dict[str, Any],
) -> list[dict[str, Any]] | None:
    records: list[dict[str, Any]] = []
    try:
        for relative in required_docs_for_route(route):
            records.append(doc_hash_record(relative, contained_doc_path(rules, relative)))
    except (OSError, ValueError):
        return None
    return records


def required_doc_failures(
    recorded: list[dict[str, Any]],
    rules: Path,
    route: dict[str, Any],
    documented_updates: set[str] | None = None,
) -> list[str]:
    expected = required_docs_for_route(route)
    if [str(item.get("path")) for item in recorded] != expected:
        return ["execution capsule required-doc manifest does not match"]
    failures: list[str] = []
    permitted_updates = documented_updates or set()
    for item in recorded:
        relative = str(item["path"])
        try:
            current = doc_hash_record(relative, contained_doc_path(rules, relative))
        except (OSError, ValueError):
            failures.append(f"execution capsule required doc is unavailable: {relative}")
            continue
        if relative in permitted_updates:
            continue
        if current["size_bytes"] != item["size_bytes"]:
            failures.append(f"execution capsule required doc size changed: {relative}")
        if current["sha256"] != item["sha256"]:
            failures.append(f"execution capsule required doc hash changed: {relative}")
    return failures
