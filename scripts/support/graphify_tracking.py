"""Git and Graphify input/output tracking policies."""

from pathlib import Path

from support.graphify_contract import (
    AGENTPLAYBOOK_GITIGNORE_BLOCK,
    GRAPHIFY_INPUT_BLOCK,
    GRAPHIFY_OUTPUT_GITIGNORE,
    ROOT_GITIGNORE_BLOCK,
)


def install_tracking_policies(project_path: Path) -> list[dict[str, str]]:
    policies = (
        (project_path / ".gitignore", ROOT_GITIGNORE_BLOCK),
        (
            project_path / ".agentplaybook" / ".gitignore",
            AGENTPLAYBOOK_GITIGNORE_BLOCK,
        ),
        (project_path / ".graphifyignore", GRAPHIFY_INPUT_BLOCK),
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


def write_managed_block(path: Path, block: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    begin = block.splitlines()[0]
    end = block.splitlines()[-1]
    start = content.find(begin)
    finish = content.find(end, start + len(begin)) if start >= 0 else -1
    if start >= 0 and finish >= 0:
        finish += len(end)
        updated = content[:start] + block + content[finish:]
    else:
        separator = "" if not content else ("" if content.endswith("\n\n") else "\n")
        updated = content + separator + block + "\n"
    if updated == content:
        return "ok"
    path.write_text(updated, encoding="utf-8")
    return "installed"


def write_if_missing(path: Path, content: str) -> str:
    if path.exists():
        return "ok"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "installed"
