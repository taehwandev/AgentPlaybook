"""Read-only structure checks for the AgentPlaybook review hook."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any


CommandRunner = Callable[[list[str], Path], dict[str, Any]]

REVIEW_SOURCE_FILE_LINE_LIMIT = 700
REVIEW_FILE_REVIEW_WARNING_LIMIT = 400
REVIEW_FUNCTION_LINE_LIMIT = 150
REVIEW_SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".cjs",
    ".dart",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".mjs",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sass",
    ".scss",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}
REVIEW_STYLE_EXTENSIONS = {".css", ".scss", ".sass"}
STRUCTURE_REVIEW_SCOPE_NOTE = (
    "checks changed source/style files only; Markdown, MDX, and prose docs are excluded "
    "from file-size and function-size limits"
)
REVIEW_SKIP_PARTS = {
    ".agentplaybook",
    ".git",
    ".next",
    "DerivedData",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}
PYTHON_BLOCK_RE = re.compile(r"^(\s*)(?:async\s+def|def|class)\s+([A-Za-z_]\w*)\b")
BRACE_BLOCK_RE = re.compile(
    r"^\s*(?:"
    r"(?:export\s+)?(?:async\s+)?function\s+\w+"
    r"|(?:export\s+)?(?:default\s+)?class\s+\w+"
    r"|(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>"
    r"|(?:public|private|protected|internal|static|final|open|override|async|func|fun|def|fn|"
    r"function|method|class|struct|enum|interface|type)\b.*"
    r")"
)
STYLE_BLOCK_RE = re.compile(r"^\s*[^@{}][^{}]*\{\s*$")


def structure_review(
    project: Path,
    max_file_lines: int,
    max_block_lines: int,
    run_command: CommandRunner,
) -> dict[str, Any]:
    discovery, paths = changed_source_paths(project, run_command)
    result: dict[str, Any] = {
        "checked_paths": [str(path) for path in paths],
        "checked_path_count": len(paths),
        "max_file_lines": max_file_lines,
        "max_block_lines": max_block_lines,
        "review_warning_file_lines": REVIEW_FILE_REVIEW_WARNING_LIMIT,
        "scope": STRUCTURE_REVIEW_SCOPE_NOTE,
        "warnings": [],
        "failures": list(discovery["command_errors"]),
        "discovery": discovery,
    }

    for relative in paths:
        absolute = project / relative
        try:
            lines = absolute.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            result["warnings"].append(f"{relative} is not valid UTF-8; manual structure review required")
            continue

        check_file_size(relative, lines, max_file_lines, result)
        result["failures"].extend(large_block_failures(relative, lines, max_block_lines))

    return result


def changed_source_paths(project: Path, run_command: CommandRunner) -> tuple[dict[str, Any], list[Path]]:
    commands: dict[str, Any] = {}
    names: set[str] = set()
    command_errors: list[str] = []

    head = run_command(["git", "rev-parse", "--verify", "HEAD"], project)
    commands["rev_parse_head"] = head
    if head["returncode"] == 0:
        diff = run_command(
            ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD", "--"],
            project,
        )
        commands["diff_name_only"] = diff
        if diff["returncode"] == 0:
            names.update(line.strip() for line in diff["stdout"].splitlines() if line.strip())
        else:
            command_errors.append("git diff changed source discovery failed")
    else:
        tracked = run_command(["git", "ls-files", "--cached", "--others", "--exclude-standard"], project)
        commands["ls_files_initial"] = tracked
        if tracked["returncode"] == 0:
            names.update(line.strip() for line in tracked["stdout"].splitlines() if line.strip())
        else:
            command_errors.append("git ls-files changed source discovery failed")

    untracked = run_command(["git", "ls-files", "--others", "--exclude-standard"], project)
    commands["ls_files_untracked"] = untracked
    if untracked["returncode"] == 0:
        names.update(line.strip() for line in untracked["stdout"].splitlines() if line.strip())
    else:
        command_errors.append("git ls-files untracked source discovery failed")

    paths = [Path(name) for name in sorted(names)]
    checked = [path for path in paths if review_source_path(project, path)]
    return {"commands": commands, "command_errors": command_errors}, checked


def review_source_path(project: Path, path: Path) -> bool:
    absolute = project / path
    return (
        path.suffix.lower() in REVIEW_SOURCE_EXTENSIONS
        and not any(part in REVIEW_SKIP_PARTS for part in path.parts)
        and absolute.exists()
        and absolute.is_file()
    )


def check_file_size(
    path: Path,
    lines: list[str],
    max_file_lines: int,
    result: dict[str, Any],
) -> None:
    line_count = len(lines)
    if line_count > max_file_lines:
        result["failures"].append(
            f"{path} is a changed source/style file with {line_count} lines; "
            f"hard limit is {max_file_lines}; split by responsibility or record an explicit "
            "boundary decision before approval"
        )
    elif line_count > REVIEW_FILE_REVIEW_WARNING_LIMIT:
        result["warnings"].append(
            f"{path} is a changed source/style file with {line_count} lines; "
            "structure-review evidence is required before approving more behavior"
        )


def large_block_failures(path: Path, lines: list[str], max_block_lines: int) -> list[str]:
    if path.suffix.lower() == ".py":
        return python_blocks(path, lines, max_block_lines)
    return brace_blocks(path, lines, max_block_lines)


def python_blocks(path: Path, lines: list[str], max_block_lines: int) -> list[str]:
    failures: list[str] = []
    starts: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = PYTHON_BLOCK_RE.match(line)
        if match:
            starts.append((index, count_line_indent(line), match.group(2)))

    for start_index, start_indent, name in starts:
        span = python_block_span(lines, start_index, start_indent)
        if span > max_block_lines:
            failures.append(block_failure(path, start_index, name, span, max_block_lines))
    return failures


def python_block_span(lines: list[str], start_index: int, start_indent: int) -> int:
    end_index = len(lines) - 1
    for index in range(start_index + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if count_line_indent(lines[index]) <= start_indent and not stripped.startswith("@"):
            end_index = index - 1
            break
    return end_index - start_index + 1


def count_line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def brace_blocks(path: Path, lines: list[str], max_block_lines: int) -> list[str]:
    failures: list[str] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if "{" not in stripped or not starts_review_block(path, stripped):
            continue
        span = brace_block_span(lines, index)
        if span > max_block_lines:
            label = stripped[:80].replace("`", "'")
            failures.append(block_failure(path, index, label, span, max_block_lines))
    return failures


def starts_review_block(path: Path, stripped_line: str) -> bool:
    if path.suffix.lower() in REVIEW_STYLE_EXTENSIONS:
        return bool(STYLE_BLOCK_RE.match(stripped_line))
    return bool(BRACE_BLOCK_RE.match(stripped_line))


def brace_block_span(lines: list[str], start_index: int) -> int:
    balance = 0
    for index in range(start_index, len(lines)):
        balance += lines[index].count("{") - lines[index].count("}")
        if balance <= 0:
            return index - start_index + 1
    return len(lines) - start_index


def block_failure(
    path: Path,
    start_index: int,
    label: str,
    span: int,
    max_block_lines: int,
) -> str:
    return (
        f"{path}:{start_index + 1} block `{label}` spans {span} lines; "
        f"limit is {max_block_lines}; split responsibilities or justify why the unit "
        "must stay together before approval"
    )
