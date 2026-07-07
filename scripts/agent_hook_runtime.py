"""Runtime helpers shared by the AgentPlaybook hook CLI."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
            "next_action": "retrospective_then_retry_once",
            "recovery_required": "actionable_retrospective",
        }, [
            "recovery request: diagnose every failure, run an actionable retrospective for this "
            "failed scope, record the immediate correction plan, apply scoped and safe fixes "
            "outside the hook, then rerun this hook once with --retry-attempt 1 and cite or "
            "apply that plan",
        ]
    return {
        "retry_attempt": retry_attempt,
        "retry_limit": HOOK_RETRY_LIMIT,
        "next_action": "stop_after_retrospective_retry_failed",
        "recovery_required": "promote_or_handoff_lesson",
    }, [
        "stop request: retry limit reached after the recovery attempt; promote the retrospective "
        "lesson or hand off the blocker before continuing",
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
