"""Inspect whether Graphify's canonical-source migration is commit-ready."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from support.graphify_contract import (
    CANONICAL_SKILL_DIR,
    PLATFORM_CANONICAL_INTEGRATION_TARGETS,
    PLATFORM_INTEGRATION_PATHS,
    PLATFORM_SKILL_DIRS,
    TRACKING_POLICY_PATHS,
)


def inspect_graphify_git_tracking(
    project_path: Path,
    platforms: Iterable[str],
) -> dict[str, object]:
    """Report legacy runtime copies and mandatory canonical commit assets."""
    runtime_paths = sorted(
        {PLATFORM_SKILL_DIRS[platform] for platform in platforms}, key=str
    )
    adapter_paths = sorted(
        {
            path
            for platform in platforms
            for path in PLATFORM_INTEGRATION_PATHS[platform]
            if path in PLATFORM_CANONICAL_INTEGRATION_TARGETS
        },
        key=str,
    )
    inspected_paths = [
        CANONICAL_SKILL_DIR,
        *runtime_paths,
        *adapter_paths,
        *TRACKING_POLICY_PATHS,
    ]
    entries, error = _git_index_entries(project_path, inspected_paths)
    if entries is None:
        return {
            "git_repository": False,
            "git_tracking_error": error,
            "canonical_untracked_files": [],
            "policy_untracked_files": [],
            "tracked_runtime_skill_copies": [],
            "runtime_link_index_issues": [],
            "adapter_link_index_issues": [],
            "unstaged_commit_assets": [],
            "ignored_commit_assets": [],
            "commit_ready": None,
        }

    canonical_files = _physical_files(project_path, CANONICAL_SKILL_DIR)
    canonical_untracked = [path for path in canonical_files if path not in entries]
    policy_untracked = [
        path
        for path in TRACKING_POLICY_PATHS
        if (project_path / path).is_file() and path not in entries
    ]
    tracked_copies: list[Path] = []
    runtime_link_issues: list[Path] = []
    for runtime_path in runtime_paths:
        descendants = [
            path for path in entries if _is_descendant(path, runtime_path)
        ]
        tracked_copies.extend(descendants)
        if entries.get(runtime_path) != "120000":
            runtime_link_issues.append(runtime_path)

    adapter_link_issues = [
        path
        for path in adapter_paths
        if entries.get(path) != "120000"
    ]
    unstaged_assets = _git_unstaged_paths(project_path, inspected_paths)
    ignored_candidates = [
        *canonical_untracked,
        *policy_untracked,
        *(path for path in runtime_paths if path not in entries),
        *(path for path in adapter_paths if path not in entries),
    ]
    ignored_assets = _git_ignored_paths(project_path, ignored_candidates)
    commit_ready = not (
        canonical_untracked
        or policy_untracked
        or tracked_copies
        or runtime_link_issues
        or adapter_link_issues
        or unstaged_assets
        or ignored_assets
    )
    return {
        "git_repository": True,
        "git_tracking_error": None,
        "canonical_untracked_files": _strings(canonical_untracked),
        "policy_untracked_files": _strings(policy_untracked),
        "tracked_runtime_skill_copies": _strings(tracked_copies),
        "runtime_link_index_issues": _strings(runtime_link_issues),
        "adapter_link_index_issues": _strings(adapter_link_issues),
        "unstaged_commit_assets": _strings(unstaged_assets),
        "ignored_commit_assets": _strings(ignored_assets),
        "commit_ready": commit_ready,
    }


def _git_index_entries(
    project_path: Path,
    paths: Iterable[Path],
) -> tuple[dict[Path, str] | None, str | None]:
    completed = subprocess.run(
        ["git", "ls-files", "-s", "-z", "--", *(str(path) for path in paths)],
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        error = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
        return None, error or "not a Git work tree"
    entries: dict[Path, str] = {}
    for record in (completed.stdout or b"").split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        entries[Path(raw_path.decode("utf-8", errors="surrogateescape"))] = mode
    return entries, None


def _physical_files(project_path: Path, relative_root: Path) -> list[Path]:
    root = project_path / relative_root
    if not root.is_dir() or root.is_symlink():
        return []
    return sorted(
        (path.relative_to(project_path) for path in root.rglob("*") if path.is_file()),
        key=str,
    )


def _git_unstaged_paths(project_path: Path, paths: Iterable[Path]) -> list[Path]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--", *(str(path) for path in paths)],
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return _nul_paths(completed.stdout or b"")


def _git_ignored_paths(project_path: Path, paths: Iterable[Path]) -> list[Path]:
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--", *(str(path) for path in paths)],
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode not in {0, 1}:
        return []
    return _nul_paths(completed.stdout or b"")


def _nul_paths(value: bytes) -> list[Path]:
    return [
        Path(item.decode("utf-8", errors="surrogateescape"))
        for item in value.split(b"\0")
        if item
    ]


def _is_descendant(path: Path, parent: Path) -> bool:
    return path != parent and parent in path.parents


def _strings(paths: Iterable[Path]) -> list[str]:
    return [str(path) for path in sorted(set(paths), key=str)]
