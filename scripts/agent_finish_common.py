"""Shared helpers for Tao Agent OS finish checks."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
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


def requires_retrospective(
    missed_gates: list[str],
    gate_policy_failures: list[str],
    finish_failures: list[str],
) -> bool:
    return bool(missed_gates or gate_policy_failures or finish_failures)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
