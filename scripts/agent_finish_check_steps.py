"""Step functions for AgentPlaybook finish checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_finish_common import add_gate_signal, append_unique
from agent_finish_gate_policy import validate_gate_evidence


QUESTION_DRILL_PHRASES = (
    "grill me",
    "ask me questions",
    "help define requirements",
    "question drill",
    "question_drill: true",
    "question_drill true",
    "\uadf8\ub9b4\ubbf8",
)
QUESTION_DRILL_EVIDENCE_GATES = (
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
    for failure in gate_policy_failures:
        add_gate_signal(gate_signals, "FAIL", "gate evidence policy", "failed", failure)
        failures.append(failure)
    return required_gates, missed_gates, gate_policy_failures


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

    question_drill_required = question_drill_requested(
        _request_text(request_intake, request_classification)
    )
    drill_gate = next((gate for gate in QUESTION_DRILL_EVIDENCE_GATES if gate_evidence.get(gate)), "")
    if question_drill_required and drill_gate:
        add_gate_signal(
            gate_signals,
            "SUCCESS",
            "question drill",
            "executed",
            f"{drill_gate}: {gate_evidence[drill_gate]}",
        )
    elif question_drill_required:
        append_unique(missed_gates, "question drill")
        add_gate_signal(
            gate_signals,
            "FAIL",
            "question drill",
            "missed",
            "request classification required a question drill but no drill evidence was provided",
        )
        failures.append(
            "question drill was required by request classification but no question-drill gate evidence was provided"
        )
    return question_drill_required


def check_preflight_vibeguard(preflight: dict[str, Any], failures: list[str]) -> None:
    preflight_vibeguard_command = preflight.get("vibeguard") or {}
    preflight_vibeguard = preflight_vibeguard_command.get("overall") or {}
    if not preflight_vibeguard:
        failures.append("preflight evidence is missing VibeGuard result")
    elif preflight_vibeguard_command.get("returncode") != 0:
        failures.append("preflight VibeGuard audit failed")
    elif preflight_vibeguard.get("status") == "unknown":
        failures.append("preflight VibeGuard overall status could not be parsed")


def question_drill_requested(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in QUESTION_DRILL_PHRASES)


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
