"""Build runtime permission entries for AgentPlaybook scripts."""

from __future__ import annotations

import json
from pathlib import Path

from support.setup_config_files import quote
from support.spill_permissions import spill_helper_permission_commands as _spill_helper_permission_commands


def claude_permission_entries(scripts_dir: Path, *, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(scripts_dir):
        for command in _python_entrypoint_commands(script, "claude", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "Bash", command)
    if spill_available:
        for command in _spill_helper_permission_commands("claude"):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def claude_legacy_permission_entries(scripts_dir: Path) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(scripts_dir):
        for command in _python_entrypoint_commands(script, "claude", include_legacy=True):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def claude_project_permission_entries(scripts_dir: Path, *, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    env_prefixes = [""]
    if spill_available:
        env_prefixes += ["SPILL_AI_TOOL=claude ", "SPILL_TOKEN_USAGE_AI_TOOL=claude "]
    for script in _agentplaybook_python_scripts(scripts_dir):
        rel_path = str(Path("scripts") / script.name)
        for prefix in env_prefixes:
            _add_permission_command_entries(entries, "Bash", f"{prefix}python3 {rel_path}")
    for subcommand in ("log", "status", "diff", "show", "branch"):
        entries.append(f"Bash(git -C * {subcommand} *)")
    return entries


def agy_permission_entries(scripts_dir: Path, *, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(scripts_dir):
        for command in _python_entrypoint_commands(script, "antigravity", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "command", command)
    if spill_available:
        for command in _spill_helper_permission_commands("antigravity"):
            _add_permission_command_entries(entries, "command", command)
    return entries


def agy_legacy_permission_entries(scripts_dir: Path) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(scripts_dir):
        for command in _python_entrypoint_commands(script, "antigravity", include_legacy=True):
            _add_permission_command_entries(entries, "command", command)
    for command in _spill_helper_permission_commands("antigravity"):
        _add_permission_command_entries(entries, "command", command)
    return entries


def codex_prefix_rule_entries(scripts_dir: Path) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts(scripts_dir):
        for path in _entrypoint_path_variants(script):
            entries.append(_codex_prefix_rule(["python3", path]))
    return entries


def _agentplaybook_python_scripts(scripts_dir: Path) -> list[Path]:
    return sorted(scripts_dir.glob("*.py"))


def _python_entrypoint_commands(
    script: Path,
    tool: str,
    *,
    include_legacy: bool = False,
    include_spill_env: bool = True,
) -> list[str]:
    commands: list[str] = []
    env_prefixes = ("",)
    if include_spill_env:
        env_prefixes += (
            f"SPILL_AI_TOOL={tool} ",
            f"SPILL_TOKEN_USAGE_AI_TOOL={tool} ",
        )
    path_variants = (
        _legacy_entrypoint_path_variants(script)
        if include_legacy
        else _entrypoint_path_variants(script)
    )
    for path in path_variants:
        for prefix in env_prefixes:
            commands.append(f"{prefix}python3 {path}")
    return commands


def _entrypoint_path_variants(script: Path) -> list[str]:
    raw = str(script)
    return _dedupe([
        raw,
        quote(raw),
        _double_quote(raw),
    ])


def _legacy_entrypoint_path_variants(script: Path) -> list[str]:
    raw = str(script)
    variants = [
        *_entrypoint_path_variants(script),
        str(Path("scripts") / script.name),
    ]
    home = str(Path.home())
    if raw.startswith(home + "/"):
        suffix = raw[len(home) + 1:]
        variants += [
            f"~/{suffix}",
            f"$HOME/{suffix}",
            _double_quote(f"$HOME/{suffix}"),
            f"${{HOME}}/{suffix}",
            _double_quote(f"${{HOME}}/{suffix}"),
        ]
    return _dedupe(variants)


def _add_permission_command_entries(entries: list[str], prefix: str, command: str) -> None:
    entries.append(f"{prefix}({command})")
    entries.append(f"{prefix}({command}:*)")
    entries.append(f"{prefix}({command} *)")


def _codex_prefix_rule(pattern: list[str]) -> str:
    encoded = ", ".join(json.dumps(item) for item in pattern)
    return f"prefix_rule(pattern=[{encoded}], decision=\"allow\")"


def _double_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
