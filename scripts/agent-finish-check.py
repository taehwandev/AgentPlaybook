#!/usr/bin/env python3
"""Verify AgentPlaybook gate evidence before final report, commit, or handoff."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
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
SIGNAL_DISPLAY = {
    "SUCCESS": "\U0001f431\U0001f7e2 SUCCESS",
    "FAIL": "\U0001f431\U0001f534 FAIL",
}


def clean_output(text: str) -> str:
    return ANSI_RE.sub("", text)


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": result.returncode,
        "stdout": clean_output(result.stdout),
        "stderr": clean_output(result.stderr),
    }


def vibeguard_command(project: Path, rules: Path) -> list[str]:
    binary = shutil.which("vibeguard")
    if binary:
        return [binary, "audit", str(project), "--rules", str(rules)]
    return [
        "npx",
        "--yes",
        "@taehwandev/vibeguard",
        "audit",
        str(project),
        "--rules",
        str(rules),
    ]


def parse_overall(output: str) -> dict[str, str]:
    for raw_line in clean_output(output).splitlines():
        line = raw_line.strip()
        if not line.startswith("Overall:"):
            continue
        value = line.split("Overall:", 1)[1].strip()
        if "Ready" in value:
            status = "Ready"
        elif "Needs review" in value:
            status = "Needs review"
        elif "Blocked" in value:
            status = "Blocked"
        else:
            status = value or "unknown"
        return {"status": status, "line": line}
    return {"status": "unknown", "line": ""}


def parse_gate(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("gate evidence must use '<gate>=<evidence>'")
    gate, evidence = value.split("=", 1)
    gate = gate.strip()
    evidence = evidence.strip()
    if not gate or not evidence:
        raise argparse.ArgumentTypeError("gate and evidence must both be non-empty")
    return gate, evidence


def question_drill_requested(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in QUESTION_DRILL_PHRASES)


def add_gate_signal(
    gate_signals: list[dict[str, str]],
    signal: str,
    gate: str,
    status: str,
    evidence: str,
) -> None:
    gate_signals.append(
        {
            "gate": gate,
            "signal": signal,
            "status": status,
            "evidence": evidence,
        }
    )


def display_signal(signal: str) -> str:
    return SIGNAL_DISPLAY.get(signal, signal)


def append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    playbook_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Check route gate evidence, validation, diff hygiene, and VibeGuard."
    )
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--rules", type=Path, default=playbook_root)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gate", action="append", default=[], type=parse_gate)
    parser.add_argument(
        "--allow-vibeguard-review",
        help="required reason when final VibeGuard is not Ready",
    )
    args = parser.parse_args()

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

    failures: list[str] = []
    if not evidence_path.exists():
        failures.append(f"missing preflight evidence at {evidence_path}")
        preflight: dict[str, Any] = {}
    else:
        try:
            preflight = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            failures.append(f"preflight evidence is not valid JSON: {error}")
            preflight = {}

    route = preflight.get("route") or {}
    request_intake = preflight.get("request_intake") or {}
    request_classification = route.get("request_classification") or {}
    required_gates = route.get("gates") or []
    if not required_gates:
        failures.append("preflight evidence is missing route gates")
    gate_evidence = dict(args.gate)
    missed_gates: list[str] = []
    gate_signals: list[dict[str, str]] = []
    for gate in required_gates:
        evidence = gate_evidence.get(gate, "")
        if evidence:
            add_gate_signal(gate_signals, "SUCCESS", gate, "executed", evidence)
        else:
            append_unique(missed_gates, gate)
            add_gate_signal(gate_signals, "FAIL", gate, "missed", "missing evidence")

    if missed_gates:
        failures.append("missing required gate evidence: " + ", ".join(missed_gates))

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

    request_text = " ".join(
        str(value)
        for value in (
            request_intake.get("request"),
            request_intake.get("classification_evidence"),
            request_classification.get("request"),
        )
        if value
    )
    question_drill_required = bool(
        request_classification.get("question_drill")
    ) or question_drill_requested(request_text)
    question_drill_evidence_gate = next(
        (gate for gate in QUESTION_DRILL_EVIDENCE_GATES if gate_evidence.get(gate)),
        "",
    )
    if question_drill_required and question_drill_evidence_gate:
        add_gate_signal(
            gate_signals,
            "SUCCESS",
            "question drill",
            "executed",
            f"{question_drill_evidence_gate}: {gate_evidence[question_drill_evidence_gate]}",
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

    preflight_vibeguard_command = preflight.get("vibeguard") or {}
    preflight_vibeguard = preflight_vibeguard_command.get("overall") or {}
    if not preflight_vibeguard:
        failures.append("preflight evidence is missing VibeGuard result")
    elif preflight_vibeguard_command.get("returncode") != 0:
        failures.append("preflight VibeGuard audit failed")
    elif preflight_vibeguard.get("status") == "unknown":
        failures.append("preflight VibeGuard overall status could not be parsed")

    validate = run_command(
        [sys.executable, str(playbook_root / "scripts" / "workflow.py"), "validate"],
        playbook_root,
    )
    diff_check = run_command(["git", "diff", "--check"], project)
    vibeguard = run_command(vibeguard_command(project, rules), project)
    vibeguard_output = vibeguard["stdout"] + "\n" + vibeguard["stderr"]
    vibeguard["overall"] = parse_overall(vibeguard_output)

    if validate["returncode"] != 0:
        add_gate_signal(gate_signals, "FAIL", "workflow validate", "failed", "non-zero exit")
        failures.append("workflow validate failed")
    else:
        add_gate_signal(gate_signals, "SUCCESS", "workflow validate", "executed", "exit 0")
    if diff_check["returncode"] != 0:
        add_gate_signal(gate_signals, "FAIL", "diff check", "failed", "non-zero exit")
        failures.append("git diff --check failed")
    else:
        add_gate_signal(gate_signals, "SUCCESS", "diff check", "executed", "exit 0")
    if vibeguard["returncode"] != 0:
        add_gate_signal(gate_signals, "FAIL", "VibeGuard", "failed", "non-zero exit")
        failures.append("final VibeGuard audit failed")

    overall = vibeguard["overall"]["status"]
    if vibeguard["returncode"] != 0:
        pass
    elif overall != "Ready" and not args.allow_vibeguard_review:
        add_gate_signal(gate_signals, "FAIL", "VibeGuard", "blocked", overall)
        failures.append(
            "final VibeGuard is not Ready; report the state and pass "
            "--allow-vibeguard-review with a reason if the review is acceptable"
        )
    elif overall != "Ready":
        add_gate_signal(
            gate_signals,
            "SUCCESS",
            "VibeGuard",
            "review accepted",
            args.allow_vibeguard_review or overall,
        )
    else:
        add_gate_signal(gate_signals, "SUCCESS", "VibeGuard", "executed", overall)

    retrospective_required = bool(missed_gates)
    if retrospective_required:
        failures.append(
            "retrospective required before final report, commit, release, or handoff"
        )

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook_root": str(playbook_root),
        "project": str(project),
        "rules": str(rules),
        "preflight_evidence": str(evidence_path),
        "request_intake": request_intake,
        "request_classification": request_classification,
        "required_gates": required_gates,
        "gate_evidence": gate_evidence,
        "gate_signals": gate_signals,
        "missed_gates": missed_gates,
        "question_drill_required": question_drill_required,
        "retrospective_required": retrospective_required,
        "allow_vibeguard_review": args.allow_vibeguard_review,
        "validate": validate,
        "diff_check": diff_check,
        "vibeguard": vibeguard,
        "failures": failures,
    }
    write_json(output_path, result)

    print(f"Finish evidence: {output_path}")
    print(f"Required gates: {required_gates}")
    print(f"VibeGuard overall: {overall}")
    print(f"Retrospective required: {str(retrospective_required).lower()}")
    print("Gate signals:")
    for gate_signal in gate_signals:
        print(
            f"- {display_signal(gate_signal['signal'])} | gate: {gate_signal['gate']} | "
            f"status: {gate_signal['status']}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
