"""Final validation, diff, and VibeGuard checks for finish-check."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from agent_finish_common import add_gate_signal, parse_overall, run_command, vibeguard_command


def run_final_checks(
    playbook_root: Path,
    project: Path,
    rules: Path,
    allow_vibeguard_review: str | None,
    gate_signals: list[dict[str, str]],
    failures: list[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    validate = run_command(
        [sys.executable, str(playbook_root / "scripts" / "workflow.py"), "validate"],
        playbook_root,
    )
    diff_check = run_command(["git", "diff", "--check"], project)
    vibeguard = run_command(vibeguard_command(project, rules), project)
    vibeguard["overall"] = parse_overall(vibeguard["stdout"] + "\n" + vibeguard["stderr"])
    _record_final_check_signals(validate, diff_check, vibeguard, allow_vibeguard_review, gate_signals, failures)
    return validate, diff_check, vibeguard, vibeguard["overall"]["status"]


def _record_final_check_signals(
    validate: dict[str, Any],
    diff_check: dict[str, Any],
    vibeguard: dict[str, Any],
    allow_vibeguard_review: str | None,
    gate_signals: list[dict[str, str]],
    failures: list[str],
) -> None:
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
    _record_vibeguard_signal(vibeguard, allow_vibeguard_review, gate_signals, failures)


def _record_vibeguard_signal(
    vibeguard: dict[str, Any],
    allow_vibeguard_review: str | None,
    gate_signals: list[dict[str, str]],
    failures: list[str],
) -> None:
    overall = vibeguard["overall"]["status"]
    if vibeguard["returncode"] != 0:
        add_gate_signal(gate_signals, "FAIL", "VibeGuard", "failed", "non-zero exit")
        failures.append("final VibeGuard audit failed")
    elif overall != "Ready" and not allow_vibeguard_review:
        add_gate_signal(gate_signals, "FAIL", "VibeGuard", "blocked", overall)
        failures.append(
            "final VibeGuard is not Ready; report the state and pass "
            "--allow-vibeguard-review with a reason if the review is acceptable"
        )
    elif overall != "Ready":
        add_gate_signal(gate_signals, "SUCCESS", "VibeGuard", "review accepted", allow_vibeguard_review or overall)
    else:
        add_gate_signal(gate_signals, "SUCCESS", "VibeGuard", "executed", overall)
