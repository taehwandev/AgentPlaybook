"""Filesystem and registry search primitives for project discovery."""

from __future__ import annotations

import json
import os
import re
import shlex
from pathlib import Path
from typing import Iterable

from agent_project_types import INSTRUCTION_FILES, PROJECT_MARKERS, ProjectCandidate
from workflow_common import unique


DEFAULT_SEARCH_ROOT_NAMES = ("Documents", "Developer", "GitHub", "Projects", "Downloads")
SKIP_SEARCH_DIRS = {
    ".git", ".hg", ".svn", ".cache", ".gradle", ".idea", ".venv",
    "build", "dist", "node_modules", "target", "DerivedData",
}


def find_project_root(start: Path) -> Path | None:
    """Return the nearest parent with project instructions or common markers."""
    current = start.expanduser()
    if current.is_file():
        current = current.parent
    current = safe_resolve(current)

    for candidate in (current, *current.parents):
        if instruction_files(candidate) or project_markers(candidate):
            return candidate
    return None


def load_registry(registry_path: Path | None = None) -> dict[str, object]:
    path = registry_path or default_registry_path()
    if not path.exists():
        return {"projects": [], "search_roots": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"projects": [], "search_roots": []}
    if isinstance(raw, list):
        return {"projects": raw, "search_roots": []}
    if isinstance(raw, dict):
        projects = raw.get("projects", [])
        search_roots = raw.get("search_roots", [])
        return {
            "projects": projects if isinstance(projects, list) else [],
            "search_roots": search_roots if isinstance(search_roots, list) else [],
        }
    return {"projects": [], "search_roots": []}


def build_candidate(path: Path, base_score: int, reason: str, source: str) -> ProjectCandidate:
    path = safe_resolve(path)
    files = instruction_files(path)
    markers = project_markers(path)
    score = base_score
    if files:
        score += 20
    if ".git" in markers:
        score += 10
    if markers:
        score += 5
    return ProjectCandidate(
        path=path,
        confidence=score,
        reasons=[reason],
        instruction_files=files,
        markers=markers,
        sources=[source],
    )


def add_candidate(candidates: dict[Path, ProjectCandidate], candidate: ProjectCandidate) -> None:
    key = safe_resolve(candidate.path)
    candidate.path = key
    if key in candidates:
        candidates[key].merge(candidate)
    else:
        candidates[key] = candidate


def explicit_request_paths(request: str, cwd: Path) -> list[Path]:
    try:
        tokens = set(shlex.split(request))
    except ValueError:
        tokens = set(request.split())
    tokens.update(match.group(0) for match in re.finditer(r"(?:~|/|\.)[^\s,;:]+", request))
    paths: list[Path] = []
    for token in tokens:
        cleaned = token.strip("\"'`.,;:)]}<>")
        if not cleaned or cleaned in {".", ".."}:
            continue
        if not (cleaned.startswith("/") or cleaned.startswith("~") or cleaned.startswith(".")):
            continue
        path = Path(cleaned).expanduser()
        if not path.is_absolute():
            path = cwd / path
        if path.exists():
            paths.append(path)
    return unique(paths)


def registry_project_path(entry: object) -> Path | None:
    if not isinstance(entry, dict):
        return None
    if entry.get("disabled") is True:
        return None
    root = entry.get("root") or entry.get("path")
    if not isinstance(root, str) or not root:
        return None
    return Path(os.path.expandvars(root)).expanduser()


def registry_search_roots(registry: dict[str, object]) -> list[Path]:
    raw = registry.get("search_roots", [])
    if not isinstance(raw, list):
        return []
    return [Path(os.path.expandvars(item)).expanduser() for item in raw if isinstance(item, str)]


def env_search_roots() -> list[Path]:
    raw = os.environ.get("AGENTPLAYBOOK_PROJECT_SEARCH_ROOTS", "")
    if not raw:
        return []
    return [
        Path(os.path.expandvars(item)).expanduser()
        for item in raw.split(os.pathsep)
        if item
    ]


def default_search_roots() -> list[Path]:
    return [Path.home() / name for name in DEFAULT_SEARCH_ROOT_NAMES]


def scan_project_roots(root: Path, *, max_depth: int, max_visited: int = 1500) -> Iterable[Path]:
    queue: list[tuple[Path, int]] = [(safe_resolve(root), 0)]
    visited = 0
    while queue and visited < max_visited:
        current, depth = queue.pop(0)
        visited += 1
        if instruction_files(current) or project_markers(current):
            yield current
        if depth >= max_depth:
            continue
        for child in iter_child_dirs(current):
            queue.append((child, depth + 1))


def usable_directory(path: Path) -> Path | None:
    path = safe_resolve(path)
    if path.is_file():
        path = path.parent
    if path.is_dir() and (instruction_files(path) or project_markers(path)):
        return path
    return None


def instruction_files(path: Path) -> list[str]:
    return [name for name in INSTRUCTION_FILES if (path / name).exists()]


def project_markers(path: Path) -> list[str]:
    return [name for name in PROJECT_MARKERS if (path / name).exists()]


def safe_resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def default_registry_path() -> Path:
    raw = os.environ.get("AGENTPLAYBOOK_PROJECT_REGISTRY")
    if raw:
        return Path(os.path.expandvars(raw)).expanduser()
    return Path.home() / ".agentplaybook" / "projects.json"


def iter_child_dirs(path: Path) -> list[Path]:
    try:
        children = sorted(path.iterdir(), key=lambda child: child.name.lower())
    except OSError:
        return []
    result = []
    for child in children:
        if child.name.startswith(".") or child.name in SKIP_SEARCH_DIRS:
            continue
        try:
            if child.is_dir():
                result.append(child)
        except OSError:
            continue
    return result
