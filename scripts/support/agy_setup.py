"""Antigravity/AGY runtime bridge and permission setup."""

from __future__ import annotations

import re
from pathlib import Path

from support.permission_entries import agy_legacy_permission_entries, agy_permission_entries
from support.setup_config_files import merge_permissions_allow

AGY_RUNTIME_BRIDGE_PATH = Path.home() / ".antigravity" / "AGENTS.md"
AGY_RUNTIME_BRIDGE_BEGIN = "<!-- agentplaybook-runtime-bridge:start -->"
AGY_RUNTIME_BRIDGE_END = "<!-- agentplaybook-runtime-bridge:end -->"
AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES = [
    "Antigravity reads AGENTS.md",
    "Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
    "Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
    "If this bridge or the project-root AGENTS.md cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
]


def configure_agy(
    dry_run: bool,
    *,
    root: Path,
    scripts_dir: Path,
    spill_available: bool = True,
) -> list[dict]:
    results = []
    status = _merge_agy_runtime_bridge(AGY_RUNTIME_BRIDGE_PATH, dry_run, root=root)
    results.append({
        "tool": "agy",
        "hook": "runtime_bridge.AGENTS",
        "status": status,
        "path": str(AGY_RUNTIME_BRIDGE_PATH),
    })

    entries = agy_permission_entries(scripts_dir, spill_available=spill_available)
    cleanup_entries = agy_legacy_permission_entries(scripts_dir)
    if not spill_available:
        cleanup_entries += agy_permission_entries(scripts_dir, spill_available=True)
    targets = [
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
        Path.home() / ".gemini" / "config" / "config.json",
    ]

    for target in targets:
        status = merge_permissions_allow(
            target,
            entries,
            dry_run,
            cleanup_entries=cleanup_entries,
        )
        results.append({
            "tool": "agy",
            "hook": "permissions.AgentPlaybookPython",
            "status": status,
            "path": str(target),
        })

    hooks_path = Path.home() / ".gemini" / "config" / "hooks.json"
    status = "ok" if hooks_path.exists() else "ok (no hooks file; permissions use config.json/settings.json)"
    results.append({
        "tool": "agy",
        "hook": "config.hooks",
        "status": status,
        "path": str(hooks_path),
    })
    return results


def _merge_agy_runtime_bridge(target: Path, dry_run: bool, *, root: Path) -> str:
    text = target.read_text() if target.exists() else ""
    block = _agy_runtime_bridge_block(root)
    pattern = re.compile(
        re.escape(AGY_RUNTIME_BRIDGE_BEGIN)
        + r"[\s\S]*?"
        + re.escape(AGY_RUNTIME_BRIDGE_END)
        + r"\n?",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match:
        if match.group(0) == block:
            return "ok"
        if dry_run:
            return "missing"
        updated = pattern.sub(block, text)
    else:
        missing = [phrase for phrase in AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES if phrase not in text]
        if not missing:
            return "ok"
        if dry_run:
            return "missing"
        separator = "" if not text or text.endswith("\n") else "\n"
        updated = f"{text}{separator}{block}"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated)
    return "installed"


def _agy_runtime_bridge_block(root: Path) -> str:
    return "\n".join([
        AGY_RUNTIME_BRIDGE_BEGIN,
        "## AgentPlaybook Runtime Bridge",
        "",
        "Apply this bridge before project work in Antigravity/AGY sessions.",
        "",
        f"- Shared AgentPlaybook root: `{root}`",
        "- Start every task by identifying the current project root.",
        "- Before project work, open the project-root instruction file for the active runtime.",
        "- Antigravity reads AGENTS.md.",
        "- Read project-root instructions before AgentPlaybook shared guidance.",
        "- For multi-step work, run AgentPlaybook preflight before edits and finish-check before final report, commit, release, or handoff.",
        "- If this bridge or the project-root AGENTS.md cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
        "- Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
        "- Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
        "- If a response exposed those background details, do not answer with an apology-only message; continue by repairing the action path or stopping with the specific blocker.",
        AGY_RUNTIME_BRIDGE_END,
        "",
    ])
