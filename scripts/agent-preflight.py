#!/usr/bin/env python3
"""Create executable preflight evidence for AgentPlaybook tasks."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_BASELINE_HOOK_RE = re.compile(r"workflow\.py.*route.*triage.*--request-classified")
AGY_RUNTIME_BRIDGE_PATH = Path.home() / ".antigravity" / "AGENTS.md"
AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES = [
    "Antigravity reads AGENTS.md",
    "Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
    "Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
    "If this bridge or the project-root AGENTS.md cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
]


DEFAULT_SPILL_SETUP_HELPER = (
    Path.home()
    / "Library/Application Support/Spill/adapters/setup/spill-token-metering-setup.mjs"
)
SPILL_ALLOWED_TOOLS = {"codex", "claude", "antigravity", "openai"}


def spill_tool_label() -> str:
    tool = (
        os.environ.get("SPILL_AI_TOOL")
        or os.environ.get("SPILL_TOKEN_USAGE_AI_TOOL")
        or "codex"
    ).strip().lower()
    return tool if tool in SPILL_ALLOWED_TOOLS else "codex"


def write_spill_label(task_type: str, stage: str) -> None:
    if not _has_spill_setup_helper():
        return
    try:
        subprocess.run(
            [
                "node",
                str(_spill_setup_helper_path()),
                "--label",
                spill_tool_label(),
                "--task-type",
                task_type,
                "--stage",
                stage,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def _spill_setup_helper_path() -> Path:
    override = os.environ.get("AGENTPLAYBOOK_SPILL_HELPER_PATH", "")
    return Path(override) if override else DEFAULT_SPILL_SETUP_HELPER


def _has_spill_setup_helper() -> bool:
    return _spill_setup_helper_path().is_file()


def _check_agent_hooks(playbook_root: Path) -> tuple[list[str], list[str]]:
    """Return warning and failure strings for missing runtime registrations."""
    warnings: list[str] = []
    failures: list[str] = []
    spill_available = _has_spill_setup_helper()

    codex_rules = Path.home() / ".codex" / "rules" / "default.rules"
    if codex_rules.exists():
        try:
            missing_permissions = _missing_text_entries(
                codex_rules.read_text(),
                _codex_prefix_rule_entries(playbook_root),
            )
            if missing_permissions:
                warnings.append(
                    "Codex AgentPlaybook Python prefix rules are missing. "
                    f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
                )
        except OSError:
            pass

    claude_settings = Path.home() / ".claude" / "settings.json"
    if claude_settings.exists():
        try:
            config = json.loads(claude_settings.read_text())
            if spill_available:
                groups = config.get("hooks", {}).get("UserPromptSubmit", [])
                has_baseline = any(
                    _BASELINE_HOOK_RE.search(h.get("command", ""))
                    and "SPILL_AI_TOOL=claude" in h.get("command", "")
                    for g in groups
                    for h in g.get("hooks", [])
                )
                if not has_baseline:
                    warnings.append(
                        "Claude Code UserPromptSubmit Spill workflow label hook is missing. "
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
                _claude_permission_entries(playbook_root, spill_available=spill_available),
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
    agy_entries = _agy_permission_entries(playbook_root, spill_available=spill_available)
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

    agy_bridge_issue = _agy_runtime_bridge_issue(playbook_root)
    if agy_bridge_issue and _active_runtime_label() == "antigravity":
        failures.append(agy_bridge_issue)
    elif agy_bridge_issue and agy_configs:
        warnings.append(agy_bridge_issue)

    return warnings, failures


def _active_runtime_label() -> str:
    for key in ("AGENTPLAYBOOK_AI_TOOL", "SPILL_AI_TOOL", "SPILL_TOKEN_USAGE_AI_TOOL"):
        value = os.environ.get(key, "").strip().lower()
        if value in {"agy", "antigravity"}:
            return "antigravity"
        if value in {"codex", "claude", "openai"}:
            return value
    return ""


def _agy_runtime_bridge_issue(playbook_root: Path) -> str:
    try:
        text = AGY_RUNTIME_BRIDGE_PATH.read_text()
    except OSError:
        return (
            "AGY runtime bridge is missing required fail-closed instructions at "
            f"{AGY_RUNTIME_BRIDGE_PATH}. Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )
    missing = [phrase for phrase in AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES if phrase not in text]
    if not missing:
        return ""
    return (
        "AGY runtime bridge is missing required fail-closed instructions at "
        f"{AGY_RUNTIME_BRIDGE_PATH}. Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
    )


def _claude_permission_entries(playbook_root: Path, *, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(playbook_root):
        for command in _python_entrypoint_commands(script, "claude", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def _agy_permission_entries(playbook_root: Path, *, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(playbook_root):
        for command in _python_entrypoint_commands(script, "antigravity", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "command", command)
    return entries


def _codex_prefix_rule_entries(playbook_root: Path) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(playbook_root):
        for path in _entrypoint_path_variants(script):
            entries.append(_codex_prefix_rule(["python3", path]))
    return entries


def _agentplaybook_python_scripts(playbook_root: Path) -> list[Path]:
    return sorted((playbook_root / "scripts").glob("*.py"))


def _python_entrypoint_commands(script: Path, tool: str, *, include_spill_env: bool = True) -> list[str]:
    commands: list[str] = []
    env_prefixes = ("",)
    if include_spill_env:
        env_prefixes += (
            f"SPILL_AI_TOOL={tool} ",
            f"SPILL_TOKEN_USAGE_AI_TOOL={tool} ",
        )
    for path in _entrypoint_path_variants(script):
        for prefix in env_prefixes:
            commands.append(f"{prefix}python3 {path}")
    return commands


def _entrypoint_path_variants(script: Path) -> list[str]:
    raw = str(script)
    variants = [
        raw,
        _quote(raw),
        _double_quote(raw),
    ]
    return _dedupe(variants)


def _add_permission_command_entries(entries: list[str], prefix: str, command: str) -> None:
    entries.append(f"{prefix}({command})")
    entries.append(f"{prefix}({command}:*)")
    entries.append(f"{prefix}({command} *)")


def _codex_prefix_rule(pattern: list[str]) -> str:
    encoded = ", ".join(json.dumps(item) for item in pattern)
    return f"prefix_rule(pattern=[{encoded}], decision=\"allow\")"


def _missing_allow_entries(config: dict[str, Any], entries: list[str]) -> list[str]:
    permissions = config.get("permissions")
    if not isinstance(permissions, dict):
        return entries
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        return entries
    return [entry for entry in entries if entry not in allow]


def _missing_text_entries(text: str, entries: list[str]) -> list[str]:
    return [entry for entry in entries if entry not in text]


def _quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def _double_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


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


def main() -> int:
    write_spill_label("analysis", "classify")
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

    early_bridge_failure = ""
    if _active_runtime_label() == "antigravity":
        early_bridge_failure = _agy_runtime_bridge_issue(playbook_root)
    if early_bridge_failure:
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
            "early_runtime_bridge_failure": early_bridge_failure,
        }
        write_json(evidence_path, evidence)
        print(f"Preflight evidence: {evidence_path}")
        print(f"FAIL: {early_bridge_failure}", file=sys.stderr)
        return 1

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
    vibeguard = run_command(vibeguard_command(project, rules), project)
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

    hook_warnings, hook_failures = _check_agent_hooks(playbook_root)

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
