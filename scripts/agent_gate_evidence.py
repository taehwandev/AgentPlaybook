"""Structured route gate evidence ledger."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import (
    atomic_write_json,
    capsule_path_for_evidence,
    execution_capsule_binding_fingerprint,
    preflight_snapshot_binding_fingerprint,
    read_json_object,
)
from agent_route_state import (
    preflight_evidence_sha256,
    required_docs_for_route,
    route_fingerprint,
)
from agent_repair_ledger import (
    checkpoint_failure_signature,
    checkpoint_has_recorded_failure,
    record_finish_failure_checkpoints,
    register_repair_attempt,
    repair_checkpoint_path_for_preflight,
)
from agent_state_lock import state_lock


GATE_EVIDENCE_FILENAME = "gate-evidence.json"
SCHEMA_VERSION = 1
CAPSULE_BINDING_FIELD = "execution_capsule_binding"


FIELD_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "agentic run state": ("state", "transition", "evidence", "checkpoint", "blockers"),
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
    "graphify readiness": (
        "cli",
        "skill_doc",
        "runtime_links",
        "git_ownership",
        "project_integration",
        "graph",
        "query_smoke",
    ),
    "multi-agent split decision": ("mode", "reason", "verification"),
    "side-effect audit": ("scope", "result"),
    "source docs": ("required_docs", "source", "takeaway"),
    "tests": ("check", "result"),
}

MULTI_AGENT_PARALLEL_FIELDS = (
    "owned_scope",
    "forbidden_scope",
    "contract",
    "acceptance",
    "integration_owner",
)
MULTI_AGENT_SERIAL_MODES = {"serial", "single-agent", "single agent"}


def _sibling_evidence_path(evidence_path: Path, default_filename: str, suffix: str) -> Path:
    """Resolve a file that lives next to one preflight evidence file.

    Every per-preflight side-file (gate ledger, repair-checkpoints record,
    ...) shares this naming rule: the canonical filename when evidence_path
    is the default "preflight.json", otherwise a name derived from that
    evidence file's own stem so worker-isolated evidence paths (which are
    not literally named "preflight.json") still get their own side-file
    instead of colliding with the parent's.
    """

    if evidence_path.name != "preflight.json":
        return evidence_path.parent / f"{evidence_path.stem}-{suffix}"
    return evidence_path.parent / default_filename


def gate_evidence_path_for_preflight(evidence_path: Path) -> Path:
    return _sibling_evidence_path(evidence_path, GATE_EVIDENCE_FILENAME, "gate-evidence.json")


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
    _enforce_worker_evidence_boundary(evidence_path)
    path = gate_evidence_path_for_preflight(evidence_path)
    with state_lock(path):
        ledger = _new_ledger(evidence_path, preflight)
        _write_gate_evidence_ledger(path, ledger)
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
    _enforce_worker_evidence_boundary(evidence_path)
    path = gate_evidence_path_for_preflight(evidence_path)
    with state_lock(path):
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
            fields = canonical_gate_fields(
                gate,
                _string_fields(record.get("fields") or {}),
                preflight,
            )
            capsule_binding = _capsule_binding_for_preflight(evidence_path, preflight)
            if capsule_binding:
                fields[CAPSULE_BINDING_FIELD] = capsule_binding
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


def record_cli_gate_evidence(
    *,
    evidence_path: Path,
    preflight: dict[str, Any],
    cli_gate_evidence: dict[str, str],
) -> list[dict[str, Any]]:
    """Persist finish CLI fallback evidence before it participates in validation.

    A direct ``--gate`` value is compatibility input, not an in-memory
    override.  Writing it through the same ledger path gives it the current
    execution-capsule fingerprint and keeps every required gate subject to the
    same binding check.
    """

    records = [
        {
            "gate": gate,
            "evidence": evidence,
            "source": "finish cli fallback",
        }
        for gate, evidence in cli_gate_evidence.items()
    ]
    return record_many_gate_evidence(
        evidence_path=evidence_path,
        preflight=preflight,
        records=records,
    )


def bind_gate_evidence_to_capsule(
    *,
    evidence_path: Path,
    preflight: dict[str, Any],
) -> int:
    """Attach the ready capsule fingerprint to already-recorded route gates.

    Start must record request intake before a capsule can become ready.  This
    post-refresh pass closes that ordering gap without making a second
    document-reading command part of the lifecycle.
    """

    _enforce_worker_evidence_boundary(evidence_path)
    binding = _capsule_binding_for_preflight(evidence_path, preflight)
    if not binding:
        return 0
    path = gate_evidence_path_for_preflight(evidence_path)
    changed = 0
    with state_lock(path):
        ledger = read_gate_evidence_ledger(path)
        if not _ledger_matches_preflight(ledger, evidence_path, preflight):
            return 0
        required_gates = {str(gate) for gate in (preflight.get("route") or {}).get("gates", [])}
        entries = ledger.get("entries")
        if not isinstance(entries, list):
            return 0
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or entry.get("status") != "SUCCESS"
                or str(entry.get("gate") or "") not in required_gates
            ):
                continue
            fields = _string_fields(entry.get("fields") or {})
            if fields.get(CAPSULE_BINDING_FIELD) == binding:
                continue
            fields[CAPSULE_BINDING_FIELD] = binding
            entry["fields"] = dict(sorted(fields.items()))
            changed += 1
        if changed:
            _write_gate_evidence_ledger(path, ledger)
    return changed


def resync_gate_evidence_ledger(evidence_path: Path, preflight: dict[str, Any]) -> None:
    """Refresh the ledger's preflight binding after we mutate preflight.json ourselves.

    agent-hook.py's _register_started_run rewrites preflight.json in place to
    add agent_run_id right after "request intake" was already recorded
    against the pre-mutation content. Left alone, the ledger's stored
    preflight_evidence_sha256 goes stale, and the next gate write's self-heal
    check (record_many_gate_evidence / register_repair_attempt: "a stale
    ledger for the current preflight is not the same as an empty one") can no
    longer tell that stale-because-we-just-mutated-it apart from
    stale-because-this-is-a-genuinely-different-request, and silently wipes
    every already-recorded entry -- including "request intake" -- on every
    real task that reaches this point, not just when a new request begins.
    Call this immediately after any in-place preflight.json mutation whose
    route/request identity did not actually change.
    """

    _enforce_worker_evidence_boundary(evidence_path)
    path = gate_evidence_path_for_preflight(evidence_path)
    with state_lock(path):
        ledger = read_gate_evidence_ledger(path)
        if not ledger or ledger.get("invalid_json"):
            return
        # Only resync the binding fields when the route identity itself is
        # unchanged. If it genuinely differs (a real new request), leave the
        # mismatch alone so the normal self-heal path replaces the ledger.
        if ledger.get("route_fingerprint") != route_fingerprint(preflight.get("route") or {}):
            return
        _refresh_ledger_binding(ledger, evidence_path, preflight)
        _write_gate_evidence_ledger(path, ledger)


def _enforce_worker_evidence_boundary(evidence_path: Path) -> None:
    if os.environ.get("AGENTPLAYBOOK_PARENT_EVIDENCE_READONLY") == "1":
        raise PermissionError("reusable worker capsule cannot write parent gate evidence")
    expected = os.environ.get("AGENTPLAYBOOK_WORKER_EVIDENCE")
    if expected and evidence_path.resolve() != Path(expected).expanduser().resolve():
        raise PermissionError("worker may write only its launcher-issued gate evidence")


def merge_gate_evidence_from_ledger(
    *,
    route: dict[str, Any],
    evidence_path: Path,
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
        "capsule_bindings": {},
    }
    if cli_gate_evidence:
        diagnostics["warnings"].append(
            "CLI gate evidence must be persisted before ledger merge"
        )
    if not ledger:
        return {}, diagnostics
    if ledger.get("invalid_json"):
        diagnostics["warnings"].append("gate evidence ledger is not valid JSON")
        return {}, diagnostics
    if not _ledger_matches_route(ledger, evidence_path, route):
        diagnostics["warnings"].append("gate evidence ledger is stale for the current preflight route")
        return {}, diagnostics

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
        )
        if missing:
            if gate not in merged:
                diagnostics["missing_fields"][gate] = missing
            continue
        if evidence:
            merged[gate] = evidence
            diagnostics["sources"][gate] = str(entry.get("source") or "ledger")
            binding = _string_fields(entry.get("fields") or {}).get(CAPSULE_BINDING_FIELD)
            if binding:
                diagnostics["capsule_bindings"][gate] = binding
            else:
                diagnostics["capsule_bindings"].pop(gate, None)
            diagnostics["missing_fields"].pop(gate, None)

    diagnostics["used"] = bool(merged)
    return merged, diagnostics


def synthesize_gate_evidence(
    gate: str,
    evidence: str,
    fields: dict[str, str],
) -> tuple[str, list[str]]:
    missing = missing_structured_gate_fields(gate, evidence, fields)
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
            f"gate/command/check evidence: {fields['evidence']}; "
            f"checkpoint: {fields['checkpoint']}; blocker status: {fields['blockers']}",
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
        return (
            "multi-agent/subagent split; owned scope: "
            f"{fields['owned_scope']}; forbidden scope: {fields['forbidden_scope']}; "
            f"contract/brief: {fields['contract']}; acceptance checks: {fields['acceptance']}; "
            f"integration owner: {fields['integration_owner']}; verification: {fields['verification']}",
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
            f"reason: {fields['reason']}; original evidence: {evidence}",
            [],
        )
    if gate == "documentation":
        return (
            f"documentation decision: {fields['decision']}; source-of-truth target: "
            f"{fields['target']}; reason: {fields['reason']}; original evidence: {evidence}",
            [],
        )
    if gate == "source docs":
        return (
            "read every route required_docs entry directly before implementation or edits; "
            f"required-doc reading: {fields['required_docs']}; "
            "searched and opened/read source-of-truth docs before implementation or edits; "
            f"source: {fields['source']}; applied takeaway: {fields['takeaway']}; "
            f"original evidence: {evidence}",
            [],
        )
    if gate == "tests":
        return f"test/check run: {fields['check']}; result: {fields['result']}", []
    if gate == "graphify readiness":
        invalid = [
            field
            for field in FIELD_REQUIREMENTS[gate]
            if fields[field].strip().lower() != "success"
        ]
        if invalid:
            return "", [
                "graphify readiness fields must use exact success status: "
                + ", ".join(invalid)
            ]
        return (
            f"graphify readiness: cli={fields['cli']}; skill doc="
            f"{fields['skill_doc']}; runtime links={fields['runtime_links']}; "
            f"git ownership={fields['git_ownership']}; project integration="
            f"{fields['project_integration']}; target graph={fields['graph']}; "
            f"query smoke={fields['query_smoke']}",
            [],
        )
    if not evidence.strip():
        generic_fields = {
            key: value
            for key, value in fields.items()
            if key != CAPSULE_BINDING_FIELD and value.strip()
        }
        if generic_fields:
            evidence = "; ".join(
                f"{key}={generic_fields[key]}" for key in sorted(generic_fields)
            )
    return evidence, []


def missing_structured_gate_fields(
    gate: str,
    evidence: str,
    fields: dict[str, str],
) -> list[str]:
    """Return the complete structured-field requirement for one gate record."""

    missing = [
        field
        for field in FIELD_REQUIREMENTS.get(gate, ())
        if not fields.get(field, "").strip()
    ]
    if gate != "multi-agent split decision":
        return missing

    mode = fields.get("mode", "").strip().lower()
    parallel = mode not in MULTI_AGENT_SERIAL_MODES
    if parallel:
        missing.extend(
            field
            for field in MULTI_AGENT_PARALLEL_FIELDS
            if not fields.get(field, "").strip()
        )
    return list(dict.fromkeys(missing))


def incomplete_gate_evidence_failures(diagnostics: dict[str, Any]) -> list[str]:
    """Expose legacy ledger omissions as complete, actionable finish failures."""

    failures: list[str] = []
    missing_fields = diagnostics.get("missing_fields") or {}
    if not isinstance(missing_fields, dict):
        return failures
    for gate, missing in missing_fields.items():
        if not isinstance(missing, list) or not missing:
            continue
        failures.append(
            f"structured gate evidence for {gate} is incomplete: " + ", ".join(str(item) for item in missing)
        )
    return failures


def latest_successful_gate_fields(
    *,
    route: dict[str, Any],
    evidence_path: Path,
    gate: str,
) -> dict[str, str]:
    """Return the latest current-route fields for one successful gate."""

    ledger = read_gate_evidence_ledger(gate_evidence_path_for_preflight(evidence_path))
    if not _ledger_matches_route(ledger, evidence_path, route):
        return {}
    for entry in reversed(ledger.get("entries", [])):
        if (
            isinstance(entry, dict)
            and entry.get("status") == "SUCCESS"
            and str(entry.get("gate") or "") == gate
        ):
            return _string_fields(entry.get("fields") or {})
    return {}


def _new_ledger(evidence_path: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    route = preflight.get("route") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preflight_evidence": str(evidence_path.resolve()),
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
    if not _same_evidence_path(ledger.get("preflight_evidence"), evidence_path):
        return False
    if ledger.get("preflight_evidence_sha256") != preflight_evidence_sha256(evidence_path):
        return False
    return ledger.get("route_fingerprint") == route_fingerprint(route)


def _same_evidence_path(recorded: Any, evidence_path: Path) -> bool:
    try:
        return Path(str(recorded)).expanduser().resolve() == evidence_path.resolve()
    except (OSError, RuntimeError, ValueError):
        return False


def _refresh_ledger_binding(
    ledger: dict[str, Any],
    evidence_path: Path,
    preflight: dict[str, Any],
) -> None:
    ledger["preflight_evidence"] = str(evidence_path.resolve())
    ledger["preflight_evidence_sha256"] = preflight_evidence_sha256(evidence_path)
    ledger["route_fingerprint"] = route_fingerprint(preflight.get("route") or {})


def canonical_gate_fields(
    gate: str,
    fields: dict[str, str],
    preflight: dict[str, Any],
) -> dict[str, str]:
    """Populate fields the agent must not be allowed to self-declare."""

    if gate != "source docs":
        return fields
    required_docs = required_docs_for_route(preflight.get("route") or {})
    if required_docs:
        fields["required_docs"] = "required_docs manifest: " + ", ".join(required_docs)
    else:
        fields["required_docs"] = "required_docs manifest: empty"
    return fields


def _capsule_binding_for_preflight(
    evidence_path: Path,
    preflight: dict[str, Any],
) -> str | None:
    capsule = read_json_object(capsule_path_for_evidence(evidence_path))
    binding = execution_capsule_binding_fingerprint(capsule)
    if not binding:
        return _preflight_snapshot_binding(preflight)
    expected_hash = preflight_evidence_sha256(evidence_path)
    preflight_record = capsule.get("preflight_evidence")
    if not isinstance(preflight_record, dict):
        return _preflight_snapshot_binding(preflight)
    if preflight_record.get("sha256") != expected_hash:
        return _preflight_snapshot_binding(preflight)
    if capsule.get("route_fingerprint") != route_fingerprint(preflight.get("route") or {}):
        binding = None
    if binding:
        return binding
    return _preflight_snapshot_binding(preflight)


def _preflight_snapshot_binding(preflight: dict[str, Any]) -> str | None:
    snapshot = preflight.get("execution_snapshot")
    return (
        preflight_snapshot_binding_fingerprint(snapshot)
        if isinstance(snapshot, dict)
        else None
    )


def _string_fields(fields: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in fields.items() if value is not None}


def _write_gate_evidence_ledger(path: Path, ledger: dict[str, Any]) -> None:
    atomic_write_json(path, ledger)
