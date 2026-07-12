"""Mutating Graphify setup orchestration for global and project scopes."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from support.graphify_contract import (
    CANONICAL_SKILL_DIR,
    CANONICAL_SKILL_PATH,
    GLOBAL_PLATFORM_SKILL_DIRS,
    PLATFORM_INTEGRATION_PATHS,
    PLATFORM_SKILL_DIRS,
)
from support.graphify_inspection import inspect_global_graphify, inspect_target_graphify
from support.graphify_paths import (
    detach_runtime_skill_link,
    install_canonical_skill,
    replace_path_with_relative_link,
    replace_runtime_skill_with_link,
)
from support.graphify_runtime_integration import normalize_runtime_integrations
from support.graphify_tracking import install_tracking_policies


def configure_global_graphify(
    home_path: Path,
    platforms: Iterable[str],
    dry_run: bool,
) -> list[dict[str, str]]:
    selected = sorted(set(platforms) | {"agents"})
    graphify = shutil.which("graphify")
    results = [_result("global.cli", "ok" if graphify else "missing", graphify or "graphify")]
    if graphify and not dry_run:
        installed = install_canonical_skill(graphify, home_path)
        results.append(
            _result(
                "global.skill.canonical.install",
                "installed" if installed else "missing",
                home_path / CANONICAL_SKILL_PATH,
            )
        )
        if installed:
            for platform in selected:
                replace_path_with_relative_link(
                    home_path / GLOBAL_PLATFORM_SKILL_DIRS[platform],
                    home_path / CANONICAL_SKILL_DIR,
                    target_is_directory=True,
                )

    readiness = inspect_global_graphify(home_path, selected)
    results.append(
        _result(
            "global.skill.canonical",
            "ok" if readiness["canonical_skill_exists"] else "missing",
            readiness["canonical_skill_doc"],
        )
    )
    invalid_links = set(readiness["invalid_runtime_links"])
    for platform, path in readiness["runtime_skill_links"].items():
        results.append(
            _result(
                f"global.skill_link.{platform}",
                "missing" if path in invalid_links else "ok",
                path,
            )
        )
    return results


def configure_target_graphify(
    project_path: Path,
    platforms: Iterable[str],
    dry_run: bool,
) -> list[dict[str, str]]:
    selected = sorted(set(platforms))
    graphify = shutil.which("graphify")
    results = [_result("cli", "ok" if graphify else "missing", graphify or "graphify")]
    if graphify and not dry_run:
        for platform in selected:
            detach_runtime_skill_link(project_path / PLATFORM_SKILL_DIRS[platform])
            completed = subprocess.run(
                [graphify, "install", "--project", "--platform", platform],
                cwd=project_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            results.append(
                _result(
                    f"integration.install.{platform}",
                    "installed" if completed.returncode == 0 else "missing",
                    project_path,
                )
            )

        installed = install_canonical_skill(graphify, project_path)
        results.append(
            _result(
                "skill.canonical.install",
                "installed" if installed else "missing",
                project_path / CANONICAL_SKILL_PATH,
            )
        )
        if installed:
            for platform in selected:
                replace_runtime_skill_with_link(project_path, platform)
            normalize_runtime_integrations(project_path, selected)
        results.extend(install_tracking_policies(project_path))

    readiness = inspect_target_graphify(project_path, selected)
    results.append(
        _result(
            "skill.canonical",
            "ok" if readiness["canonical_skill_exists"] else "missing",
            readiness["canonical_skill_doc"],
        )
    )
    invalid_links = set(readiness["invalid_runtime_links"])
    for platform in selected:
        link = str(project_path / PLATFORM_SKILL_DIRS[platform])
        results.append(
            _result(
                f"skill_link.{platform}",
                "missing" if link in invalid_links else "ok",
                link,
            )
        )
    missing_integrations = set(readiness["missing_integrations"])
    for platform in selected:
        for relative in PLATFORM_INTEGRATION_PATHS[platform]:
            path = str(project_path / relative)
            results.append(
                _result(
                    f"integration.{platform}.{relative.name}",
                    "missing" if path in missing_integrations else "ok",
                    path,
                )
            )
    missing_policies = set(readiness["missing_tracking_policies"])
    for path in readiness["tracking_policy_paths"]:
        results.append(
            _result(
                f"tracking.{Path(path).name}",
                "missing" if path in missing_policies else "ok",
                path,
            )
        )
    commit_ready = readiness.get("commit_ready")
    results.append(
        _result(
            "tracking.commit_boundary",
            "missing" if commit_ready is False else "ok",
            (
                f"legacy={len(readiness.get('tracked_runtime_skill_copies', []))};"
                f" untracked={len(readiness.get('canonical_untracked_files', [])) + len(readiness.get('policy_untracked_files', []))};"
                f" link_issues={len(readiness.get('runtime_link_index_issues', [])) + len(readiness.get('adapter_link_index_issues', []))};"
                f" unstaged={len(readiness.get('unstaged_commit_assets', []))};"
                f" ignored={len(readiness.get('ignored_commit_assets', []))}"
            ),
        )
    )
    results.append(
        _result(
            "graph.project",
            "ok" if readiness["graph_exists"] else "missing",
            readiness["graph_path"],
        )
    )
    return results


def _result(hook: str, status: str, path: object) -> dict[str, str]:
    return {"tool": "graphify", "hook": hook, "status": status, "path": str(path)}
