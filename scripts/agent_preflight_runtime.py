"""Runtime hook checks for AgentPlaybook preflight."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agent_preflight_spill import has_spill_setup_helper
from support.permission_entries import (
    agy_permission_entries,
    claude_permission_entries,
    codex_prefix_rule_entries,
)
from support.stable_launcher import stable_launcher_issue


BASELINE_HOOK_RE = re.compile(
    r"(?:workflow\.py.*route|agentplaybook-hook.*workflow.*route).*triage.*--request-classified"
)
CLASSIFIED_HOOK_EVIDENCE_RE = re.compile(
    r"(?:workflow\.py.*route|agentplaybook-hook.*workflow.*route).*triage.*--request-classified.*--classification-evidence"
)
AGY_RUNTIME_BRIDGE_PATH = Path.home() / ".antigravity" / "AGENTS.md"
AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES = [
    "Antigravity reads AGENTS.md",
    "If the runtime starts outside the target repo or the target repo is not explicit, run AgentPlaybook agent-entry.py or project-discover.py before project work.",
    "If project discovery returns ambiguous or not_found, ask the user for the target project before routing, editing, testing, committing, or reporting completion.",
    "Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
    "Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
    "If this bridge or the project-root AGENTS.md cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
]


def check_agent_hooks(playbook_root: Path) -> tuple[list[str], list[str]]:
    """Return warning and failure strings for missing runtime registrations."""
    warnings: list[str] = []
    failures: list[str] = []
    spill_available = has_spill_setup_helper()

    warnings.extend(_codex_warnings(playbook_root))
    warnings.extend(_claude_warnings(playbook_root, spill_available=spill_available))
    agy_warnings = _agy_warnings(playbook_root, spill_available=spill_available)
    warnings.extend(agy_warnings)

    agy_bridge_issue = agy_runtime_bridge_issue(playbook_root)
    if agy_bridge_issue and active_runtime_label() == "antigravity":
        failures.append(agy_bridge_issue)
    elif agy_bridge_issue and agy_warnings:
        warnings.append(agy_bridge_issue)

    return warnings, failures


def active_runtime_label() -> str:
    for key in ("AGENTPLAYBOOK_AI_TOOL", "SPILL_AI_TOOL", "SPILL_TOKEN_USAGE_AI_TOOL"):
        value = os.environ.get(key, "").strip().lower()
        if value in {"agy", "antigravity"}:
            return "antigravity"
        if value in {"codex", "claude", "openai"}:
            return value
    return ""


def agy_runtime_bridge_issue(playbook_root: Path) -> str:
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


def _codex_warnings(playbook_root: Path) -> list[str]:
    target = Path.home() / ".codex" / "rules" / "default.rules"
    if not target.exists():
        return []
    try:
        missing_permissions = _missing_text_entries(
            target.read_text(),
            codex_prefix_rule_entries(playbook_root / "scripts"),
        )
    except OSError:
        return []
    if not missing_permissions:
        return []
    return [
        "Codex AgentPlaybook Python prefix rules are missing. "
        f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
    ]


def _claude_warnings(playbook_root: Path, *, spill_available: bool) -> list[str]:
    target = Path.home() / ".claude" / "settings.json"
    if not target.exists():
        return []
    try:
        config = json.loads(target.read_text())
    except (json.JSONDecodeError, OSError):
        return []

    warnings: list[str] = []
    launcher_issue = stable_launcher_issue(playbook_root)
    if launcher_issue:
        warnings.append(launcher_issue)
    if spill_available:
        warnings.extend(_claude_spill_warnings(config, playbook_root))
    missing_permissions = _missing_allow_entries(
        config,
        claude_permission_entries(playbook_root / "scripts", spill_available=spill_available),
    )
    if missing_permissions:
        warnings.append(
            "Claude Code AgentPlaybook Python permissions are missing. "
            f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )
    return warnings


def _claude_spill_warnings(config: dict[str, Any], playbook_root: Path) -> list[str]:
    warnings: list[str] = []
    groups = config.get("hooks", {}).get("UserPromptSubmit", [])
    managed_commands = [
        h.get("command", "")
        for g in groups
        for h in g.get("hooks", [])
        if BASELINE_HOOK_RE.search(h.get("command", ""))
        and "SPILL_AI_TOOL=claude" in h.get("command", "")
    ]
    has_classification_evidence = any(
        CLASSIFIED_HOOK_EVIDENCE_RE.search(command)
        for command in managed_commands
    )
    if not managed_commands:
        warnings.append(
            "Claude Code UserPromptSubmit Spill workflow label hook is missing. "
            f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )
    elif not has_classification_evidence:
        warnings.append(
            "Claude Code UserPromptSubmit Spill workflow label hook is missing "
            "--classification-evidence. Run: "
            f"python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )
    spill_tool = config.get("env", {}).get("SPILL_AI_TOOL", "")
    if spill_tool != "claude":
        warnings.append(
            "env.SPILL_AI_TOOL is not set to 'claude' in ~/.claude/settings.json. "
            f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        )
    return warnings


def _agy_warnings(playbook_root: Path, *, spill_available: bool) -> list[str]:
    targets = [
        Path.home() / ".gemini" / "config" / "config.json",
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
    ]
    entries = agy_permission_entries(playbook_root / "scripts", spill_available=spill_available)
    configs: list[dict[str, Any]] = []
    for target in targets:
        config = _read_json_object(target)
        if config is not None:
            configs.append(config)
    if configs and not any(not _missing_allow_entries(config, entries) for config in configs):
        return [
            "AGY AgentPlaybook Python permissions are missing from AGY config. "
            f"Run: python3 {playbook_root / 'scripts' / 'setup-agent-hooks.py'}"
        ]
    return []


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


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
