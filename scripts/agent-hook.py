#!/usr/bin/env python3
"""Run the three essential AgentPlaybook hooks.

Hooks intentionally expose only two outcomes: SUCCESS or FAIL. Details explain
why, but callers should treat any non-zero exit as blocking.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from agent_hook_gate_records import (
    gate_batch_hook,
    gate_hook,
    preflight_evidence_path,
    record_hook_gate,
    reset_and_record_start_gate,
)
from agent_hook_runtime import (
    REVIEW_CHANGED_PATH_LIMIT,
    existing_path,
    finish_with_result,
    git_status,
    non_negative_int,
    parse_overall,
    retry_attempt,
    run_command,
    vibeguard_command,
)
from agent_inprocess import run_script_main
from agent_finish_gate_core_validators import validate_route_docs_application_fields
from agent_review_hook import review_hook
from agent_review_structure import (
    REVIEW_FUNCTION_LINE_LIMIT,
    REVIEW_SOURCE_FILE_LINE_LIMIT,
)


ROOT = Path(__file__).resolve().parents[1]


def start_hook(args: argparse.Namespace) -> int:
    command = [
        "--project",
        str(args.project),
        "--rules",
        str(args.rules),
        "--command",
        args.command,
    ]
    if args.request_classified:
        command.append("--request-classified")
        command.extend(["--classification-evidence", args.classification_evidence])
    else:
        command.extend(["--request", args.request])
    for platform in args.platform:
        command.extend(["--platform", platform])
    for concern in args.concern:
        command.extend(["--concern", concern])
    if args.evidence:
        command.extend(["--evidence", str(args.evidence)])

    result = run_script_main(ROOT / "scripts" / "agent-preflight.py", command, args.project)
    success = result["returncode"] == 0
    details = ["preflight completed" if success else "preflight failed"]
    details.extend(_summary_lines(result))
    if success:
        details.extend(_hook_summary_from_preflight(preflight_evidence_path(args)))
        reset_and_record_start_gate(args)
    return finish_with_result(
        "start",
        success,
        details,
        args.output,
        {"preflight": result},
        args.retry_attempt,
    )


def _hook_summary_from_preflight(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    hooks = (payload.get("route") or {}).get("hooks") or []
    required = [hook.get("hook") for hook in hooks if hook.get("required")]
    conditional = [hook.get("hook") for hook in hooks if not hook.get("required")]
    lines: list[str] = []
    if required:
        lines.append(f"Required hooks: {required}")
    if conditional:
        lines.append(f"Conditional hooks: {conditional}")
    return lines


def finish_hook(args: argparse.Namespace) -> int:
    command = [
        "--project",
        str(args.project),
        "--rules",
        str(args.rules),
    ]
    if args.evidence:
        command.extend(["--evidence", str(args.evidence)])
    for gate in args.gate:
        command.extend(["--gate", gate])
    if args.allow_vibeguard_review:
        command.extend(["--allow-vibeguard-review", args.allow_vibeguard_review])

    result = run_script_main(ROOT / "scripts" / "agent-finish-check.py", command, args.project)
    success = result["returncode"] == 0
    details = ["finish check completed" if success else "finish check failed"]
    details.extend(_summary_lines(result))
    return finish_with_result(
        "finish",
        success,
        details,
        args.output,
        {"finish_check": result},
        args.retry_attempt,
    )


def docs_read_hook(args: argparse.Namespace) -> int:
    command = [
        "--project",
        str(args.project),
        "--rules",
        str(args.rules),
    ]
    if args.evidence:
        command.extend(["--evidence", str(args.evidence)])
    receipt_output = args.receipt_output or args.output
    if receipt_output:
        command.extend(["--receipt-output", str(receipt_output)])

    result = run_script_main(ROOT / "scripts" / "agent-docs-read.py", command, args.project)
    success = result["returncode"] == 0
    details = ["route docs read receipt completed" if success else "route docs read receipt failed"]
    details.extend(_summary_lines(result))
    if success:
        application_failures = validate_route_docs_application_fields(
            args.takeaway or "",
            args.next_action or "",
        )
        if application_failures:
            details.append("route docs read gate evidence is incomplete")
            details.extend(f"required recovery: {failure}" for failure in application_failures)
            details.append(
                "rerun docs-read with --takeaway \"<doc-derived rule>\" "
                "--next-action \"<immediate task action>\""
            )
            success = False
    if success:
        record_hook_gate(
            args,
            "route docs read",
            "docs-read receipt completed",
            {
                "takeaway": args.takeaway or "",
                "next_action": args.next_action or "",
            },
            "docs-read",
        )
    return finish_with_result(
        "docs-read",
        success,
        details,
        None,
        {"docs_read": result},
        args.retry_attempt,
    )


def _summary_lines(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for stream in ("stdout", "stderr"):
        for line in result.get(stream, "").splitlines():
            stripped = line.strip()
            if stripped.startswith((
                "Route:",
                "Required hooks:",
                "Conditional hooks:",
                "VibeGuard overall:",
                "FAIL:",
                "Required gates:",
                "Retrospective required:",
                "Retrospective lesson candidate:",
                "Global lessons:",
                "SUCCESS docs-read",
                "- receipt:",
                "- required docs read:",
                "- routed doc candidates:",
                "- on-demand reference docs:",
            )):
                lines.append(stripped)
    return lines[:8]


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("hook", choices=("start", "docs-read", "gate", "gate-batch", "review", "finish"))
    parser.add_argument("--project", type=existing_path, default=Path.cwd())
    parser.add_argument("--rules", type=existing_path, default=ROOT)
    parser.add_argument(
        "--output",
        type=existing_path,
        help=(
            "hook evidence output for start/review/finish; legacy docs-read "
            "alias for --receipt-output"
        ),
    )
    parser.add_argument(
        "--receipt-output",
        type=existing_path,
        help="docs-read receipt path; use this instead of --output for docs-read",
    )
    parser.add_argument(
        "--evidence",
        type=existing_path,
        help="preflight evidence path; start writes it and finish reads it",
    )
    parser.add_argument(
        "--retry-attempt",
        type=retry_attempt,
        default=0,
        help="0 for the first hook run, 1 for the single allowed retry",
    )


def _add_start_arguments(parser: argparse.ArgumentParser) -> None:
    start = parser.add_argument_group("start hook")
    start.add_argument("--command", default="task", help="workflow route command for start")
    start_request = start.add_mutually_exclusive_group()
    start_request.add_argument("--request", help="current user request")
    start_request.add_argument("--request-classified", action="store_true")
    start.add_argument("--classification-evidence", default="")
    start.add_argument("--platform", action="append", default=[])
    start.add_argument("--concern", action="append", default=[])


def _add_docs_read_arguments(parser: argparse.ArgumentParser) -> None:
    docs_read = parser.add_argument_group("docs-read hook")
    docs_read.add_argument(
        "--takeaway",
        help="task-specific rule, criterion, policy, or takeaway applied from the required docs",
    )
    docs_read.add_argument(
        "--next-action",
        help="immediate next task action that applies the discovered docs",
    )


def _add_review_arguments(parser: argparse.ArgumentParser) -> None:
    review = parser.add_argument_group("review hook")
    review.add_argument(
        "--code-review-evidence",
        help="short evidence that the exact diff was reviewed against request and rules",
    )
    review.add_argument(
        "--docs-freshness-evidence",
        help="short evidence that affected docs were updated or intentionally unchanged",
    )
    review.add_argument(
        "--structure-review-evidence",
        help=(
            "short evidence that runtime file/function size, top-level owner count, and "
            "responsibility splits were reviewed; new runtime package boundaries must "
            "include owner, allowed imports, forbidden imports, callers/tests, and verification"
        ),
    )
    review.add_argument(
        "--boundary-plan-evidence",
        help="short evidence of the owned boundary/scope and nearest verification chosen before implementation",
    )
    review.add_argument(
        "--side-effect-audit-evidence",
        help="short evidence that the final diff and side-effect surfaces were checked",
    )
    review.add_argument(
        "--review-scope",
        choices=("working-tree", "pathspec"),
        default="working-tree",
        help="declare whether review covers the whole working tree or explicit --review-path pathspecs",
    )
    review.add_argument(
        "--review-path",
        action="append",
        default=[],
        help="limit review hook changed-path, diff, and structure checks to this pathspec; repeat as needed",
    )
    review.add_argument(
        "--max-changed-paths",
        type=non_negative_int,
        default=REVIEW_CHANGED_PATH_LIMIT,
        help="fail review when the changed path count is above this limit",
    )
    review.add_argument(
        "--max-source-file-lines",
        type=non_negative_int,
        default=REVIEW_SOURCE_FILE_LINE_LIMIT,
        help="fail review when a changed development source/style file is above this line count",
    )
    review.add_argument(
        "--max-function-lines",
        type=non_negative_int,
        default=REVIEW_FUNCTION_LINE_LIMIT,
        help="fail review when a changed function, class, component, or style block is above this line count",
    )


def _add_finish_arguments(parser: argparse.ArgumentParser) -> None:
    finish = parser.add_argument_group("finish hook")
    finish.add_argument("--gate", action="append", default=[])
    finish.add_argument("--allow-vibeguard-review")


def _add_gate_arguments(parser: argparse.ArgumentParser) -> None:
    gate = parser.add_argument_group("gate evidence hook")
    gate.add_argument("--gate-name", help="route gate name to record in the structured ledger")
    gate.add_argument("--status", choices=("SUCCESS", "FAIL"), default="SUCCESS")
    gate.add_argument("--source", default="manual")
    gate.add_argument("--gate-evidence", default="")
    gate.add_argument("--field", action="append", default=[], help="structured evidence field as key=value")
    gate.add_argument(
        "--gate-record",
        action="append",
        default=[],
        help="JSON object or array of objects with gate, evidence, fields, source, and status",
    )
    gate.add_argument(
        "--gate-json",
        type=existing_path,
        help="JSON file containing a gate evidence object or array of objects",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run essential AgentPlaybook hooks.")
    _add_common_arguments(parser)
    _add_start_arguments(parser)
    _add_docs_read_arguments(parser)
    _add_review_arguments(parser)
    _add_finish_arguments(parser)
    _add_gate_arguments(parser)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.hook == "start":
        if args.request_classified and not args.classification_evidence:
            parser.error("start --request-classified requires --classification-evidence")
        if not args.request_classified and not args.request:
            parser.error("start requires --request or --request-classified")
        return start_hook(args)
    if args.hook == "review":
        args.review_path = [path.strip() for path in args.review_path if path.strip()]
        if args.review_path and args.review_scope == "working-tree":
            args.review_scope = "pathspec"
        if args.review_scope == "pathspec" and not args.review_path:
            parser.error("review --review-scope pathspec requires at least one --review-path")
        return review_hook(args, run_command, git_status, vibeguard_command, parse_overall, finish_with_result)
    if args.hook == "docs-read":
        return docs_read_hook(args)
    if args.hook == "gate":
        if not args.gate_name:
            parser.error("gate requires --gate-name")
        return gate_hook(args)
    if args.hook == "gate-batch":
        return gate_batch_hook(args)
    return finish_hook(args)


if __name__ == "__main__":
    sys.exit(main())
