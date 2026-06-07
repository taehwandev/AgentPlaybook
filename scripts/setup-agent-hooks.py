#!/usr/bin/env python3
"""Configure AI runtime hooks and permissions for AgentPlaybook.

Run once after cloning AgentPlaybook to allow the AgentPlaybook Python
entrypoints in local agent runtimes. When the optional local Spill helper is
installed, this also wires AgentPlaybook's workflow label bridge. Re-running is
safe; existing hooks and permissions are deduplicated.

Usage:
    python3 scripts/setup-agent-hooks.py
    python3 scripts/setup-agent-hooks.py --dry-run
    python3 scripts/setup-agent-hooks.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
WORKFLOW_SCRIPT = SCRIPTS_DIR / "workflow.py"
DEFAULT_SPILL_SETUP_HELPER = (
    Path.home()
    / "Library/Application Support/Spill/adapters/setup/spill-token-metering-setup.mjs"
)

_BASELINE_COMMAND_RE = re.compile(
    r"workflow\.py.*route.*triage.*--request-classified"
)
AGY_RUNTIME_BRIDGE_PATH = Path.home() / ".antigravity" / "AGENTS.md"
AGY_RUNTIME_BRIDGE_BEGIN = "<!-- agentplaybook-runtime-bridge:start -->"
AGY_RUNTIME_BRIDGE_END = "<!-- agentplaybook-runtime-bridge:end -->"
AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES = [
    "Antigravity reads AGENTS.md",
    "Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
    "Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
    "If this bridge or the project-root AGENTS.md cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure AI runtime hooks and permissions for AgentPlaybook."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any required hook is missing.",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or args.check
    results: list[dict] = []

    if _has_claude():
        results += _configure_claude(dry_run)

    if _has_codex():
        results += _configure_codex(dry_run)

    if _has_agy():
        results += _configure_agy(dry_run)

    _print_results(results, dry_run)

    if args.check:
        missing = [r for r in results if r["status"] == "missing"]
        if missing:
            print(
                "\nRun `python3 scripts/setup-agent-hooks.py` to install missing hooks or permissions.",
                file=sys.stderr,
            )
            sys.exit(1)


# detection

def _has_claude() -> bool:
    return (Path.home() / ".claude").is_dir() or bool(shutil.which("claude"))


def _has_codex() -> bool:
    return (Path.home() / ".codex").is_dir() or bool(shutil.which("codex"))


def _has_agy() -> bool:
    gemini_home = Path.home() / ".gemini"
    return (
        gemini_home.is_dir()
        or bool(shutil.which("agy"))
        or bool(shutil.which("antigravity"))
        or bool(shutil.which("gemini"))
    )


def _spill_setup_helper_path() -> Path:
    override = os.environ.get("AGENTPLAYBOOK_SPILL_HELPER_PATH", "")
    return Path(override) if override else DEFAULT_SPILL_SETUP_HELPER


def _has_spill_setup_helper() -> bool:
    return _spill_setup_helper_path().is_file()


# Claude Code

def _configure_claude(dry_run: bool) -> list[dict]:
    target = Path.home() / ".claude" / "settings.json"
    baseline_cmd = (
        f"SPILL_AI_TOOL=claude python3 {_quote(str(WORKFLOW_SCRIPT))}"
        " route triage --request-classified"
    )
    spill_available = _has_spill_setup_helper()
    results = []

    if spill_available:
        status = _merge_claude_user_prompt_submit(target, baseline_cmd, dry_run)
    else:
        status = _remove_claude_user_prompt_submit(target, dry_run)
    results.append({"tool": "claude", "hook": "UserPromptSubmit_spill_bridge", "status": status, "path": str(target)})

    cleanup_entries = _claude_legacy_permission_entries()
    if not spill_available:
        cleanup_entries += _claude_permission_entries(spill_available=True)
    status = _merge_permissions_allow(
        target,
        _claude_permission_entries(spill_available=spill_available),
        dry_run,
        cleanup_entries=cleanup_entries,
    )
    results.append({"tool": "claude", "hook": "permissions.AgentPlaybookPython", "status": status, "path": str(target)})

    status = _set_claude_env(target, dry_run) if spill_available else _remove_claude_env(target, dry_run)
    results.append({"tool": "claude", "hook": "env.SPILL_AI_TOOL", "status": status, "path": str(target)})

    return results


def _merge_claude_user_prompt_submit(target: Path, command: str, dry_run: bool) -> str:
    config = _read_json(target)
    hooks = config.get("hooks", {})
    groups: list = hooks.get("UserPromptSubmit", [])

    # Check if already present
    for group in groups:
        for hook in group.get("hooks", []):
            if _is_managed_claude_spill_bridge_command(hook.get("command", "")):
                return "ok"

    if dry_run:
        return "missing"

    cleaned = [
        g for g in groups
        if not any(
            _is_managed_claude_spill_bridge_command(h.get("command", ""))
            for h in g.get("hooks", [])
        )
    ]
    cleaned.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": command, "timeout": 5}],
    })
    hooks["UserPromptSubmit"] = cleaned
    config["hooks"] = hooks
    _write_json(target, config)
    return "installed"


def _remove_claude_user_prompt_submit(target: Path, dry_run: bool) -> str:
    config = _read_json(target)
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
    _write_json(target, config)
    return "removed"


def _is_managed_claude_spill_bridge_command(command: str) -> bool:
    return bool(
        _BASELINE_COMMAND_RE.search(command)
        and "SPILL_AI_TOOL=claude" in command
    )


def _set_claude_env(target: Path, dry_run: bool) -> str:
    config = _read_json(target)
    env = config.get("env", {})
    if env.get("SPILL_AI_TOOL") == "claude":
        return "ok"
    if dry_run:
        return "missing"
    env["SPILL_AI_TOOL"] = "claude"
    env["SPILL_TOKEN_USAGE_AI_TOOL"] = "claude"
    config["env"] = env
    _write_json(target, config)
    return "installed"


def _remove_claude_env(target: Path, dry_run: bool) -> str:
    config = _read_json(target)
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
    _write_json(target, config)
    return "removed"


# Codex

def _configure_codex(dry_run: bool) -> list[dict]:
    results = []
    target = Path.home() / ".codex" / "rules" / "default.rules"
    status = _merge_codex_prefix_rules(target, _codex_prefix_rule_entries(), dry_run)
    results.append({"tool": "codex", "hook": "rules.AgentPlaybookPython", "status": status, "path": str(target)})

    return results


# Antigravity / AGY

def _configure_agy(dry_run: bool) -> list[dict]:
    results = []
    status = _merge_agy_runtime_bridge(AGY_RUNTIME_BRIDGE_PATH, dry_run)
    results.append({
        "tool": "agy",
        "hook": "runtime_bridge.AGENTS",
        "status": status,
        "path": str(AGY_RUNTIME_BRIDGE_PATH),
    })

    spill_available = _has_spill_setup_helper()
    entries = _agy_permission_entries(spill_available=spill_available)
    cleanup_entries = _agy_legacy_permission_entries()
    if not spill_available:
        cleanup_entries += _agy_permission_entries(spill_available=True)
    targets = [
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
        Path.home() / ".gemini" / "config" / "config.json",
    ]

    for target in targets:
        status = _merge_permissions_allow(
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


# helpers

def _merge_agy_runtime_bridge(target: Path, dry_run: bool) -> str:
    text = target.read_text() if target.exists() else ""
    block = _agy_runtime_bridge_block()
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


def _agy_runtime_bridge_block() -> str:
    return "\n".join([
        AGY_RUNTIME_BRIDGE_BEGIN,
        "## AgentPlaybook Runtime Bridge",
        "",
        "Apply this bridge before project work in Antigravity/AGY sessions.",
        "",
        f"- Shared AgentPlaybook root: `{ROOT}`",
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


def _claude_permission_entries(*, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "claude", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def _claude_legacy_permission_entries() -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "claude", include_legacy=True):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def _agy_permission_entries(*, spill_available: bool = True) -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "antigravity", include_spill_env=spill_available):
            _add_permission_command_entries(entries, "command", command)
    return entries


def _agy_legacy_permission_entries() -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "antigravity", include_legacy=True):
            _add_permission_command_entries(entries, "command", command)
    return entries


def _codex_prefix_rule_entries() -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for path in _entrypoint_path_variants(script):
            entries.append(_codex_prefix_rule(["python3", path]))
    return entries


def _agentplaybook_python_scripts() -> list[Path]:
    return sorted(SCRIPTS_DIR.glob("*.py"))


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
    variants = [
        raw,
        _quote(raw),
        _double_quote(raw),
    ]
    return _dedupe(variants)


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
    # Include both common wildcard spellings because Claude Code and AGY have
    # used different permission matchers across versions.
    entries.append(f"{prefix}({command})")
    entries.append(f"{prefix}({command}:*)")
    entries.append(f"{prefix}({command} *)")


def _codex_prefix_rule(pattern: list[str]) -> str:
    encoded = ", ".join(json.dumps(item) for item in pattern)
    return f"prefix_rule(pattern=[{encoded}], decision=\"allow\")"


def _merge_codex_prefix_rules(target: Path, entries: list[str], dry_run: bool) -> str:
    text = target.read_text() if target.exists() else ""
    text, removed_legacy_shell_rules = _remove_legacy_codex_shell_rules(text)
    block = "\n".join([
        "# agentplaybook-hooks:begin",
        "# Managed by AgentPlaybook setup. Keep narrow; do not replace with broad python3 rules.",
        *entries,
        "# agentplaybook-hooks:end",
        "",
    ])
    pattern = re.compile(
        r"# agentplaybook-hooks:begin[\s\S]*?# agentplaybook-hooks:end\n?",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match:
        if match.group(0) == block:
            if removed_legacy_shell_rules:
                if dry_run:
                    return "missing"
                target.write_text(text)
                return "installed"
            return "ok"
        if dry_run:
            return "missing"
        updated = pattern.sub(block, text)
    else:
        missing = [entry for entry in entries if entry not in text]
        if not missing and not removed_legacy_shell_rules:
            return "ok"
        if dry_run:
            return "missing"
        if missing:
            updated = f"{text}{'' if not text or text.endswith(chr(10)) else chr(10)}{block}"
        else:
            updated = text
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated)
    return "installed"


def _remove_legacy_codex_shell_rules(text: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    removed = False
    for line in lines:
        if _is_legacy_codex_agentplaybook_shell_rule(line):
            removed = True
            continue
        kept.append(line)
    return "".join(kept), removed


def _is_legacy_codex_agentplaybook_shell_rule(line: str) -> bool:
    if not line.startswith("prefix_rule(pattern=["):
        return False
    if '"-lc"' not in line:
        return False
    if not any(
        shell in line
        for shell in ('"/bin/zsh"', '"zsh"', '"/bin/bash"', '"bash"')
    ):
        return False
    if "python3 " not in line or "AgentPlaybook/scripts/" not in line:
        return False
    return True


def _merge_permissions_allow(
    target: Path,
    entries: list[str],
    dry_run: bool,
    *,
    cleanup_entries: list[str] | None = None,
) -> str:
    config = _read_json(target)
    permissions = config.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        allow = []

    cleanup_set = set(cleanup_entries or [])
    entry_set = set(entries)
    stale = [
        entry for entry in allow
        if entry in cleanup_set and entry not in entry_set
    ]
    missing = [entry for entry in entries if entry not in allow]
    if not missing and not stale:
        return "ok"
    if dry_run:
        if stale and not missing:
            return "would_remove"
        if stale:
            return "would_update"
        return "missing"

    cleaned = [entry for entry in allow if entry not in stale]
    permissions["allow"] = cleaned + missing
    config["permissions"] = permissions
    _write_json(target, config)
    return "installed"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


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


def _print_results(results: list[dict], dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    for r in results:
        marker = (
            "OK"
            if r["status"].startswith("ok")
            else (
                "INSTALLED"
                if r["status"] == "installed"
                else (
                    "REMOVED"
                    if r["status"] == "removed"
                    else (
                        "WOULD REMOVE"
                        if r["status"] == "would_remove"
                        else ("WOULD UPDATE" if r["status"] == "would_update" else "MISSING")
                    )
                )
            )
        )
        print(f"{prefix}{marker} {r['tool']} / {r['hook']}: {r['status']} ({r['path']})")


if __name__ == "__main__":
    main()
