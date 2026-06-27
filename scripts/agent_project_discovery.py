"""Project discovery orchestration for user-level AgentPlaybook bridges."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from agent_project_search import (
    add_candidate,
    build_candidate,
    default_search_roots,
    env_search_roots,
    explicit_request_paths,
    find_project_root,
    load_registry,
    registry_project_path,
    registry_search_roots,
    safe_resolve,
    scan_project_roots,
    usable_directory,
)
from agent_project_types import (
    DiscoveryResult,
    ProjectCandidate,
    format_discovery_text,
    format_entry_text,
)
from workflow_common import ROOT, unique


def discover_projects(
    request: str,
    cwd: Path,
    *,
    search_roots: Sequence[Path] = (),
    registry_path: Path | None = None,
    max_depth: int = 2,
    include_default_search_roots: bool = False,
) -> DiscoveryResult:
    """Find the target project for a runtime bridge without editing anything."""
    cwd = safe_resolve(cwd.expanduser())
    registry = load_registry(registry_path)
    candidates: dict[Path, ProjectCandidate] = {}

    for path in explicit_request_paths(request, cwd):
        root = find_project_root(path) or usable_directory(path)
        if root:
            add_candidate(candidates, build_candidate(root, 130, "explicit path in request", "request_path"))

    cwd_root = find_project_root(cwd)
    if cwd_root:
        add_candidate(candidates, build_candidate(cwd_root, 65, "current working directory is inside a project", "cwd"))

    request_lc = request.lower()
    for entry in registry.get("projects", []):
        path = registry_project_path(entry)
        if not path or not path.exists():
            continue
        root = find_project_root(path) or usable_directory(path)
        if not root or not isinstance(entry, dict):
            continue
        aliases = [alias for alias in entry.get("aliases", []) if isinstance(alias, str)]
        matched_aliases = [alias for alias in aliases if alias.lower() in request_lc]
        if matched_aliases or root.name.lower() in request_lc:
            candidate = build_candidate(root, 120, "registry alias or project name matched request", "registry")
            candidate.aliases = aliases
            add_candidate(candidates, candidate)

    scan_roots = _scan_roots(registry, search_roots, include_default_search_roots)
    for scan_root in scan_roots:
        if not scan_root.exists() or not scan_root.is_dir():
            continue
        for root in scan_project_roots(scan_root, max_depth=max(0, max_depth)):
            score = 35
            reason = "project marker found under configured search root"
            if root.name.lower() in request_lc:
                score += 65
                reason = "project name matched request under configured search root"
            add_candidate(candidates, build_candidate(root, score, reason, "search_root"))

    ranked = sorted(
        (_rescore_for_request(candidate, request_lc) for candidate in candidates.values()),
        key=lambda candidate: (-candidate.confidence, str(candidate.path)),
    )
    if not ranked:
        return DiscoveryResult(status="not_found", candidates=[])
    if len(ranked) == 1 or ranked[0].confidence - ranked[1].confidence >= 20:
        return DiscoveryResult(status="selected", selected=ranked[0], candidates=ranked)
    return DiscoveryResult(status="ambiguous", candidates=ranked)


def build_entry_manifest(
    request: str,
    cwd: Path,
    *,
    runtime: str,
    command: str = "task",
    search_roots: Sequence[Path] = (),
    registry_path: Path | None = None,
    max_depth: int = 2,
    include_default_search_roots: bool = False,
) -> dict[str, object]:
    result = discover_projects(
        request,
        cwd,
        search_roots=search_roots,
        registry_path=registry_path,
        max_depth=max_depth,
        include_default_search_roots=include_default_search_roots,
    )
    manifest: dict[str, object] = {
        **result.to_dict(),
        "runtime": runtime,
        "cwd": str(safe_resolve(cwd.expanduser())),
        "agentplaybook": {
            "root": str(ROOT),
            "agent_instructions": str(ROOT / "AGENTS.md"),
            "index": str(ROOT / "index.md"),
            "workflow": str(ROOT / "scripts" / "workflow.py"),
            "preflight": str(ROOT / "scripts" / "agent-preflight.py"),
            "finish_check": str(ROOT / "scripts" / "agent-finish-check.py"),
        },
        "next_steps": [],
    }
    if result.selected:
        manifest["next_steps"] = [
            "Open the selected project's runtime instruction files before project work.",
            "Run AgentPlaybook workflow routing with the current request before editing.",
            "Run preflight before edits and finish check before final report, commit, release, or handoff.",
        ]
        manifest["workflow_command"] = (
            f"python3 {ROOT / 'scripts' / 'workflow.py'} route {command} "
            "--request \"<USER_REQUEST>\""
        )
    elif result.status == "ambiguous":
        manifest["next_steps"] = [
            "Ask the user to choose one candidate before reading project docs or editing.",
            "Optionally add a stable alias to ~/.agentplaybook/projects.json.",
        ]
    else:
        manifest["next_steps"] = [
            "Ask the user for the target project path before project work.",
            "Optionally register known projects in ~/.agentplaybook/projects.json.",
        ]
    return manifest


def _scan_roots(
    registry: dict[str, object],
    search_roots: Sequence[Path],
    include_default_search_roots: bool,
) -> list[Path]:
    defaults = default_search_roots() if include_default_search_roots else []
    return unique([*registry_search_roots(registry), *env_search_roots(), *search_roots, *defaults])


def _rescore_for_request(candidate: ProjectCandidate, request_lc: str) -> ProjectCandidate:
    names = [candidate.path.name, *candidate.aliases]
    if any(name and name.lower() in request_lc for name in names):
        candidate.confidence += 12
        candidate.reasons = unique([*candidate.reasons, "candidate name appeared in request"])
    return candidate
