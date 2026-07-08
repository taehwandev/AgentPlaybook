"""Route document read receipts for AgentPlaybook workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RECEIPT_FILENAME = "route-docs-read.json"


def route_fingerprint(route: dict[str, Any]) -> str:
    stable = {
        "command": route.get("command"),
        "platform": route.get("platform"),
        "concerns": route.get("concerns") or [],
        "docs": route.get("docs") or [],
        "required_docs": route.get("required_docs") or [],
        "reference_docs": route.get("reference_docs") or [],
        "gates": route.get("gates") or [],
    }
    payload = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def receipt_path_for_evidence(evidence_path: Path) -> Path:
    if evidence_path.name == "preflight.json":
        return evidence_path.parent / RECEIPT_FILENAME
    return evidence_path.parent / f"{evidence_path.stem}-{RECEIPT_FILENAME}"


def receipt_candidate_paths_for_evidence(evidence_path: Path) -> list[Path]:
    primary = receipt_path_for_evidence(evidence_path)
    fallback = evidence_path.parent / RECEIPT_FILENAME
    if fallback == primary:
        return [primary]
    return [primary, fallback]


def preflight_evidence_sha256(evidence_path: Path) -> str:
    return hashlib.sha256(evidence_path.read_bytes()).hexdigest()


def read_route_doc_receipt(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"invalid_json": True, "path": str(path)}


def route_docs_to_read(route: dict[str, Any]) -> list[str]:
    docs = route.get("required_docs") or route.get("docs") or []
    return [str(doc) for doc in docs if str(doc).strip()]


def build_route_doc_receipt(
    *,
    playbook_root: Path,
    project: Path,
    evidence_path: Path,
    route: dict[str, Any],
) -> dict[str, Any]:
    docs = route_docs_to_read(route)
    entries: list[dict[str, Any]] = []
    for doc in docs:
        absolute = (playbook_root / doc).resolve()
        data = absolute.read_bytes()
        entries.append(
            {
                "path": doc,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "playbook_root": str(playbook_root),
        "preflight_evidence": str(evidence_path),
        "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
        "route_fingerprint": route_fingerprint(route),
        "doc_count": len(entries),
        "read_scope": "required_docs" if route.get("required_docs") else "docs",
        "routed_doc_count": len(route.get("docs") or []),
        "reference_doc_count": len(route.get("reference_docs") or []),
        "docs": entries,
    }


def validate_route_doc_receipt(
    route: dict[str, Any],
    receipt: dict[str, Any],
    evidence_path: Path | None = None,
) -> list[str]:
    docs = route_docs_to_read(route)
    if not docs:
        return ["route docs read receipt cannot be checked because preflight required docs are missing"]
    if not receipt:
        return [f"route docs read receipt is missing; run docs-read after preflight for {len(docs)} required docs"]
    if receipt.get("invalid_json"):
        return ["route docs read receipt is not valid JSON"]
    if receipt.get("schema_version") != 1:
        return ["route docs read receipt has an unsupported schema version"]
    if receipt.get("route_fingerprint") != route_fingerprint(route):
        return ["route docs read receipt does not match the current preflight route manifest"]
    if receipt.get("doc_count") != len(docs):
        return ["route docs read receipt doc_count does not match the current preflight required-doc manifest"]

    if evidence_path:
        if receipt.get("preflight_evidence") != str(evidence_path):
            return ["route docs read receipt is bound to a different preflight evidence file"]
        if receipt.get("preflight_evidence_sha256") != preflight_evidence_sha256(evidence_path):
            return ["route docs read receipt is stale for the current preflight evidence file"]

    receipt_docs = receipt.get("docs") or []
    receipt_paths = {str(item.get("path")) for item in receipt_docs if item.get("path")}
    missing = [doc for doc in docs if doc not in receipt_paths]
    if missing:
        preview = ", ".join(missing[:5])
        suffix = " ..." if len(missing) > 5 else ""
        return [f"route docs read receipt is missing required docs: {preview}{suffix}"]

    malformed = [
        str(item.get("path") or "<unknown>")
        for item in receipt_docs
        if not item.get("sha256") or not isinstance(item.get("size_bytes"), int)
    ]
    if malformed:
        preview = ", ".join(malformed[:5])
        suffix = " ..." if len(malformed) > 5 else ""
        return [f"route docs read receipt has malformed doc entries: {preview}{suffix}"]
    return []
