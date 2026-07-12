"""Canonical Graphify bundle staging and relative-link helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from support.graphify_contract import (
    CANONICAL_SKILL_DIR,
    CANONICAL_SKILL_REPLACEMENTS,
    PLATFORM_SKILL_DIRS,
)


def install_canonical_skill(graphify: str, project_path: Path) -> bool:
    with tempfile.TemporaryDirectory(prefix="agentplaybook-graphify-") as temp_dir:
        stage_project = Path(temp_dir)
        completed = subprocess.run(
            [graphify, "install", "--project", "--platform", "agents"],
            cwd=stage_project,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        source = stage_project / PLATFORM_SKILL_DIRS["agents"]
        skill_path = source / "SKILL.md"
        if completed.returncode != 0 or not skill_path.is_file():
            return False
        try:
            skill_path.write_text(
                make_skill_runtime_neutral(skill_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
        except (OSError, ValueError):
            return False

        canonical = project_path / CANONICAL_SKILL_DIR
        canonical.parent.mkdir(parents=True, exist_ok=True)
        staged = Path(
            tempfile.mkdtemp(prefix=".graphify-canonical-", dir=canonical.parent)
        )
        shutil.copytree(source, staged, dirs_exist_ok=True)
        backup = canonical.parent / ".graphify-canonical.previous"
        remove_path(backup)
        if canonical.exists() or canonical.is_symlink():
            os.replace(canonical, backup)
        try:
            os.replace(staged, canonical)
        except OSError:
            if backup.exists() or backup.is_symlink():
                os.replace(backup, canonical)
            remove_path(staged)
            return False
        remove_path(backup)
        return True


def make_skill_runtime_neutral(content: str) -> str:
    for source, replacement in CANONICAL_SKILL_REPLACEMENTS:
        if source not in content:
            raise ValueError("Graphify canonicalization marker is missing")
        content = content.replace(source, replacement, 1)
    return content


def detach_runtime_skill_link(skill_dir: Path) -> None:
    if skill_dir.is_symlink():
        skill_dir.unlink()


def replace_runtime_skill_with_link(project_path: Path, platform: str) -> None:
    replace_path_with_relative_link(
        project_path / PLATFORM_SKILL_DIRS[platform],
        project_path / CANONICAL_SKILL_DIR,
        target_is_directory=True,
    )


def runtime_link_ready(link: Path, canonical: Path) -> bool:
    if not link.is_symlink() or not (link / "SKILL.md").is_file():
        return False
    try:
        return link.resolve(strict=True) == canonical.resolve(strict=True)
    except OSError:
        return False


def file_link_ready(link: Path, canonical: Path) -> bool:
    if not link.is_symlink() or not link.is_file():
        return False
    try:
        return link.resolve(strict=True) == canonical.resolve(strict=True)
    except OSError:
        return False


def replace_file_with_link(link: Path, target: Path) -> None:
    replace_path_with_relative_link(link, target, target_is_directory=False)


def replace_path_with_relative_link(
    link: Path,
    target: Path,
    *,
    target_is_directory: bool,
) -> None:
    remove_path(link)
    link.parent.mkdir(parents=True, exist_ok=True)
    relative_target = os.path.relpath(target, start=link.parent)
    link.symlink_to(relative_target, target_is_directory=target_is_directory)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
