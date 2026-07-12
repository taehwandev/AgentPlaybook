"""Remove runtime prose copies and keep only canonical Graphify adapters."""

from __future__ import annotations

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
