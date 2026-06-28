"""Step functions for AgentPlaybook finish checks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from agent_delegation_plan import validate_delegation_plan_evidence
from agent_finish_common import add_gate_signal, append_unique
from agent_finish_gate_policy import ROUTE_DOCS_READ_GATE, validate_gate_evidence
from agent_route_docs import read_route_doc_receipt, receipt_path_for_evidence, validate_route_doc_receipt
from workflow_request_patterns import GRILL_ME_REQUEST_PATTERNS


LEGACY_GRILL_ME_FLAGS = (
    "grill_me: true",
    "grill_me true",
    "question_drill: true",
    "question_drill true",
)
GRILL_ME_EVIDENCE_GATES = (
    "grill-me if needed",
    "grill-me",
    "question drill if needed",
    "ask blockers",
    "question drill",
    "clarification drill",
)


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    project = args.project.resolve()
    rules = args.rules.resolve()
    evidence_path = (
        args.evidence.resolve()
        if args.evidence
        else project / ".agentplaybook" / "preflight.json"
    )
    output_path = (
        args.output.resolve()
        if args.output
        else project / ".agentplaybook" / "finish.json"
    )
    return project, rules, evidence_path, output_path


def read_preflight(evidence_path: Path, failures: list[str]) -> dict[str, Any]:
    if not evidence_path.exists():
        failures.append(f"missing preflight evidence at {evidence_path}")
        return {}
    try:
        return json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        failures.append(f"preflight evidence is not valid JSON: {error}")
        return {}


def check_required_gates(
    route: dict[str, Any],
    gate_evidence: dict[str, str],
    gate_signals: list[dict[str, str]],
    failures: list[str],
    route_docs_receipt: dict[str, Any] | None = None,
    evidence_path: Path | None = None,
    delegation_plan: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    required_gates = route.get("gates") or []
    if not required_gates:
        failures.append("preflight evidence is missing route gates")
    missed_gates: list[str] = []
    for gate in required_gates:
        evidence = gate_evidence.get(gate, "")
        if evidence:
            add_gate_signal(gate_signals, "SUCCESS", gate, "executed", evidence)
        else:
            append_unique(missed_gates, gate)
            add_gate_signal(gate_signals, "FAIL", gate, "missed", "missing evidence")

    if missed_gates:
        failures.append("missing required gate evidence: " + ", ".join(missed_gates))

    gate_policy_failures = validate_gate_evidence(gate_evidence, required_gates)
    gate_policy_failures.extend(
        validate_delegation_plan_evidence(required_gates, gate_evidence, delegation_plan or {})
    )
    gate_policy_failures.extend(
        validate_route_docs_manifest_evidence(
            route,
            gate_evidence,
            route_docs_receipt or {},
            evidence_path,
        )
    )
    for failure in gate_policy_failures:
        add_gate_signal(gate_signals, "FAIL", "gate evidence policy", "failed", failure)
        failures.append(failure)
    return required_gates, missed_gates, gate_policy_failures


def read_route_docs_receipt_for_preflight(evidence_path: Path) -> dict[str, Any]:
    return read_route_doc_receipt(receipt_path_for_evidence(evidence_path))


def validate_route_docs_manifest_evidence(
    route: dict[str, Any],
    gate_evidence: dict[str, str],
    route_docs_receipt: dict[str, Any],
    evidence_path: Path | None = None,
) -> list[str]:
    required_gates = route.get("gates") or []
    if ROUTE_DOCS_READ_GATE not in required_gates:
        return []
    evidence = gate_evidence.get(ROUTE_DOCS_READ_GATE, "")
    if not evidence:
        return []
    return validate_route_doc_receipt(route, route_docs_receipt, evidence_path)


def check_request_intake(
    route: dict[str, Any],
    request_intake: dict[str, Any],
    request_classification: dict[str, Any],
    gate_evidence: dict[str, str],
    gate_signals: list[dict[str, str]],
    missed_gates: list[str],
    failures: list[str],
) -> bool:
    if route.get("request_classified") and not request_intake.get("classification_evidence"):
        append_unique(missed_gates, "request intake")
        add_gate_signal(
            gate_signals,
            "FAIL",
            "request intake",
            "missed",
            "--request-classified used without classification evidence",
        )
        failures.append("--request-classified used without classification evidence")

    grill_me_required = _classification_requires_grill_me(request_classification) or grill_me_requested(
        _request_text(request_intake, request_classification)
    )
    grill_me_gate = next((gate for gate in GRILL_ME_EVIDENCE_GATES if gate_evidence.get(gate)), "")
    if grill_me_required and grill_me_gate:
        evidence = gate_evidence[grill_me_gate]
        evidence_failures = validate_grill_me_skill_evidence(evidence)
        if evidence_failures:
            append_unique(missed_gates, "grill-me")
            for failure in evidence_failures:
                add_gate_signal(gate_signals, "FAIL", "grill-me", "failed", failure)
                failures.append(failure)
        else:
            add_gate_signal(
                gate_signals,
                "SUCCESS",
                "grill-me",
                "executed",
                f"{grill_me_gate}: {evidence}",
            )
    elif grill_me_required:
        append_unique(missed_gates, "grill-me")
        add_gate_signal(
            gate_signals,
            "FAIL",
            "grill-me",
            "missed",
            "request classification required the Grill-Me protocol but no Grill-Me evidence was provided",
        )
        failures.append(
            "Grill-Me protocol was required by request classification but no Grill-Me gate evidence was provided"
        )
    return grill_me_required


def check_preflight_vibeguard(preflight: dict[str, Any], failures: list[str]) -> None:
    preflight_vibeguard_command = preflight.get("vibeguard") or {}
    preflight_vibeguard = preflight_vibeguard_command.get("overall") or {}
    if not preflight_vibeguard:
        failures.append("preflight evidence is missing VibeGuard result")
    elif preflight_vibeguard_command.get("returncode") != 0:
        failures.append("preflight VibeGuard audit failed")
    elif preflight_vibeguard.get("status") == "unknown":
        failures.append("preflight VibeGuard overall status could not be parsed")


def grill_me_requested(text: str) -> bool:
    lowered = text.lower()
    return any(flag in lowered for flag in LEGACY_GRILL_ME_FLAGS) or any(
        re.search(pattern, lowered) for pattern in GRILL_ME_REQUEST_PATTERNS
    )


def _classification_requires_grill_me(request_classification: dict[str, Any]) -> bool:
    return _truthy(request_classification.get("grill_me")) or _truthy(
        request_classification.get("question_drill")
    )


def _truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def validate_grill_me_skill_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    names_skill = any(
        phrase in text
        for phrase in ("grill-me", "grill me", "grillme", "/grilling", "grilling", "\uadf8\ub9b4\ubbf8")
    )
    names_session = any(
        phrase in text
        for phrase in (
            "skill",
            "/grilling",
            "grilling",
            "session",
            "started",
            "ran",
            "used",
            "invocation",
            "invoked",
            "output",
            "result",
        )
    )
    names_outcome = any(
        phrase in text
        for phrase in (
            "completed",
            "asked",
            "answered",
            "blocker",
            "questions",
            "one question",
            "recommended answer",
            "feedback",
            "decisions",
            "resolved",
            "no blockers",
            "clarified",
        )
    )
    if names_skill and names_session and names_outcome:
        return []
    return [
        "Grill-Me evidence must name the Grill-Me protocol, skill, or /grilling session and its output; "
        "unstructured manual blocker questions alone are not enough"
    ]


question_drill_requested = grill_me_requested
validate_grill_me_service_evidence = validate_grill_me_skill_evidence


def _request_text(request_intake: dict[str, Any], request_classification: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in (
            request_intake.get("request"),
            request_intake.get("classification_evidence"),
            request_classification.get("request"),
        )
        if value
    )
