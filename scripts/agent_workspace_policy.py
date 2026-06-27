"""Workspace policy helpers shared by AgentPlaybook hooks."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def is_writing_workspace(project: Path) -> bool:
    """Return true for a draft-only writing workspace documented by AGENTS.md."""
    instructions = project / "AGENTS.md"
    drafts = project / "drafts"
    if not instructions.exists() or not drafts.is_dir():
        return False
    try:
        text = instructions.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return (
        "writing workspace instructions" in text
        or "primary workspace for blog posts" in text
        or "local_writing_workspace" in text
    )


def is_git_status_review_only(project: Path, git_status: dict[str, Any]) -> bool:
    return git_status.get("returncode") != 0 and is_writing_workspace(project)


def non_git_writing_workspace_note(project: Path) -> str:
    return (
        f"{project} is a documented writing workspace without Git tracking; "
        "treat git status/diff evidence as review-only for draft editing"
    )

