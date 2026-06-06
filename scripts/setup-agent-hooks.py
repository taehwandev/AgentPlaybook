#!/usr/bin/env python3
"""Configure AI runtime hooks and permissions for AgentPlaybook.

Run once after cloning AgentPlaybook to register the UserPromptSubmit
baseline label hook for each detected AI runtime (Claude Code, Codex)
and allow the AgentPlaybook Python entrypoints in local agent runtimes.
Re-running is safe; existing hooks and permissions are deduplicated.

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

_BASELINE_COMMAND_RE = re.compile(
    r"workflow\.py.*route.*triage.*--request-classified"
)


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


# Claude Code

def _configure_claude(dry_run: bool) -> list[dict]:
    target = Path.home() / ".claude" / "settings.json"
    baseline_cmd = (
        f"SPILL_AI_TOOL=claude python3 {_quote(str(WORKFLOW_SCRIPT))}"
        " route triage --request-classified"
    )
    results = []

    # UserPromptSubmit baseline label hook
    status = _merge_claude_user_prompt_submit(target, baseline_cmd, dry_run)
    results.append({"tool": "claude", "hook": "UserPromptSubmit_baseline", "status": status, "path": str(target)})

    status = _merge_permissions_allow(target, _claude_permission_entries(), dry_run)
    results.append({"tool": "claude", "hook": "permissions.AgentPlaybookPython", "status": status, "path": str(target)})

    # SPILL_AI_TOOL env in settings
    status = _set_claude_env(target, dry_run)
    results.append({"tool": "claude", "hook": "env.SPILL_AI_TOOL", "status": status, "path": str(target)})

    # ~/.zshenv fallback
    status = _set_zshenv(dry_run)
    results.append({"tool": "claude", "hook": "zshenv.SPILL_AI_TOOL", "status": status, "path": str(Path.home() / ".zshenv")})

    return results


def _merge_claude_user_prompt_submit(target: Path, command: str, dry_run: bool) -> str:
    config = _read_json(target)
    hooks = config.get("hooks", {})
    groups: list = hooks.get("UserPromptSubmit", [])

    # Check if already present
    for group in groups:
        for hook in group.get("hooks", []):
            if _BASELINE_COMMAND_RE.search(hook.get("command", "")):
                return "ok"

    if dry_run:
        return "missing"

    cleaned = [
        g for g in groups
        if not any(
            _BASELINE_COMMAND_RE.search(h.get("command", ""))
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


def _set_zshenv(dry_run: bool) -> str:
    zshenv = Path.home() / ".zshenv"
    text = zshenv.read_text() if zshenv.exists() else ""
    if "SPILL_AI_TOOL" in text:
        return "ok"
    if dry_run:
        return "missing"
    with open(zshenv, "a") as f:
        f.write("\nexport SPILL_AI_TOOL=claude\n")
    return "installed"


# Codex

def _configure_codex(dry_run: bool) -> list[dict]:
    results = []
    target = Path.home() / ".codex" / "rules" / "default.rules"
    status = _merge_codex_prefix_rules(target, _codex_prefix_rule_entries(), dry_run)
    results.append({"tool": "codex", "hook": "rules.AgentPlaybookPython", "status": status, "path": str(target)})

    status = _set_codex_env_zshenv(dry_run)
    results.append({"tool": "codex", "hook": "zshenv.SPILL_AI_TOOL_CODEX", "status": status, "path": str(Path.home() / ".zshenv")})
    return results


def _set_codex_env_zshenv(dry_run: bool) -> str:
    # Codex reads SPILL_AI_TOOL from its shell env.
    # Already handled by the global SPILL_AI_TOOL if running claude-only,
    # but Codex needs its own value when both run simultaneously.
    # Skip if already set by Spill setup.mjs.
    zshenv = Path.home() / ".zshenv"
    text = zshenv.read_text() if zshenv.exists() else ""
    if "SPILL_AI_TOOL" in text:
        return "ok (covered by existing SPILL_AI_TOOL entry)"
    return "ok (codex uses system SPILL_AI_TOOL)"


# Antigravity / AGY

def _configure_agy(dry_run: bool) -> list[dict]:
    results = []
    entries = _agy_permission_entries()
    targets = [
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
        Path.home() / ".gemini" / "config" / "config.json",
    ]

    for target in targets:
        status = _merge_permissions_allow(target, entries, dry_run)
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

def _claude_permission_entries() -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "claude"):
            _add_permission_command_entries(entries, "Bash", command)
    return entries


def _agy_permission_entries() -> list[str]:
    entries: list[str] = []
    for script in _agentplaybook_python_scripts():
        for command in _python_entrypoint_commands(script, "antigravity"):
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


def _python_entrypoint_commands(script: Path, tool: str) -> list[str]:
    commands: list[str] = []
    env_prefixes = (
        "",
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
        str(Path("scripts") / script.name),
    ]
    home = str(Path.home())
    if raw.startswith(home + os.sep):
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
            return "ok"
        if dry_run:
            return "missing"
        updated = pattern.sub(block, text)
    else:
        missing = [entry for entry in entries if entry not in text]
        if not missing:
            return "ok"
        if dry_run:
            return "missing"
        updated = f"{text}{'' if not text or text.endswith(chr(10)) else chr(10)}{block}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated)
    return "installed"


def _merge_permissions_allow(target: Path, entries: list[str], dry_run: bool) -> str:
    config = _read_json(target)
    permissions = config.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        allow = []

    missing = [entry for entry in entries if entry not in allow]
    if not missing:
        return "ok"
    if dry_run:
        return "missing"

    permissions["allow"] = allow + missing
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
            else ("INSTALLED" if r["status"] == "installed" else "MISSING")
        )
        print(f"{prefix}{marker} {r['tool']} / {r['hook']}: {r['status']} ({r['path']})")


if __name__ == "__main__":
    main()
