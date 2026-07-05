"""Gate ledger helpers for the AgentPlaybook hook CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_gate_evidence import (
    parse_field,
    record_gate_evidence,
    record_many_gate_evidence,
    reset_gate_evidence_ledger,
)
from agent_hook_runtime import finish_with_result, print_status


def preflight_evidence_path(args: argparse.Namespace) -> Path:
    return args.evidence if args.evidence else args.project / ".agentplaybook" / "preflight.json"


def gate_hook(args: argparse.Namespace) -> int:
    fields: dict[str, str] = {}
    for raw_field in args.field:
        try:
            key, value = parse_field(raw_field)
        except ValueError as error:
            print_status("gate", False, [str(error)])
            return 1
        fields[key] = value
    try:
        entry = record_hook_gate(
            args,
            args.gate_name,
            args.gate_evidence or "",
            fields,
            args.source,
            args.status,
        )
    except (OSError, json.JSONDecodeError) as error:
        print_status("gate", False, [f"gate evidence ledger update failed: {error}"])
        return 1
    return finish_with_result(
        "gate",
        True,
        [f"gate evidence recorded: {entry['gate']}"],
        args.output,
        {"gate_evidence": entry},
        args.retry_attempt,
    )


def gate_batch_hook(args: argparse.Namespace) -> int:
    try:
        records = _gate_records_from_args(args)
        entries = record_hook_gate_batch(args, records)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print_status("gate-batch", False, [f"gate evidence batch update failed: {error}"])
        return 1
    details = [f"{len(entries)} gate evidence entries recorded"]
    details.extend(f"recorded gate: {entry['gate']}" for entry in entries[:8])
    if len(entries) > 8:
        details.append(f"recorded gates truncated: {len(entries) - 8} more")
    return finish_with_result(
        "gate-batch",
        True,
        details,
        args.output,
        {"gate_evidence": entries},
        args.retry_attempt,
    )


def record_hook_gate(
    args: argparse.Namespace,
    gate: str,
    evidence: str,
    fields: dict[str, str],
    source: str,
    status: str = "SUCCESS",
) -> dict[str, Any]:
    evidence_path = preflight_evidence_path(args)
    preflight = json.loads(evidence_path.read_text(encoding="utf-8"))
    return record_gate_evidence(
        evidence_path=evidence_path,
        preflight=preflight,
        gate=gate,
        evidence=evidence,
        fields=fields,
        status=status,
        source=source,
    )


def record_hook_gate_batch(
    args: argparse.Namespace,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence_path = preflight_evidence_path(args)
    preflight = json.loads(evidence_path.read_text(encoding="utf-8"))
    return record_many_gate_evidence(
        evidence_path=evidence_path,
        preflight=preflight,
        records=records,
    )


def reset_and_record_start_gate(args: argparse.Namespace) -> None:
    evidence_path = preflight_evidence_path(args)
    try:
        preflight = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    reset_gate_evidence_ledger(evidence_path, preflight)
    classification_evidence = (
        (preflight.get("request_intake") or {}).get("classification_evidence")
        or "request provided to preflight"
    )
    record_gate_evidence(
        evidence_path=evidence_path,
        preflight=preflight,
        gate="request intake",
        evidence=f"preflight request intake completed: {classification_evidence}",
        fields={"classification_evidence": str(classification_evidence)},
        status="SUCCESS",
        source="start",
    )


def _gate_records_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw_record in args.gate_record:
        records.extend(_parse_gate_records(raw_record))
    if args.gate_json:
        records.extend(_parse_gate_records(args.gate_json.read_text(encoding="utf-8")))
    if not records:
        raise ValueError("gate-batch requires --gate-record or --gate-json")
    return records


def _parse_gate_records(raw: str) -> list[dict[str, Any]]:
    payload = json.loads(raw)
    if isinstance(payload, list):
        return [_normalize_gate_record(item) for item in payload]
    return [_normalize_gate_record(payload)]


def _normalize_gate_record(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("gate record JSON must be an object or an array of objects")
    gate = str(payload.get("gate") or payload.get("gate_name") or "").strip()
    if not gate:
        raise ValueError("gate record JSON requires gate")
    status = str(payload.get("status") or "SUCCESS").strip()
    if status not in {"SUCCESS", "FAIL"}:
        raise ValueError(f"gate record JSON has invalid status: {status}")
    fields = payload.get("fields") or {}
    if not isinstance(fields, dict):
        raise ValueError(f"gate record for {gate} has non-object fields")
    return {
        "gate": gate,
        "status": status,
        "source": str(payload.get("source") or "manual"),
        "evidence": str(payload.get("evidence") or payload.get("gate_evidence") or ""),
        "fields": {str(key): str(value) for key, value in fields.items()},
    }
