"""Read, merge, and report runtime setup configuration files."""

from __future__ import annotations

import json
import re
from pathlib import Path


def merge_codex_prefix_rules(target: Path, entries: list[str], dry_run: bool) -> str:
    text = target.read_text() if target.exists() else ""
    text, removed_legacy_shell_rules = _remove_legacy_codex_shell_rules(text)
    text, removed_legacy_prefix_rules = _remove_legacy_codex_agentplaybook_prefix_rules(text, entries)
    removed_legacy_rules = removed_legacy_shell_rules or removed_legacy_prefix_rules
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
            if removed_legacy_rules:
                if dry_run:
                    return "missing"
                target.write_text(text)
                return "installed"
            return "ok"
        if dry_run:
            return "missing"
        updated = text[:match.start()] + block + text[match.end():]
    else:
        missing = [entry for entry in entries if entry not in text]
        if not missing and not removed_legacy_rules:
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


def merge_permissions_allow(
    target: Path,
    entries: list[str],
    dry_run: bool,
    *,
    cleanup_entries: list[str] | None = None,
) -> str:
    config = read_json(target)
    permissions = config.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        allow = []

    entry_set = set(entries)
    cleanup_set = set(cleanup_entries or [])
    cleanup_script_names = (
        _permission_entry_script_names([*entries, *(cleanup_entries or [])])
        if cleanup_entries is not None
        else set()
    )
    stale = [
        entry for entry in allow
        if entry not in entry_set
        and (
            entry in cleanup_set
            or _permission_entry_targets_agentplaybook_script(entry, cleanup_script_names)
        )
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
    write_json(target, config)
    return "installed"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def print_results(results: list[dict], dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    for result in results:
        print(f"{prefix}{_status_marker(result['status'])} {result['tool']} / {result['hook']}: {result['status']} ({result['path']})")


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


def _remove_legacy_codex_agentplaybook_prefix_rules(text: str, entries: list[str]) -> tuple[str, bool]:
    script_names = _codex_prefix_script_names(entries)
    if not script_names:
        return text, False

    pattern = re.compile(
        r"# agentplaybook-hooks:begin[\s\S]*?# agentplaybook-hooks:end\n?",
        re.MULTILINE,
    )
    chunks: list[str] = []
    removed = False
    cursor = 0
    for match in pattern.finditer(text):
        cleaned, chunk_removed = _remove_legacy_codex_agentplaybook_prefix_rule_lines(
            text[cursor:match.start()],
            script_names,
        )
        chunks.append(cleaned)
        chunks.append(match.group(0))
        removed = removed or chunk_removed
        cursor = match.end()

    cleaned, chunk_removed = _remove_legacy_codex_agentplaybook_prefix_rule_lines(
        text[cursor:],
        script_names,
    )
    chunks.append(cleaned)
    removed = removed or chunk_removed
    return "".join(chunks), removed


def _remove_legacy_codex_agentplaybook_prefix_rule_lines(text: str, script_names: set[str]) -> tuple[str, bool]:
    kept: list[str] = []
    removed = False
    for line in text.splitlines(keepends=True):
        if _is_codex_agentplaybook_prefix_rule(line, script_names):
            removed = True
            continue
        kept.append(line)
    return "".join(kept), removed


def _codex_prefix_script_names(entries: list[str]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        pattern = _parse_codex_prefix_rule(entry)
        if not pattern:
            continue
        for token in pattern:
            if token.endswith(".py"):
                names.add(Path(token).name)
    return names


def _is_codex_agentplaybook_prefix_rule(line: str, script_names: set[str]) -> bool:
    pattern = _parse_codex_prefix_rule(line)
    if not pattern:
        return False
    return any(_token_targets_agentplaybook_script(token, script_names) for token in pattern)


def _parse_codex_prefix_rule(line: str) -> list[str]:
    match = re.match(r"^prefix_rule\(pattern=(\[[^\]]*\]), decision=\"allow\"\)\s*$", line.strip())
    if not match:
        return []
    try:
        pattern = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    if not isinstance(pattern, list) or not all(isinstance(item, str) for item in pattern):
        return []
    return pattern


def _token_targets_agentplaybook_script(token: str, script_names: set[str]) -> bool:
    normalized = token.strip("'\"").replace("\\.", ".")
    return any(f"scripts/{name}" in normalized for name in script_names)


def _permission_entry_script_names(entries: list[str]) -> set[str]:
    names: set[str] = set()
    for entry in entries:
        for match in re.finditer(r"(?:^|[/\s'\"`])scripts/([A-Za-z0-9_.-]+\.py)", entry):
            names.add(match.group(1))
    return names


def _permission_entry_targets_agentplaybook_script(entry: str, script_names: set[str]) -> bool:
    normalized = entry.replace("\\.", ".")
    return any(f"scripts/{name}" in normalized for name in script_names)


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


def _status_marker(status: str) -> str:
    if status.startswith("ok"):
        return "OK"
    if status == "installed":
        return "INSTALLED"
    if status == "removed":
        return "REMOVED"
    if status == "would_remove":
        return "WOULD REMOVE"
    if status == "would_update":
        return "WOULD UPDATE"
    return "MISSING"
