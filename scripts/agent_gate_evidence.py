"""Structured route gate evidence ledger."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_route_docs import preflight_evidence_sha256, route_fingerprint, validate_route_doc_receipt


GATE_EVIDENCE_FILENAME = "gate-evidence.json"
SCHEMA_VERSION = 1


FIELD_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "agentic run state": ("state", "transition", "evidence"),
    "boundary plan": ("scope", "verification"),
    "cycle contract": (
        "cycle_type",
        "input_scope",
        "allowed_changes",
        "forbidden_changes",
        "acceptance_criteria",
        "verification",
        "stop_condition",
        "checkpoint",
    ),
    "documentation": ("decision", "target", "reason"),
    "documentation impact": ("artifact", "decision", "reason"),
    "multi-agent split decision": ("mode", "reason", "verification"),
    "route docs read": ("takeaway",),
    "side-effect audit": ("scope", "result"),
    "source docs": ("source", "outcome"),
    "tests": ("check", "result"),
}


def gate_evidence_path_for_preflight(evidence_path: Path) -> Path:
    if evidence_path.name != "preflight.json":
        return evidence_path.parent / f"{evidence_path.stem}-gate-evidence.json"
    return evidence_path.parent / GATE_EVIDENCE_FILENAME


def parse_field(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise ValueError("field must use key=value")
    key, field_value = value.split("=", 1)
    key = key.strip()
    field_value = field_value.strip()
    if not key or not field_value:
        raise ValueError("field key and value must both be non-empty")
    return key, field_value


def read_gate_evidence_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"invalid_json": True, "path": str(path)}


def reset_gate_evidence_ledger(evidence_path: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    ledger = _new_ledger(evidence_path, preflight)
    _write_gate_evidence_ledger(gate_evidence_path_for_preflight(evidence_path), ledger)
    return ledger


def record_gate_evidence(
    *,
    evidence_path: Path,
    preflight: dict[str, Any],
    gate: str,
    evidence: str = "",
    fields: dict[str, str] | None = None,
    status: str = "SUCCESS",
    source: str = "manual",
) -> dict[str, Any]:
    entries = record_many_gate_evidence(
        evidence_path=evidence_path,
        preflight=preflight,
        records=[
            {
                "gate": gate,
                "evidence": evidence,
                "fields": fields or {},
                "status": status,
                "source": source,
            }
        ],
    )
    return entries[0]


def record_many_gate_evidence(
    *,
    evidence_path: Path,
    preflight: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not records:
        return []
    path = gate_evidence_path_for_preflight(evidence_path)
    ledger = read_gate_evidence_ledger(path)
    if not _ledger_matches_preflight(ledger, evidence_path, preflight):
        ledger = _new_ledger(evidence_path, preflight)
    entries = [item for item in ledger.get("entries", []) if isinstance(item, dict)]
    recorded: list[dict[str, Any]] = []
    for record in records:
        gate = str(record.get("gate") or "").strip()
        if not gate:
            raise ValueError("gate evidence record requires a non-empty gate")
        status = str(record.get("status") or "SUCCESS").strip()
        if status not in {"SUCCESS", "FAIL"}:
            raise ValueError(f"gate evidence record has invalid status: {status}")
        fields = _string_fields(record.get("fields") or {})
        entry = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "gate": gate,
            "status": status,
            "source": str(record.get("source") or "manual"),
            "evidence": str(record.get("evidence") or ""),
            "fields": dict(sorted(fields.items())),
        }
        entries.append(entry)
        recorded.append(entry)
    _refresh_ledger_binding(ledger, evidence_path, preflight)
    ledger["entries"] = entries
    _write_gate_evidence_ledger(path, ledger)
    return recorded


def merge_gate_evidence_from_ledger(
    *,
    route: dict[str, Any],
    evidence_path: Path,
    route_docs_receipt: dict[str, Any],
    cli_gate_evidence: dict[str, str],
) -> tuple[dict[str, str], dict[str, Any]]:
    path = gate_evidence_path_for_preflight(evidence_path)
    ledger = read_gate_evidence_ledger(path)
    diagnostics: dict[str, Any] = {
        "path": str(path),
        "used": False,
        "warnings": [],
        "missing_fields": {},
        "sources": {},
    }
    if not ledger:
        return dict(cli_gate_evidence), diagnostics
    if ledger.get("invalid_json"):
        diagnostics["warnings"].append("gate evidence ledger is not valid JSON")
        return dict(cli_gate_evidence), diagnostics
    if not _ledger_matches_route(ledger, evidence_path, route):
        diagnostics["warnings"].append("gate evidence ledger is stale for the current preflight route")
        return dict(cli_gate_evidence), diagnostics

    merged: dict[str, str] = {}
    required_gates = {str(gate) for gate in (route.get("gates") or [])}
    for entry in ledger.get("entries", []):
        if not isinstance(entry, dict) or entry.get("status") != "SUCCESS":
            continue
        gate = str(entry.get("gate") or "")
        if gate not in required_gates:
            continue
        evidence, missing = synthesize_gate_evidence(
            gate,
            str(entry.get("evidence") or ""),
            _string_fields(entry.get("fields") or {}),
            route_docs_receipt,
            route,
        )
        if missing:
            diagnostics["missing_fields"][gate] = missing
            continue
        if evidence:
            merged[gate] = evidence
            diagnostics["sources"][gate] = str(entry.get("source") or "ledger")

    merged.update(cli_gate_evidence)
    diagnostics["used"] = bool(merged)
    return merged, diagnostics


def synthesize_gate_evidence(
    gate: str,
    evidence: str,
    fields: dict[str, str],
    route_docs_receipt: dict[str, Any],
    route: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    if gate == "route docs read":
        receipt_failures = validate_route_doc_receipt(route or {}, route_docs_receipt)
        if receipt_failures:
            return "", ["matching route docs receipt"]
        missing = _missing_fields(gate, fields)
        if missing:
            return "", missing
        return (
            "read required skill/guidance docs before code, implementation, or editing "
            f"with docs-read receipt; applied rule/takeaway: {fields['takeaway']}",
            [],
        )
    missing = _missing_fields(gate, fields)
    if missing:
        return "", missing
    if gate == "cycle contract":
        return (
            f"cycle_type={fields['cycle_type']}; input_scope={fields['input_scope']}; "
            f"allowed_changes={fields['allowed_changes']}; "
            f"forbidden_changes={fields['forbidden_changes']}; "
            f"acceptance criteria={fields['acceptance_criteria']}; "
            f"verification={fields['verification']}; "
            f"stop condition={fields['stop_condition']}; checkpoint={fields['checkpoint']}",
            [],
        )
    if gate == "agentic run state":
        return (
            f"run state: {fields['state']}; next transition: {fields['transition']}; "
            f"gate/command/check evidence: {fields['evidence']}",
            [],
        )
    if gate == "boundary plan":
        return (
            f"boundary/scope: {fields['scope']}; nearest verification/check: "
            f"{fields['verification']}",
            [],
        )
    if gate == "multi-agent split decision":
        mode = fields["mode"].lower()
        if mode in {"serial", "single-agent", "single agent"}:
            return (
                "serial/single-agent decision; concrete reason: "
                f"{fields['reason']}; verification: {fields['verification']}",
                [],
            )
        extra_missing = [
            field
            for field in ("owned_scope", "forbidden_scope", "contract")
            if not fields.get(field)
        ]
        if extra_missing:
            return "", extra_missing
        return (
            "multi-agent/subagent split; owned scope: "
            f"{fields['owned_scope']}; forbidden scope: {fields['forbidden_scope']}; "
            f"contract/brief: {fields['contract']}; verification: {fields['verification']}",
            [],
        )
    if gate == "side-effect audit":
        return (
            "side-effect audit checked final diff; "
            f"scope/risk reviewed: {fields['scope']}; result: {fields['result']}",
            [],
        )
    if gate == "documentation impact":
        return (
            "pre-code/pre-edit documentation artifact selection: "
            f"{fields['artifact']}; impact decision: {fields['decision']}; "
            f"reason: {fields['reason']}",
            [],
        )
    if gate == "documentation":
        return (
            f"documentation decision: {fields['decision']}; source-of-truth target: "
            f"{fields['target']}; reason: {fields['reason']}",
            [],
        )
    if gate == "source docs":
        return (
            "searched and opened/read source-of-truth docs before implementation or edits; "
            f"source: {fields['source']}; outcome used/applied: {fields['outcome']}",
            [],
        )
    if gate == "tests":
        return f"test/check run: {fields['check']}; result: {fields['result']}", []
    return evidence, []


def _missing_fields(gate: str, fields: dict[str, str]) -> list[str]:
    return [field for field in FIELD_REQUIREMENTS.get(gate, ()) if not fields.get(field)]


def _new_ledger(evidence_path: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    route = preflight.get("route") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preflight_evidence": str(evidence_path),
        "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
        "route_fingerprint": route_fingerprint(route),
        "entries": [],
    }


def _ledger_matches_preflight(
    ledger: dict[str, Any],
    evidence_path: Path,
    preflight: dict[str, Any],
) -> bool:
    return _ledger_matches_route(ledger, evidence_path, preflight.get("route") or {})


def _ledger_matches_route(ledger: dict[str, Any], evidence_path: Path, route: dict[str, Any]) -> bool:
    if ledger.get("schema_version") != SCHEMA_VERSION:
        return False
    if ledger.get("preflight_evidence") != str(evidence_path):
        return False
    if ledger.get("preflight_evidence_sha256") != preflight_evidence_sha256(evidence_path):
        return False
    return ledger.get("route_fingerprint") == route_fingerprint(route)


def _refresh_ledger_binding(
    ledger: dict[str, Any],
    evidence_path: Path,
    preflight: dict[str, Any],
) -> None:
    ledger["preflight_evidence"] = str(evidence_path)
    ledger["preflight_evidence_sha256"] = preflight_evidence_sha256(evidence_path)
    ledger["route_fingerprint"] = route_fingerprint(preflight.get("route") or {})


def _string_fields(fields: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in fields.items() if value is not None}


def _write_gate_evidence_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
