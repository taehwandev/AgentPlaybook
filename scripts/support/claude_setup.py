"""Claude Code hook and permission setup."""

from __future__ import annotations

import re
from pathlib import Path

from support.permission_entries import (
    claude_legacy_permission_entries,
    claude_permission_entries,
    claude_project_permission_entries,
)
from support.setup_config_files import merge_permissions_allow, quote, read_json, write_json

_BASELINE_COMMAND_RE = re.compile(
    r"workflow\.py.*route.*triage.*--request-classified"
)


def configure_claude(
    dry_run: bool,
    *,
    root: Path,
    scripts_dir: Path,
    workflow_script: Path,
    spill_available: bool = True,
) -> list[dict]:
    target = Path.home() / ".claude" / "settings.json"
    baseline_cmd = (
        f"SPILL_AI_TOOL=claude python3 {quote(str(workflow_script))}"
        " route triage --request-classified"
    )
    results = []

    if spill_available:
        status = _merge_claude_user_prompt_submit(target, baseline_cmd, dry_run)
    else:
        status = _remove_claude_user_prompt_submit(target, dry_run)
    results.append({"tool": "claude", "hook": "UserPromptSubmit_spill_bridge", "status": status, "path": str(target)})

    cleanup_entries = claude_legacy_permission_entries(scripts_dir)
    if not spill_available:
        cleanup_entries += claude_permission_entries(scripts_dir, spill_available=True)
    status = merge_permissions_allow(
        target,
        claude_permission_entries(scripts_dir, spill_available=spill_available),
        dry_run,
        cleanup_entries=cleanup_entries,
    )
    results.append({"tool": "claude", "hook": "permissions.AgentPlaybookPython", "status": status, "path": str(target)})

    status = _set_claude_env(target, dry_run) if spill_available else _remove_claude_env(target, dry_run)
    results.append({"tool": "claude", "hook": "env.SPILL_AI_TOOL", "status": status, "path": str(target)})
    results += _configure_claude_project(root, scripts_dir, dry_run, spill_available=spill_available)
    return results


def _configure_claude_project(
    root: Path,
    scripts_dir: Path,
    dry_run: bool,
    *,
    spill_available: bool = True,
) -> list[dict]:
    target = root / ".claude" / "settings.json"
    entries = claude_project_permission_entries(scripts_dir, spill_available=spill_available)
    status = merge_permissions_allow(target, entries, dry_run)
    return [{"tool": "claude", "hook": "permissions.project", "status": status, "path": str(target)}]


def _merge_claude_user_prompt_submit(target: Path, command: str, dry_run: bool) -> str:
    config = read_json(target)
    hooks = config.get("hooks", {})
    groups: list = hooks.get("UserPromptSubmit", [])

    for group in groups:
        for hook in group.get("hooks", []):
            if _is_managed_claude_spill_bridge_command(hook.get("command", "")):
                return "ok"

    if dry_run:
        return "missing"

    cleaned = [
        group for group in groups
        if not any(
            _is_managed_claude_spill_bridge_command(hook.get("command", ""))
            for hook in group.get("hooks", [])
        )
    ]
    cleaned.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": command, "timeout": 5}],
    })
    hooks["UserPromptSubmit"] = cleaned
    config["hooks"] = hooks
    write_json(target, config)
    return "installed"


def _remove_claude_user_prompt_submit(target: Path, dry_run: bool) -> str:
    config = read_json(target)
    hooks = config.get("hooks", {})
    groups: list = hooks.get("UserPromptSubmit", [])
    changed = False
    cleaned_groups = []

    for group in groups:
        group_hooks = group.get("hooks", [])
        if not isinstance(group_hooks, list):
            cleaned_groups.append(group)
            continue
        filtered_hooks = [
            hook for hook in group_hooks
            if not _is_managed_claude_spill_bridge_command(hook.get("command", ""))
        ]
        if len(filtered_hooks) != len(group_hooks):
            changed = True
        if filtered_hooks:
            updated_group = dict(group)
            updated_group["hooks"] = filtered_hooks
            cleaned_groups.append(updated_group)

    if not changed:
        return "ok"
    if dry_run:
        return "would_remove"

    hooks["UserPromptSubmit"] = cleaned_groups
    config["hooks"] = hooks
    write_json(target, config)
    return "removed"


def _is_managed_claude_spill_bridge_command(command: str) -> bool:
    return bool(
        _BASELINE_COMMAND_RE.search(command)
        and "SPILL_AI_TOOL=claude" in command
    )


def _set_claude_env(target: Path, dry_run: bool) -> str:
    config = read_json(target)
    env = config.get("env", {})
    if env.get("SPILL_AI_TOOL") == "claude":
        return "ok"
    if dry_run:
        return "missing"
    env["SPILL_AI_TOOL"] = "claude"
    env["SPILL_TOKEN_USAGE_AI_TOOL"] = "claude"
    config["env"] = env
    write_json(target, config)
    return "installed"


def _remove_claude_env(target: Path, dry_run: bool) -> str:
    config = read_json(target)
    env = config.get("env", {})
    if not isinstance(env, dict):
        return "ok"

    changed = False
    for key, expected in (
        ("SPILL_AI_TOOL", "claude"),
        ("SPILL_TOKEN_USAGE_AI_TOOL", "claude"),
    ):
        if env.get(key) == expected:
            env.pop(key)
            changed = True
    if not changed:
        return "ok"
    if dry_run:
        return "would_remove"
    if env:
        config["env"] = env
    else:
        config.pop("env", None)
    write_json(target, config)
    return "removed"
