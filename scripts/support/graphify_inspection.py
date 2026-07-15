"""Read-only Graphify canonical-source and readiness inspection."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from support.graphify_contract import (
    CANONICAL_SKILL_DIR,
    CANONICAL_SKILL_PATH,
    GLOBAL_PLATFORM_SKILL_DIRS,
    PLATFORM_CANONICAL_INTEGRATION_TARGETS,
    PLATFORM_INTEGRATION_PATHS,
    PLATFORM_SKILL_DIRS,
    TRACKING_POLICY_PATHS,
)
from support.graphify_git_tracking import inspect_graphify_git_tracking
from support.graphify_graph_state import inspect_project_graph_state
from support.graphify_input_inspection import inspect_project_graph_inputs
from support.graphify_paths import file_link_ready, runtime_link_ready


def discover_project_graphify_platforms(project_path: Path) -> list[str]:
    platforms: list[str] = []
    for platform in ("codex", "claude", "antigravity"):
        skill_dir = project_path / PLATFORM_SKILL_DIRS[platform]
        integration_paths = PLATFORM_INTEGRATION_PATHS[platform]
        if skill_dir.exists() or skill_dir.is_symlink() or any(
            (project_path / path).exists() for path in integration_paths
        ):
            platforms.append(platform)
    return platforms


def inspect_target_graphify(
    project_path: Path,
    platforms: Iterable[str] | None = None,
) -> dict[str, object]:
    selected = sorted(set(platforms or discover_project_graphify_platforms(project_path)))
    canonical_skill = project_path / CANONICAL_SKILL_PATH
    integration_paths = [
        project_path / path
        for platform in selected
        for path in PLATFORM_INTEGRATION_PATHS[platform]
    ]
    missing_integrations: list[Path] = []
    invalid_integration_links: list[Path] = []
    for path in integration_paths:
        canonical_target = PLATFORM_CANONICAL_INTEGRATION_TARGETS.get(
            path.relative_to(project_path)
        )
        if canonical_target is None:
            missing_integrations.append(path)
            continue
        if not file_link_ready(path, project_path / canonical_target):
            invalid_integration_links.append(path)
            missing_integrations.append(path)

    runtime_links = {
        platform: project_path / PLATFORM_SKILL_DIRS[platform]
        for platform in selected
    }
    invalid_links = [
        link
        for link in runtime_links.values()
        if not runtime_link_ready(link, project_path / CANONICAL_SKILL_DIR)
    ]
    missing_policies = [
        project_path / path
        for path in TRACKING_POLICY_PATHS
        if not (project_path / path).is_file()
    ]
    graph_path = project_path / "graphify-out" / "graph.json"
    cli_path = shutil.which("graphify")
    input_state = inspect_project_graph_inputs(project_path)
    graph_state = inspect_project_graph_state(project_path, graph_path)
    runtime_ready = bool(
        cli_path
        and selected
        and canonical_skill.is_file()
        and not invalid_links
        and not missing_integrations
        and not missing_policies
        and graph_path.is_file()
    )
    result = {
        "cli": cli_path,
        "platforms": selected,
        "canonical_skill_doc": str(canonical_skill),
        "canonical_skill_exists": canonical_skill.is_file(),
        "skill_docs": [str(canonical_skill)] if canonical_skill.is_file() else [],
        "runtime_skill_links": {key: str(value) for key, value in runtime_links.items()},
        "invalid_runtime_links": [str(path) for path in invalid_links],
        "integration_paths": [str(path) for path in integration_paths],
        "missing_integrations": [str(path) for path in missing_integrations],
        "invalid_runtime_integration_links": [
            str(path) for path in invalid_integration_links
        ],
        "tracking_policy_paths": [str(project_path / path) for path in TRACKING_POLICY_PATHS],
        "missing_tracking_policies": [str(path) for path in missing_policies],
        "graph_path": str(graph_path),
        "graph_exists": graph_path.is_file(),
        "runtime_ready": runtime_ready,
        **graph_state,
        **input_state,
    }
    tracking = inspect_graphify_git_tracking(project_path, selected)
    result.update(tracking)
    static_ready = bool(
        runtime_ready
        and graph_state["graph_integrity_ready"]
        and graph_state["graph_fresh"] is True
        and input_state["graph_input_policy_ready"]
        and input_state["knowledge_manifest_ready"]
        and tracking["git_repository"]
        and tracking["commit_ready"] is True
    )
    result["static_ready"] = static_ready
    result["ready"] = static_ready
    return result


def inspect_global_graphify(home_path: Path, platforms: Iterable[str]) -> dict[str, object]:
    selected = sorted(set(platforms) | {"agents"})
    canonical_skill = home_path / CANONICAL_SKILL_PATH
    runtime_links = {
        platform: home_path / GLOBAL_PLATFORM_SKILL_DIRS[platform]
        for platform in selected
    }
    invalid_links = [
        link
        for link in runtime_links.values()
        if not runtime_link_ready(link, home_path / CANONICAL_SKILL_DIR)
    ]
    cli_path = shutil.which("graphify")
    return {
        "cli": cli_path,
        "platforms": selected,
        "canonical_skill_doc": str(canonical_skill),
        "canonical_skill_exists": canonical_skill.is_file(),
        "runtime_skill_links": {key: str(value) for key, value in runtime_links.items()},
        "invalid_runtime_links": [str(path) for path in invalid_links],
        "ready": bool(cli_path and canonical_skill.is_file() and not invalid_links),
    }
