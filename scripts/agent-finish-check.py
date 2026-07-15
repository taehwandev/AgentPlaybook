#!/usr/bin/env python3
"""Verify AgentPlaybook gate evidence before final report, commit, or handoff."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_delegation_plan import read_delegation_plan
from agent_global_lessons import write_retrospective_candidate
from agent_finish_check_steps import (
    check_preflight_vibeguard,
    check_request_intake,
    check_required_gates,
    read_preflight,
    resolve_paths,
    route_gate_capsule_binding_failures,
)
from agent_finish_common import (
    add_gate_signal,
    display_signal,
    parse_gate,
    requires_retrospective,
    write_json,
)
from agent_finish_final_checks import run_final_checks
from agent_gate_evidence import (
    incomplete_gate_evidence_failures,
    merge_gate_evidence_from_ledger,
    record_cli_gate_evidence,
)


def build_parser(playbook_root: Path) -> argparse.ArgumentParser:
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
    return parser


def build_result(
    *,
    playbook_root: Path,
    project: Path,
    rules: Path,
    evidence_path: Path,
    args: argparse.Namespace,
    preflight: dict[str, Any],
    required_gates: list[str],
    gate_evidence: dict[str, str],
    gate_signals: list[dict[str, str]],
    missed_gates: list[str],
    gate_evidence_ledger: dict[str, Any],
    delegation_plan: dict[str, Any],
    grill_me_required: bool,
    retrospective_required: bool,
    validate: dict[str, Any],
    diff_check: dict[str, Any],
    vibeguard: dict[str, Any],
    retrospective_lesson: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    route = preflight.get("route") or {}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook_root": str(playbook_root),
        "project": str(project),
        "rules": str(rules),
        "preflight_evidence": str(evidence_path),
        "request_intake": preflight.get("request_intake") or {},
        "request_classification": route.get("request_classification") or {},
        "required_gates": required_gates,
        "gate_evidence": gate_evidence,
        "gate_evidence_ledger": gate_evidence_ledger,
        "gate_signals": gate_signals,
        "missed_gates": missed_gates,
        "agent_delegation_plan": delegation_plan,
        "grill_me_required": grill_me_required,
        "question_drill_required": grill_me_required,
        "retrospective_required": retrospective_required,
        "allow_vibeguard_review": args.allow_vibeguard_review,
        "validate": validate,
        "diff_check": diff_check,
        "vibeguard": vibeguard,
        "retrospective_lesson": retrospective_lesson,
        "failures": failures,
    }


def print_result(output_path: Path, required_gates: list[str], overall: str, result: dict[str, Any]) -> None:
    print(f"Finish evidence: {output_path}")
    print(f"Required gates: {required_gates}")
    print(f"VibeGuard overall: {overall}")
    print(f"Retrospective required: {str(result['retrospective_required']).lower()}")
    lesson = result.get("retrospective_lesson") or {}
    if lesson.get("created"):
        print(f"Retrospective lesson candidate: {lesson.get('relative_path')}")
    elif result["retrospective_required"]:
        print(f"Retrospective lesson candidate: {lesson.get('reason', 'not_created')}")
    print("Gate signals:")
    for gate_signal in result["gate_signals"]:
        print(
            f"- {display_signal(gate_signal['signal'])} | gate: {gate_signal['gate']} | "
            f"status: {gate_signal['status']}"
        )


def main() -> int:
    playbook_root = Path(__file__).resolve().parents[1]
    args = build_parser(playbook_root).parse_args()
    worker_error = _apply_worker_evidence_boundary(args)
    if worker_error:
        print(f"FAIL: {worker_error}", file=sys.stderr)
        return 2
    project, rules, evidence_path, output_path = resolve_paths(args)
    failures: list[str] = []
    preflight = read_preflight(evidence_path, failures)
    route = preflight.get("route") or {}
    cli_gate_evidence = dict(args.gate)
    if cli_gate_evidence and preflight:
        try:
            record_cli_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                cli_gate_evidence=cli_gate_evidence,
            )
        except (OSError, ValueError) as error:
            failures.append(f"finish CLI gate evidence could not be recorded: {error}")
    delegation_plan = read_delegation_plan(project)
    gate_evidence, gate_evidence_ledger = merge_gate_evidence_from_ledger(
        route=route,
        evidence_path=evidence_path,
        cli_gate_evidence={},
    )
    failures.extend(incomplete_gate_evidence_failures(gate_evidence_ledger))
    gate_signals: list[dict[str, str]] = []
    required_gates, missed_gates, gate_policy_failures = check_required_gates(
        route,
        gate_evidence,
        gate_signals,
        failures,
        delegation_plan,
    )
    capsule_binding_failures = route_gate_capsule_binding_failures(
        route,
        project,
        rules,
        evidence_path,
        gate_evidence,
        gate_evidence_ledger,
    )
    for failure in capsule_binding_failures:
        add_gate_signal(gate_signals, "FAIL", "execution capsule", "failed", failure)
        failures.append(failure)
    gate_policy_failures.extend(capsule_binding_failures)
    grill_me_required = check_request_intake(
        route,
        preflight.get("request_intake") or {},
        route.get("request_classification") or {},
        gate_evidence,
        gate_signals,
        missed_gates,
        failures,
    )
    check_preflight_vibeguard(preflight, failures)
    validate, diff_check, vibeguard, overall = run_final_checks(
        playbook_root,
        project,
        rules,
        args.allow_vibeguard_review,
        gate_signals,
        failures,
    )
    finish_failures_before_retrospective = list(failures)
    retrospective_required = requires_retrospective(
        missed_gates,
        gate_policy_failures,
        finish_failures_before_retrospective,
    )
    if retrospective_required:
        failures.append(
            "retrospective required before retry, final report, commit, release, or handoff; "
            "record the immediate correction plan, apply safe scoped fixes, then resume at the "
            "first missed gate or same failed scope"
        )
    retrospective_lesson = write_retrospective_candidate(
        {
            "missed_gates": missed_gates,
            "gate_signals": gate_signals,
            "retrospective_required": retrospective_required,
        }
    )

    result = build_result(
        playbook_root=playbook_root,
        project=project,
        rules=rules,
        evidence_path=evidence_path,
        args=args,
        preflight=preflight,
        required_gates=required_gates,
        gate_evidence=gate_evidence,
        gate_signals=gate_signals,
        missed_gates=missed_gates,
        gate_evidence_ledger=gate_evidence_ledger,
        delegation_plan=delegation_plan,
        grill_me_required=grill_me_required,
        retrospective_required=retrospective_required,
        validate=validate,
        diff_check=diff_check,
        vibeguard=vibeguard,
        retrospective_lesson=retrospective_lesson,
        failures=failures,
    )
    write_json(output_path, result)
    print_result(output_path, required_gates, overall, result)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


def _apply_worker_evidence_boundary(args: argparse.Namespace) -> str:
    if os.environ.get("AGENTPLAYBOOK_PARENT_EVIDENCE_READONLY") == "1":
        return "reusable worker capsule cannot run a finish check against parent evidence"
    expected = os.environ.get("AGENTPLAYBOOK_WORKER_EVIDENCE")
    if not expected:
        return ""
    expected_path = Path(expected).expanduser().resolve()
    if args.evidence and args.evidence.resolve() != expected_path:
        return "worker finish check must use the launcher-issued isolated evidence path"
    args.evidence = expected_path
    return ""


if __name__ == "__main__":
    sys.exit(main())
