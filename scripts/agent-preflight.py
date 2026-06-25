#!/usr/bin/env python3
"""Create executable preflight evidence for AgentPlaybook tasks."""

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

from agent_global_lessons import lesson_summary
from agent_preflight_runtime import (
    active_runtime_label,
    agy_runtime_bridge_issue,
    check_agent_hooks,
)
from agent_preflight_spill import write_spill_label


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


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


def route_command(args: argparse.Namespace, playbook_root: Path) -> list[str]:
    command = [
        sys.executable,
        str(playbook_root / "scripts" / "workflow.py"),
        "route",
        args.command,
        "--format",
        "json",
    ]
    if args.request_classified:
        command.append("--request-classified")
    else:
        command.extend(["--request", args.request])
    for platform in args.platform:
        command.extend(["--platform", platform])
    for concern in args.concern:
        command.extend(["--concern", concern])
    return command


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser(playbook_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run route, git status, and VibeGuard before agent work."
    )
    parser.add_argument("--command", required=True, help="workflow.py route command")
    request_group = parser.add_mutually_exclusive_group(required=True)
    request_group.add_argument("--request", help="current user request")
    request_group.add_argument(
        "--request-classified",
        action="store_true",
        help="use only after request classification or answer-first handling",
    )
    parser.add_argument(
        "--classification-evidence",
        help=(
            "required with --request-classified; describes the prior "
            "classification or answer-first handling"
        ),
    )
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--concern", action="append", default=[])
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--rules", type=Path, default=playbook_root)
    parser.add_argument("--evidence", type=Path)
    return parser


def resolve_evidence_path(args: argparse.Namespace, project: Path) -> Path:
    return (
        args.evidence.resolve()
        if args.evidence
        else project / ".agentplaybook" / "preflight.json"
    )


def request_intake(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "request": args.request or "",
        "request_classified": args.request_classified,
        "classification_evidence": args.classification_evidence or "",
    }


def write_early_bridge_failure(
    args: argparse.Namespace,
    playbook_root: Path,
    project: Path,
    rules: Path,
    evidence_path: Path,
    failure: str,
) -> int:
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook_root": str(playbook_root),
        "project": str(project),
        "rules": str(rules),
        "request_intake": request_intake(args),
        "early_runtime_bridge_failure": failure,
    }
    write_json(evidence_path, evidence)
    print(f"Preflight evidence: {evidence_path}")
    print(f"FAIL: {failure}", file=sys.stderr)
    return 1


def parse_route_payload(route_result: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    if route_result["returncode"] != 0:
        return None, ""
    try:
        return json.loads(route_result["stdout"]), ""
    except json.JSONDecodeError as error:
        return None, str(error)


def collect_failures(
    route_result: dict[str, Any],
    route_payload: dict[str, Any] | None,
    route_parse_error: str,
    git_status: dict[str, Any],
    vibeguard: dict[str, Any],
    hook_failures: list[str],
) -> list[str]:
    failures: list[str] = []
    if route_result["returncode"] != 0:
        failures.append("workflow route failed")
    elif route_parse_error:
        failures.append("workflow route output was not valid JSON")
    elif route_payload and route_payload.get("missing"):
        failures.append("workflow route reported missing documents")
    if git_status["returncode"] != 0:
        failures.append("git status failed")
    if vibeguard["returncode"] != 0:
        failures.append("VibeGuard audit failed")
    failures.extend(hook_failures)
    return failures


def run_preflight(args: argparse.Namespace, playbook_root: Path) -> int:
    project = args.project.resolve()
    rules = args.rules.resolve()
    evidence_path = resolve_evidence_path(args, project)

    early_bridge_failure = ""
    if active_runtime_label() == "antigravity":
        early_bridge_failure = agy_runtime_bridge_issue(playbook_root)
    if early_bridge_failure:
        return write_early_bridge_failure(
            args,
            playbook_root,
            project,
            rules,
            evidence_path,
            early_bridge_failure,
        )

    route_result = run_command(route_command(args, playbook_root), project)
    route_payload, route_parse_error = parse_route_payload(route_result)
    git_status = run_command(["git", "status", "--short", "--untracked-files=all"], project)
    vibeguard = run_command(vibeguard_command(project, rules), project)
    vibeguard["overall"] = parse_overall(vibeguard["stdout"] + "\n" + vibeguard["stderr"])
    global_lessons = lesson_summary()

    write_json(evidence_path, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook_root": str(playbook_root),
        "project": str(project),
        "rules": str(rules),
        "request_intake": request_intake(args),
        "route": route_payload,
        "route_parse_error": route_parse_error,
        "route_command": route_result,
        "git_status": git_status,
        "vibeguard": vibeguard,
        "global_lessons": global_lessons,
    })

    hook_warnings, hook_failures = check_agent_hooks(playbook_root)
    failures = collect_failures(
        route_result,
        route_payload,
        route_parse_error,
        git_status,
        vibeguard,
        hook_failures,
    )

    print(f"Preflight evidence: {evidence_path}")
    if route_payload:
        print(f"Route: {route_payload.get('command')} gates={route_payload.get('gates')}")
    print(f"VibeGuard overall: {vibeguard['overall']['status']}")
    print(
        "Global lessons: "
        f"accepted={len(global_lessons['accepted'])} "
        f"promoted={len(global_lessons['promoted'])} "
        f"candidates={global_lessons['candidate_count']}"
    )
    for warning in hook_warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    write_spill_label("analysis", "classify")
    playbook_root = Path(__file__).resolve().parents[1]
    parser = build_parser(playbook_root)
    args = parser.parse_args()
    if args.request_classified and not args.classification_evidence:
        parser.error(
            "--request-classified requires --classification-evidence so request "
            "intake cannot be skipped silently"
        )
    return run_preflight(args, playbook_root)


if __name__ == "__main__":
    sys.exit(main())
