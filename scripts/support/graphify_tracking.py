"""Git and Graphify input/output tracking policies."""

from __future__ import annotations

import re
from pathlib import Path

# A managed block is found by its marker lines, so renaming the marker orphans
# every block written under the old one: the search misses it and a second block
# is appended beside it. Match the marker shape rather than a list of past names,
# so a block from any earlier naming is removed without carrying that naming
# forward here.
SUPERSEDED_MANAGED_BLOCK_PATTERN = re.compile(
    r"# (?P<name>[a-z0-9-]+)-project-assets:start[\s\S]*?"
    r"# (?P=name)-project-assets:end\n?",
    re.MULTILINE,
)

from support.graphify_contract import (
    TAO_GITIGNORE_BLOCK,
    GRAPHIFY_INPUT_BLOCK,
    GRAPHIFY_OUTPUT_GITIGNORE,
    ROOT_GITIGNORE_BLOCK,
)


def install_tracking_policies(project_path: Path) -> list[dict[str, str]]:
    policies = (
        (project_path / ".gitignore", ROOT_GITIGNORE_BLOCK),
        (
            project_path / ".tao" / ".gitignore",
            TAO_GITIGNORE_BLOCK,
        ),
    )
    results: list[dict[str, str]] = []
    for path, block in policies:
        status = write_managed_block(path, block)
        results.append(
            {
                "tool": "graphify",
                "hook": f"tracking.install.{path.name}",
                "status": status,
                "path": str(path),
            }
        )
    results.append(install_graphify_input_policy(project_path))

    output_policy = project_path / "graphify-out" / ".gitignore"
    results.append(
        {
            "tool": "graphify",
            "hook": "tracking.install.graphify-output",
            "status": write_if_missing(output_policy, GRAPHIFY_OUTPUT_GITIGNORE),
            "path": str(output_policy),
        }
    )
    return results


def install_graphify_input_policy(project_path: Path) -> dict[str, str]:
    path = project_path / ".graphifyignore"
    status = write_managed_block(path, GRAPHIFY_INPUT_BLOCK)
    if remove_legacy_runtime_blankets(path):
        status = "installed"
    gitignore = project_path / ".gitignore"
    if narrow_root_runtime_blankets(gitignore):
        status = "installed"
    return {
        "tool": "graphify",
        "hook": "tracking.install.graphify-inputs",
        "status": status,
        "path": f"{path}; {gitignore}",
    }


def remove_legacy_runtime_blankets(path: Path) -> bool:
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    begin = GRAPHIFY_INPUT_BLOCK.splitlines()[0]
    end = GRAPHIFY_INPUT_BLOCK.splitlines()[-1]
    inside_managed = False
    changed = False
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == begin:
            inside_managed = True
        if not inside_managed and _is_runtime_blanket(stripped):
            changed = True
            continue
        kept.append(line)
        if stripped == end:
            inside_managed = False
    if changed:
        path.write_text("".join(kept), encoding="utf-8")
    return changed


def narrow_root_runtime_blankets(path: Path) -> bool:
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    existing = {line.strip() for line in lines}
    replacements = {
        ".agents": (),
        ".claude": (
            ".claude/settings.json",
            ".claude/settings.local.json",
        ),
        ".codex": (".codex/hooks.json",),
    }
    changed = False
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        root = _runtime_blanket_root(stripped)
        if root is None:
            kept.append(line)
            continue
        changed = True
        ending = "\n" if line.endswith("\n") else ""
        for replacement in replacements[root]:
            if replacement not in existing:
                kept.append(replacement + ending)
                existing.add(replacement)
    if changed:
        path.write_text("".join(kept), encoding="utf-8")
    return changed


def _is_runtime_blanket(value: str) -> bool:
    return _runtime_blanket_root(value) is not None


def _runtime_blanket_root(value: str) -> str | None:
    if not value or value.startswith(("#", "!")):
        return None
    normalized = value.lstrip("/")
    if normalized.startswith("**/"):
        normalized = normalized[3:]
    for root in (".agents", ".claude", ".codex"):
        if not normalized.startswith(root):
            continue
        remainder = normalized[len(root):].strip("/")
        if not remainder or set(remainder) <= {"*", "/"}:
            return root
    return None


def write_managed_block(path: Path, block: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = original = path.read_text(encoding="utf-8") if path.exists() else ""
    begin = block.splitlines()[0]
    end = block.splitlines()[-1]
    content = SUPERSEDED_MANAGED_BLOCK_PATTERN.sub(
        lambda match: match.group(0) if match.group(0).startswith(begin) else "",
        content,
    )
    cursor = 0
    found = False
    fragments: list[str] = []
    while True:
        start = content.find(begin, cursor)
        if start < 0:
            fragments.append(content[cursor:])
            break
        finish = content.find(end, start + len(begin))
        if finish < 0:
            fragments.append(content[cursor:])
            break
        fragments.append(content[cursor:start])
        if not found:
            fragments.append(block)
            found = True
        cursor = finish + len(end)
    if found:
        updated = "".join(fragments)
    else:
        separator = "" if not content else ("" if content.endswith("\n\n") else "\n")
        updated = content + separator + block + "\n"
    if updated == original:
        return "ok"
    path.write_text(updated, encoding="utf-8")
    return "installed"


def write_if_missing(path: Path, content: str) -> str:
    if path.exists():
        return "ok"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "installed"
