#!/usr/bin/env python3
"""Run the three essential AgentPlaybook hooks.

Hooks intentionally expose only two outcomes: SUCCESS or FAIL. Details explain
why, but callers should treat any non-zero exit as blocking.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from agent_handoff_hook import handoff_hook
from agent_hook_gate_records import (
    gate_batch_hook,
    gate_hook,
    preflight_evidence_path,
)
from agent_hook_runtime import (
    REVIEW_CHANGED_PATH_LIMIT,
    existing_path,
    finish_with_result,
    git_status,
    non_negative_int,
    parse_overall,
    print_status,
    retry_attempt,
    run_command,
    vibeguard_command,
)
from agent_inprocess import run_script_main
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
        if args.request:
            command.extend(["--request", args.request])
    else:
        command.extend(["--request", args.request])
    for platform in args.platform:
        command.extend(["--platform", platform])
    for concern in args.concern:
        command.extend(["--concern", concern])
    if args.evidence:
        command.extend(["--evidence", str(args.evidence)])
    if args.worker_reservation_token:
        command.extend(["--worker-reservation-token", args.worker_reservation_token])

    result = run_script_main(ROOT / "scripts" / "agent-preflight.py", command, args.project)
    success = result["returncode"] == 0
    details = ["preflight completed" if success else "preflight failed"]
    details.extend(_summary_lines(result))
    if success:
        details.extend(_hook_summary_from_preflight(preflight_evidence_path(args)))
        capsule_detail = _start_capsule_detail(args)
        if capsule_detail:
            details.append(capsule_detail)
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


def _start_capsule_detail(args: argparse.Namespace) -> str:
    """Describe the lazy parent-to-worker capsule boundary."""

    _ = args
    return "execution capsule creation deferred until a worker handoff"


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


def _summary_lines(result: dict[str, Any]) -> list[str]:
    # FAIL lines must never be dropped: hiding some failures makes fixed
    # reruns surface "new" complaints that were failing all along.
    info_lines: list[str] = []
    fail_lines: list[str] = []
    for stream in ("stdout", "stderr"):
        for line in result.get(stream, "").splitlines():
            stripped = line.strip()
            if stripped.startswith("FAIL:"):
                fail_lines.append(stripped)
            elif stripped.startswith((
                "Route:",
                "Required hooks:",
                "Conditional hooks:",
                "VibeGuard overall:",
                "Required gates:",
                "Retrospective required:",
                "Retrospective lesson candidate:",
                "Global lessons:",
                "- routed doc candidates:",
                "- on-demand reference docs:",
            )):
                info_lines.append(stripped)
    return info_lines[:8] + fail_lines


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "hook",
        choices=("start", "handoff", "gate", "gate-batch", "review", "finish"),
    )
    parser.add_argument("--project", type=existing_path, default=Path.cwd())
    parser.add_argument("--rules", type=existing_path, default=ROOT)
    parser.add_argument(
        "--output",
        type=existing_path,
        help="hook evidence output for start, handoff, review, or finish",
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
    start.add_argument("--request", help="current user request")
    start.add_argument(
        "--request-classified",
        action="store_true",
        help="mark the request as already resolved; also pass --request so handoffs can reuse its capsule",
    )
    start.add_argument("--classification-evidence", default="")
    start.add_argument("--platform", action="append", default=[])
    start.add_argument("--concern", action="append", default=[])
    start.add_argument(
        "--worker-reservation-token",
        default="",
        help="opaque token issued by the parent handoff for a fallback worker start",
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
    _add_review_arguments(parser)
    _add_finish_arguments(parser)
    _add_gate_arguments(parser)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    worker_error = _apply_worker_evidence_boundary(args)
    if worker_error:
        print_status(args.hook, False, [worker_error])
        return 2
    if args.hook == "start":
        if args.request_classified and not args.classification_evidence:
            parser.error("start --request-classified requires --classification-evidence")
        if not args.request:
            parser.error(
                "start requires --request; for resolved requests, keep --request and add "
                "--request-classified with --classification-evidence"
            )
        return start_hook(args)
    if args.hook == "review":
        args.review_path = [path.strip() for path in args.review_path if path.strip()]
        if args.review_path and args.review_scope == "working-tree":
            args.review_scope = "pathspec"
        if args.review_scope == "pathspec" and not args.review_path:
            parser.error("review --review-scope pathspec requires at least one --review-path")
        return review_hook(args, run_command, git_status, vibeguard_command, parse_overall, finish_with_result)
    if args.hook == "handoff":
        return handoff_hook(args)
    if args.hook == "gate":
        if not args.gate_name:
            parser.error("gate requires --gate-name")
        return gate_hook(args)
    if args.hook == "gate-batch":
        return gate_batch_hook(args)
    return finish_hook(args)


def _apply_worker_evidence_boundary(args: argparse.Namespace) -> str:
    if os.environ.get("AGENTPLAYBOOK_PARENT_EVIDENCE_READONLY") == "1":
        return "reusable worker capsule cannot run lifecycle hooks that write parent evidence"
    expected = os.environ.get("AGENTPLAYBOOK_WORKER_EVIDENCE")
    if not expected:
        return ""
    expected_path = Path(expected).expanduser().resolve()
    if args.evidence and args.evidence.resolve() != expected_path:
        return "worker lifecycle must use the launcher-issued isolated evidence path"
    args.evidence = expected_path
    return ""


if __name__ == "__main__":
    sys.exit(main())
