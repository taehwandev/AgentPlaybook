#!/usr/bin/env python3
"""Create executable preflight evidence for AgentPlaybook tasks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_BASELINE_HOOK_RE = re.compile(r"workflow\.py.*route.*triage.*--request-classified")
_AGENTPLAYBOOK_PYTHON_SCRIPT_NAMES = (
    "workflow.py",
    "agent-preflight.py",
    "agent-finish-check.py",
)


def _check_agent_hooks(playbook_root: Path) -> list[str]:
    """Return warning strings for any missing runtime hook registrations."""
    warnings: list[str] = []

    claude_settings = Path.home() / ".claude" / "settings.json"
    if claude_settings.exists():
        try:
            config = json.loads(claude_settings.read_text())
            groups = config.get("hooks", {}).get("UserPromptSubmit", [])
            has_baseline = any(
                _BASELINE_HOOK_RE.search(h.get("command", ""))
                for g in groups
                for h in g.get("hooks", [])
            )
            if not has_baseline:
                warnings.append(
                    "Claude Code UserPromptSubmit baseline label hook is missing. "
                    f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
                )
            spill_tool = config.get("env", {}).get("SPILL_AI_TOOL", "")
            if spill_tool != "claude":
                warnings.append(
                    "env.SPILL_AI_TOOL is not set to 'claude' in ~/.claude/settings.json. "
                    f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
                )
            missing_permissions = _missing_allow_entries(
                config,
                _claude_permission_entries(playbook_root),
            )
            if missing_permissions:
                warnings.append(
                    "Claude Code AgentPlaybook Python permissions are missing. "
                    f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
                )
        except (json.JSONDecodeError, OSError):
            pass

    agy_targets = [
        Path.home() / ".gemini" / "config" / "config.json",
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
    ]
    agy_entries = _agy_permission_entries(playbook_root)
    agy_configs = []
    for target in agy_targets:
        if not target.exists():
            continue
        try:
            data = json.loads(target.read_text())
            if isinstance(data, dict):
                agy_configs.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    if agy_configs and not any(
        not _missing_allow_entries(config, agy_entries)
        for config in agy_configs
    ):
        warnings.append(
            "AGY AgentPlaybook Python permissions are missing from AGY config. "
            f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )

    return warnings


def _claude_permission_entries(playbook_root: Path) -> list[str]:
    entries: list[str] = []
    for name in _AGENTPLAYBOOK_PYTHON_SCRIPT_NAMES:
        script = playbook_root / "scripts" / name
        entries.append(f"Bash(python3 {script}:*)")
        entries.append(f"Bash(python3 {_quote(str(script))}:*)")
        entries.append(f"Bash(python3 scripts/{name}:*)")
    return entries


def _agy_permission_entries(playbook_root: Path) -> list[str]:
    entries: list[str] = []
    for name in _AGENTPLAYBOOK_PYTHON_SCRIPT_NAMES:
        script = playbook_root / "scripts" / name
        entries.append(f"command(python3 {script})")
        entries.append(f"command(python3 {_quote(str(script))})")
        entries.append(f"command(python3 scripts/{name})")
    return entries


def _missing_allow_entries(config: dict[str, Any], entries: list[str]) -> list[str]:
    permissions = config.get("permissions")
    if not isinstance(permissions, dict):
        return entries
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        return entries
    return [entry for entry in entries if entry not in allow]


def _quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


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


def main() -> int:
    playbook_root = Path(__file__).resolve().parents[1]
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
    args = parser.parse_args()
    if args.request_classified and not args.classification_evidence:
        parser.error(
            "--request-classified requires --classification-evidence so request "
            "intake cannot be skipped silently"
        )

    project = args.project.resolve()
    rules = args.rules.resolve()
    evidence_path = (
        args.evidence.resolve()
        if args.evidence
        else project / ".agentplaybook" / "preflight.json"
    )

    route_result = run_command(route_command(args, playbook_root), project)
    route_payload: dict[str, Any] | None = None
    route_parse_error = ""
    if route_result["returncode"] == 0:
        try:
            route_payload = json.loads(route_result["stdout"])
        except json.JSONDecodeError as error:
            route_parse_error = str(error)

    git_status = run_command(
        ["git", "status", "--short", "--untracked-files=all"],
        project,
    )
    vibeguard = run_command(
        [
            "npx",
            "--yes",
            "@taehwandev/vibeguard",
            "audit",
            str(project),
            "--rules",
            str(rules),
        ],
        project,
    )
    vibeguard_output = vibeguard["stdout"] + "\n" + vibeguard["stderr"]
    vibeguard["overall"] = parse_overall(vibeguard_output)

    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playbook_root": str(playbook_root),
        "project": str(project),
        "rules": str(rules),
        "request_intake": {
            "request": args.request or "",
            "request_classified": args.request_classified,
            "classification_evidence": args.classification_evidence or "",
        },
        "route": route_payload,
        "route_parse_error": route_parse_error,
        "route_command": route_result,
        "git_status": git_status,
        "vibeguard": vibeguard,
    }
    write_json(evidence_path, evidence)

    hook_warnings = _check_agent_hooks(playbook_root)

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

    print(f"Preflight evidence: {evidence_path}")
    if route_payload:
        print(f"Route: {route_payload.get('command')} gates={route_payload.get('gates')}")
    print(f"VibeGuard overall: {vibeguard['overall']['status']}")
    for warning in hook_warnings:
        print(f"WARN: {warning}", file=sys.stderr)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
