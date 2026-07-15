"""Finish-time documentation exceptions for the source-doc snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_gate_evidence import SCHEMA_VERSION, gate_evidence_path_for_preflight, read_gate_evidence_ledger
from agent_route_state import preflight_evidence_sha256, required_docs_for_route, route_fingerprint


def documented_required_doc_updates(
    *,
    evidence_path: Path,
    route: dict[str, Any],
) -> set[str]:
    """Return required docs explicitly declared as updated final artifacts."""

    required_docs = set(required_docs_for_route(route))
    if not required_docs:
        return set()
    ledger = read_gate_evidence_ledger(gate_evidence_path_for_preflight(evidence_path))
    if not _ledger_matches_route(ledger, evidence_path, route):
        return set()
    updates: set[str] = set()
    for entry in ledger.get("entries", []):
        if not isinstance(entry, dict) or entry.get("status") != "SUCCESS":
            continue
        if str(entry.get("gate") or "") != "documentation":
            continue
        fields = {str(key): str(value) for key, value in (entry.get("fields") or {}).items()}
        if fields.get("decision", "").strip().lower() != "updated":
            continue
        target = fields.get("target", "").strip()
        if target in required_docs:
            updates.add(target)
    return updates


def _ledger_matches_route(ledger: dict[str, Any], evidence_path: Path, route: dict[str, Any]) -> bool:
    try:
        same_path = Path(str(ledger.get("preflight_evidence"))).expanduser().resolve() == evidence_path.resolve()
    except (OSError, RuntimeError, ValueError):
        same_path = False
    return (
        ledger.get("schema_version") == SCHEMA_VERSION
        and same_path
        and ledger.get("preflight_evidence_sha256") == preflight_evidence_sha256(evidence_path)
        and ledger.get("route_fingerprint") == route_fingerprint(route)
    )
