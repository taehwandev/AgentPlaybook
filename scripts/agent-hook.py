#!/usr/bin/env python3
"""Run the three essential AgentPlaybook hooks.

Hooks intentionally expose only two outcomes: SUCCESS or FAIL. Details explain
why, but callers should treat any non-zero exit as blocking.
"""

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

from agent_review_hook import review_hook
from agent_review_structure import (
    REVIEW_FUNCTION_LINE_LIMIT,
    REVIEW_SOURCE_FILE_LINE_LIMIT,
)


ROOT = Path(__file__).resolve().parents[1]
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
HOOK_RETRY_LIMIT = 1
REVIEW_CHANGED_PATH_LIMIT = 25


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


def parse_overall(output: str) -> str:
    for raw_line in clean_output(output).splitlines():
        line = raw_line.strip()
        if line.startswith("Overall:"):
            value = line.split("Overall:", 1)[1].strip()
            if "Ready" in value:
                return "Ready"
            if "Needs review" in value:
                return "Needs review"
            if "Blocked" in value:
                return "Blocked"
            return value or "unknown"
    return "unknown"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_status(name: str, success: bool, details: list[str]) -> None:
    print(f"{'SUCCESS' if success else 'FAIL'} {name}")
    for detail in details:
        print(f"- {detail}")


def git_status(project: Path) -> tuple[dict[str, Any], list[str]]:
    result = run_command(["git", "status", "--short", "--untracked-files=all"], project)
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    return result, lines


def start_hook(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "agent-preflight.py"),
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

    result = run_command(command, args.project)
    success = result["returncode"] == 0
    details = ["preflight completed" if success else "preflight failed"]
    details.extend(_summary_lines(result))
    if success:
        details.extend(_hook_summary_from_preflight(_preflight_evidence_path(args)))
    return finish_with_result(
        "start",
        success,
        details,
        args.output,
        {"preflight": result},
        args.retry_attempt,
    )


def _preflight_evidence_path(args: argparse.Namespace) -> Path:
    return args.evidence if args.evidence else args.project / ".agentplaybook" / "preflight.json"


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
        sys.executable,
        str(ROOT / "scripts" / "agent-finish-check.py"),
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

    result = run_command(command, args.project)
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
            )):
                lines.append(stripped)
    return lines[:8]


def finish_with_result(
    name: str,
    success: bool,
    details: list[str],
    output: Path | None,
    payload: dict[str, Any],
    retry_attempt: int,
) -> int:
    policy, policy_details = hook_failure_policy(success, retry_attempt)
    details = [*details, *policy_details]
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hook": name,
        "status": "SUCCESS" if success else "FAIL",
        "policy": policy,
        "details": details,
        **payload,
    }
    if output:
        write_json(output, evidence)
    print_status(name, success, details)
    return 0 if success else 1


def hook_failure_policy(success: bool, retry_attempt: int) -> tuple[dict[str, Any], list[str]]:
    if success:
        return {
            "retry_attempt": retry_attempt,
            "retry_limit": HOOK_RETRY_LIMIT,
            "next_action": "continue",
        }, []
    if retry_attempt < HOOK_RETRY_LIMIT:
        return {
            "retry_attempt": retry_attempt,
            "retry_limit": HOOK_RETRY_LIMIT,
            "next_action": "retry_once",
        }, [
            "retry request: diagnose every failure, fix scoped and safe issues outside the hook, "
            "then rerun this hook once with --retry-attempt 1",
        ]
    return {
        "retry_attempt": retry_attempt,
        "retry_limit": HOOK_RETRY_LIMIT,
        "next_action": "retrospective_required",
    }, [
        "retrospective required: retry limit reached; run workflows/retrospective-learning.md before handoff",
    ]


def existing_path(value: str) -> Path:
    return Path(value).resolve()


def retry_attempt(value: str) -> int:
    attempt = int(value)
    if attempt < 0 or attempt > HOOK_RETRY_LIMIT:
        raise argparse.ArgumentTypeError(f"retry attempt must be 0 or {HOOK_RETRY_LIMIT}")
    return attempt


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run essential AgentPlaybook hooks.")
    parser.add_argument("hook", choices=("start", "review", "finish"))
    parser.add_argument("--project", type=existing_path, default=Path.cwd())
    parser.add_argument("--rules", type=existing_path, default=ROOT)
    parser.add_argument("--output", type=existing_path)
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

    start = parser.add_argument_group("start hook")
    start.add_argument("--command", default="task", help="workflow route command for start")
    start_request = start.add_mutually_exclusive_group()
    start_request.add_argument("--request", help="current user request")
    start_request.add_argument("--request-classified", action="store_true")
    start.add_argument("--classification-evidence", default="")
    start.add_argument("--platform", action="append", default=[])
    start.add_argument("--concern", action="append", default=[])

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

    finish = parser.add_argument_group("finish hook")
    finish.add_argument("--gate", action="append", default=[])
    finish.add_argument("--allow-vibeguard-review")
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
        return review_hook(args, run_command, git_status, vibeguard_command, parse_overall, finish_with_result)
    return finish_hook(args)


if __name__ == "__main__":
    sys.exit(main())
