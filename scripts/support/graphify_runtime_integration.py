"""Remove runtime prose copies and keep only canonical Graphify adapters."""

from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path
from typing import Iterable

from support.graphify_contract import (
    AGY_GRAPHIFY_RULE,
    AGY_GRAPHIFY_WORKFLOW,
    CANONICAL_SKILL_DIR,
)
from support.graphify_paths import replace_file_with_link


def normalize_runtime_integrations(
    project_path: Path,
    platforms: Iterable[str],
) -> None:
    selected = set(platforms)
    if "codex" in selected:
        remove_markdown_section(project_path / "AGENTS.md", "## graphify")
        remove_markdown_section_if_contains(
            project_path / "AGENTS.md",
            "## Project Scope and Ownership",
            ("graphify", "graphify-out"),
        )
        normalize_portable_graphify_command(project_path / ".codex" / "hooks.json")
    if "claude" in selected:
        remove_markdown_section(project_path / "CLAUDE.md", "## graphify")
        registration = project_path / ".claude" / "CLAUDE.md"
        remove_markdown_section(registration, "# graphify")
        if registration.is_file() and only_frontmatter(
            registration.read_text(encoding="utf-8")
        ):
            registration.unlink()
        remove_generated_graphify_pointer_lines(project_path / "CLAUDE.md")
        normalize_portable_graphify_command(
            project_path / ".claude" / "settings.json"
        )
        remove_graphify_tool_output_hooks(project_path / ".claude" / "settings.json")
    if "antigravity" in selected:
        canonical_runtime = (
            project_path / CANONICAL_SKILL_DIR / "runtime" / "antigravity"
        )
        canonical_runtime.mkdir(parents=True, exist_ok=True)
        canonical_rule = canonical_runtime / "rule.md"
        canonical_workflow = canonical_runtime / "workflow.md"
        canonical_rule.write_text(AGY_GRAPHIFY_RULE, encoding="utf-8")
        canonical_workflow.write_text(AGY_GRAPHIFY_WORKFLOW, encoding="utf-8")
        replace_file_with_link(
            project_path / ".agents" / "rules" / "graphify.md", canonical_rule
        )
        replace_file_with_link(
            project_path / ".agents" / "workflows" / "graphify.md",
            canonical_workflow,
        )


def remove_markdown_section(path: Path, heading: str) -> None:
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading),
        None,
    )
    if start is None:
        return
    level = len(heading) - len(heading.lstrip("#"))
    finish = next(
        (
            index
            for index in range(start + 1, len(lines))
            if markdown_heading_level(lines[index]) in range(1, level + 1)
        ),
        len(lines),
    )
    updated = ("".join(lines[:start]) + "".join(lines[finish:])).rstrip() + "\n"
    if updated.strip() and not only_frontmatter(updated):
        path.write_text(updated, encoding="utf-8")
    else:
        path.unlink()


def remove_markdown_section_if_contains(
    path: Path,
    heading: str,
    needles: tuple[str, ...],
) -> None:
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading),
        None,
    )
    if start is None:
        return
    level = len(heading) - len(heading.lstrip("#"))
    finish = next(
        (
            index
            for index in range(start + 1, len(lines))
            if markdown_heading_level(lines[index]) in range(1, level + 1)
        ),
        len(lines),
    )
    section = "".join(lines[start:finish]).lower()
    if any(needle.lower() in section for needle in needles):
        remove_markdown_section(path, heading)


def remove_generated_graphify_pointer_lines(path: Path) -> None:
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    generated_lines = {
        "This file only adds the project-scoped Graphify routing note for Claude.",
        "This file only indexes the project-scoped Claude Graphify skill.",
    }
    updated = "".join(
        line
        for line in content.splitlines(keepends=True)
        if line.strip() not in generated_lines
    )
    if updated != content:
        path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def normalize_portable_graphify_command(path: Path) -> None:
    if not path.is_file():
        return
    graphify = shutil.which("graphify")
    if not graphify:
        return
    content = path.read_text(encoding="utf-8")
    updated = content.replace(graphify, "graphify")
    if not updated.endswith("\n"):
        updated += "\n"
    if updated != content:
        path.write_text(updated, encoding="utf-8")


def remove_graphify_tool_output_hooks(path: Path) -> None:
    """Remove Graphify hooks that inject mandatory instructions into tool output.

    Graphify remains available through its canonical skill and explicit queries.
    Any runtime hook that invokes ``graphify hook-guard`` can inject that
    instruction path.  Preserve unrelated configuration, but remove those
    commands across every hook event and supported shell wrapper form.
    """

    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(payload, dict):
        return
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        return
    changed = False
    filtered_events: dict[str, object] = {}
    for event, registrations in hooks.items():
        if not isinstance(registrations, list):
            filtered_events[event] = registrations
            continue
        filtered_registrations: list[object] = []
        for registration in registrations:
            if not isinstance(registration, dict):
                filtered_registrations.append(registration)
                continue
            nested = registration.get("hooks")
            if not isinstance(nested, list):
                filtered_registrations.append(registration)
                continue
            remaining = [
                hook
                for hook in nested
                if not (
                    isinstance(hook, dict)
                    and isinstance(hook.get("command"), str)
                    and _is_graphify_hook_guard(hook["command"])
                )
            ]
            if len(remaining) == len(nested):
                filtered_registrations.append(registration)
            else:
                changed = True
                if remaining:
                    filtered_registrations.append({**registration, "hooks": remaining})
        if filtered_registrations:
            filtered_events[event] = filtered_registrations
    if not changed:
        return
    if filtered_events:
        payload["hooks"] = filtered_events
    else:
        payload.pop("hooks", None)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_graphify_hook_guard(command: str) -> bool:
    """Recognize direct, env-prefixed, and shell-wrapped hook-guard commands."""

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []
    for index, token in enumerate(tokens[:-1]):
        executable = Path(token).name
        if executable == "graphify" and tokens[index + 1] == "hook-guard":
            return True
    return bool(re.search(r"(?<![\w-])graphify\s+hook-guard\b", command))


def only_frontmatter(content: str) -> bool:
    stripped = content.strip()
    if not stripped.startswith("---"):
        return False
    parts = stripped.split("---")
    return len(parts) == 3 and not parts[2].strip()


def markdown_heading_level(line: str) -> int:
    stripped = line.lstrip()
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if hashes and len(stripped) > hashes and stripped[hashes] == " ":
        return hashes
    return 0
