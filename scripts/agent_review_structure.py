"""Read-only structure checks for the AgentPlaybook review hook."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent_review_boundary import boundary_note_requirements
from agent_review_purpose import purpose_failures
from agent_structure_rules import structure_rule_review
from agent_workspace_policy import is_writing_workspace


CommandRunner = Callable[[list[str], Path], dict[str, Any]]

REVIEW_SOURCE_FILE_LINE_LIMIT = 500
REVIEW_FILE_REVIEW_WARNING_LIMIT = 300
REVIEW_ADDED_LINE_LIMIT = 200
REVIEW_FUNCTION_LINE_LIMIT = 120
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
    "checks only changed files in the development-file extension allowlist; tests, "
    "fixtures, mocks, specs, generated or pinned third-party files, config/build files, Markdown, MDX, "
    "and prose docs are excluded from runtime hard gates"
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
REVIEW_GENERATED_PARTS = {"__generated__", "generated", "gen"}
REVIEW_CONFIG_FILE_NAMES = {
    "package.swift",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "setup.py",
}
REVIEW_CONFIG_SUFFIXES = (
    ".config.cjs", ".config.js", ".config.mjs", ".config.mts", ".config.py",
    ".config.ts", ".conf.js", ".conf.ts", ".gradle", ".gradle.kts",
)
TEST_PATH_PARTS = {
    "__fixtures__",
    "__mocks__",
    "__tests__",
    "fixture",
    "fixtures",
    "mock",
    "mocks",
    "spec",
    "specs",
    "test",
    "tests",
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
    review_paths: list[str] | None = None,
) -> dict[str, Any]:
    discovery, paths = changed_source_paths(project, run_command, review_paths)
    result: dict[str, Any] = {
        "checked_paths": [str(path) for path in paths],
        "checked_path_count": len(paths),
        "development_extensions": sorted(REVIEW_SOURCE_EXTENSIONS),
        "strict_checked_paths": [],
        "test_exempt_paths": [],
        "max_file_lines": max_file_lines,
        "max_block_lines": max_block_lines,
        "max_added_lines": REVIEW_ADDED_LINE_LIMIT,
        "review_warning_file_lines": REVIEW_FILE_REVIEW_WARNING_LIMIT,
        "scope": STRUCTURE_REVIEW_SCOPE_NOTE,
        "warnings": [],
        "failures": list(discovery["command_errors"]),
        "boundary_note_requirements": [],
        "discovery": discovery,
    }

    for relative in paths:
        if test_exempt_path(relative):
            result["test_exempt_paths"].append(str(relative))
            continue

        result["strict_checked_paths"].append(str(relative))
        absolute = project / relative
        try:
            lines = absolute.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            result["warnings"].append(f"{relative} is not valid UTF-8; manual structure review required")
            continue

        metadata = discovery["path_metadata"].get(str(relative), {})
        check_file_size(relative, lines, max_file_lines, metadata, result)
        block_failures, block_warnings = large_block_findings(
            project,
            relative,
            lines,
            max_block_lines,
            metadata,
            run_command,
        )
        result["failures"].extend(block_failures)
        result["warnings"].extend(block_warnings)
    result["failures"].extend(
        purpose_failures(
            project,
            paths,
            discovery["path_metadata"],
            review_source_path,
            test_exempt_path,
            run_command,
        )
    )
    structure_rules = structure_rule_review(
        project,
        paths,
        discovery["path_metadata"],
        review_source_path,
        test_exempt_path,
    )
    result["structure_rules"] = structure_rules
    result["failures"].extend(structure_rules["failures"])
    result["warnings"].extend(structure_rules["warnings"])
    result["boundary_note_requirements"] = boundary_note_requirements(
        project,
        paths,
        discovery["path_metadata"],
        run_command,
        review_source_path,
        test_exempt_path,
    )

    return result


def changed_source_paths(
    project: Path,
    run_command: CommandRunner,
    review_paths: list[str] | None = None,
) -> tuple[dict[str, Any], list[Path]]:
    commands: dict[str, Any] = {}
    names: set[str] = set()
    path_metadata: dict[str, dict[str, Any]] = {}
    command_errors: list[str] = []

    head = run_command(["git", "rev-parse", "--verify", "HEAD"], project)
    commands["rev_parse_head"] = head
    if head["returncode"] != 0 and is_writing_workspace(project):
        return {
            "commands": commands,
            "command_errors": [],
            "path_metadata": path_metadata,
            "review_only": "non_git_writing_workspace",
        }, []
    if head["returncode"] == 0:
        collect_head_diff(project, run_command, commands, names, path_metadata, command_errors, review_paths)
    else:
        tracked = run_command(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", *_pathspec_args(review_paths)],
            project,
        )
        commands["ls_files_initial"] = tracked
        if tracked["returncode"] == 0:
            for line in tracked["stdout"].splitlines():
                name = line.strip()
                if name:
                    record_path(names, path_metadata, name, status="A")
        else:
            command_errors.append("git ls-files changed source discovery failed")

    untracked = run_command(
        ["git", "ls-files", "--others", "--exclude-standard", *_pathspec_args(review_paths)],
        project,
    )
    commands["ls_files_untracked"] = untracked
    if untracked["returncode"] == 0:
        for line in untracked["stdout"].splitlines():
            name = line.strip()
            if name:
                record_path(names, path_metadata, name, status="A", untracked=True)
    else:
        command_errors.append("git ls-files untracked source discovery failed")

    paths = [Path(name) for name in sorted(names)]
    checked = [path for path in paths if review_source_path(project, path)]
    return {
        "commands": commands,
        "command_errors": command_errors,
        "path_metadata": path_metadata,
    }, checked


def collect_head_diff(
    project: Path,
    run_command: CommandRunner,
    commands: dict[str, Any],
    names: set[str],
    path_metadata: dict[str, dict[str, Any]],
    command_errors: list[str],
    review_paths: list[str] | None = None,
) -> None:
    pathspec = _pathspec_args(review_paths)
    status = run_command(
        ["git", "diff", "--name-status", "--diff-filter=ACMRTUXB", "HEAD", *pathspec],
        project,
    )
    commands["diff_name_status"] = status
    if status["returncode"] == 0:
        for line in status["stdout"].splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                record_path(names, path_metadata, parts[-1], status=parts[0][:1])
    else:
        command_errors.append("git diff changed source discovery failed")

    numstat = run_command(
        ["git", "diff", "--numstat", "--diff-filter=ACMRTUXB", "HEAD", *pathspec],
        project,
    )
    commands["diff_numstat"] = numstat
    if numstat["returncode"] == 0:
        for line in numstat["stdout"].splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                additions = int(parts[0]) if parts[0].isdigit() else 0
                record_path(names, path_metadata, parts[-1], additions=additions)
    else:
        command_errors.append("git diff line-count discovery failed")


def record_path(
    names: set[str],
    path_metadata: dict[str, dict[str, Any]],
    name: str,
    **updates: Any,
) -> None:
    names.add(name)
    path_metadata.setdefault(name, {}).update(updates)


def _pathspec_args(review_paths: list[str] | None) -> list[str]:
    paths = [path.strip() for path in (review_paths or []) if path.strip()]
    return ["--", *paths] if paths else ["--"]


def review_source_path(project: Path, path: Path) -> bool:
    absolute = project / path
    return (
        path.suffix.lower() in REVIEW_SOURCE_EXTENSIONS
        and not any(part in REVIEW_SKIP_PARTS for part in path.parts)
        and not config_or_generated_path(path)
        and not pinned_third_party_source(project, path)
        and absolute.exists()
        and absolute.is_file()
    )


def config_or_generated_path(path: Path) -> bool:
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts.intersection(REVIEW_GENERATED_PARTS):
        return True

    name = path.name.lower()
    return name in REVIEW_CONFIG_FILE_NAMES or name.endswith(REVIEW_CONFIG_SUFFIXES)


def pinned_third_party_source(project: Path, path: Path) -> bool:
    """Recognize an isolated vendor package only when provenance is present."""
    lower_parts = [part.lower() for part in path.parts]
    try:
        boundary = lower_parts.index("third_party")
    except ValueError:
        return False
    if boundary + 1 >= len(path.parts):
        return False

    package = project.joinpath(*path.parts[: boundary + 2])
    readme = package / "README.md"
    license_file = package / "LICENSE"
    if not readme.is_file() or not license_file.is_file():
        return False
    try:
        provenance = readme.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return all(marker in provenance for marker in ("upstream", "commit", "sha-256", "license"))


def test_exempt_path(path: Path) -> bool:
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts.intersection(TEST_PATH_PARTS):
        return True

    stem = path.stem
    lower_stem = stem.lower()
    return (
        lower_stem.startswith(("test_", "test-"))
        or lower_stem.endswith(("_test", "-test", ".test", "_tests", "-tests", ".tests"))
        or lower_stem.endswith(("_spec", "-spec", ".spec", "_specs", "-specs", ".specs"))
        or stem.endswith(("Test", "Tests", "Spec", "Specs"))
    )


def check_file_size(
    path: Path,
    lines: list[str],
    max_file_lines: int,
    metadata: dict[str, Any],
    result: dict[str, Any],
) -> None:
    line_count = len(lines)
    status = metadata.get("status", "")
    added_lines = metadata.get("additions")
    if added_lines is None:
        added_lines = line_count if status == "A" else 0

    if status == "A" and line_count > max_file_lines:
        result["failures"].append(
            f"{path} is a new development source/style file with {line_count} lines; "
            f"new-file hard limit is {max_file_lines}; split by responsibility before approval"
        )
    if added_lines > REVIEW_ADDED_LINE_LIMIT:
        result["failures"].append(
            f"{path} adds {added_lines} lines in one development source/style file; "
            f"per-file addition limit is {REVIEW_ADDED_LINE_LIMIT}; split the change before approval"
        )
    if status != "A" and line_count > max_file_lines and added_lines > 0:
        result["warnings"].append(
            f"{path} is already over {max_file_lines} lines and adds {added_lines} line(s); "
            "structure-review evidence is required and the new responsibility should be extracted "
            "when it expands the public owner surface"
        )
    elif line_count > REVIEW_FILE_REVIEW_WARNING_LIMIT:
        result["warnings"].append(
            f"{path} is a changed development source/style file with {line_count} lines; "
            f"review-pressure limit is {REVIEW_FILE_REVIEW_WARNING_LIMIT}; "
            "structure-review evidence is required before approving more behavior"
        )


def large_block_failures(path: Path, lines: list[str], max_block_lines: int) -> list[str]:
    failures, _warnings = large_block_findings(
        Path("."),
        path,
        lines,
        max_block_lines,
        {"status": "A"},
        lambda _command, _cwd: {"returncode": 1, "stdout": "", "stderr": ""},
    )
    return failures


def large_block_findings(
    project: Path,
    path: Path,
    lines: list[str],
    max_block_lines: int,
    metadata: dict[str, Any],
    run_command: CommandRunner,
) -> tuple[list[str], list[str]]:
    current = oversized_blocks(path, lines, max_block_lines)
    if not current:
        return [], []

    previous = previous_oversized_blocks(project, path, metadata, run_command, max_block_lines)
    previous_by_label = {str(record["label"]): record for record in previous}
    failures: list[str] = []
    warnings: list[str] = []
    for record in current:
        previous_record = previous_by_label.get(str(record["label"]))
        if previous_record and int(record["span"]) <= int(previous_record["span"]):
            warnings.append(preexisting_block_warning(record, int(previous_record["span"]), max_block_lines))
        else:
            failures.append(block_failure(record, max_block_lines))
    return failures, warnings


def previous_oversized_blocks(
    project: Path,
    path: Path,
    metadata: dict[str, Any],
    run_command: CommandRunner,
    max_block_lines: int,
) -> list[dict[str, Any]]:
    if metadata.get("status") == "A":
        return []
    previous = run_command(["git", "show", f"HEAD:{path.as_posix()}"], project)
    if previous.get("returncode") != 0:
        return []
    return oversized_blocks(path, str(previous.get("stdout") or "").splitlines(), max_block_lines)


def oversized_blocks(path: Path, lines: list[str], max_block_lines: int) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".py":
        return python_blocks(path, lines, max_block_lines)
    return brace_blocks(path, lines, max_block_lines)


def python_blocks(path: Path, lines: list[str], max_block_lines: int) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    starts: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = PYTHON_BLOCK_RE.match(line)
        if match:
            starts.append((index, count_line_indent(line), match.group(2)))

    for start_index, start_indent, name in starts:
        span = python_block_span(lines, start_index, start_indent)
        if span > max_block_lines:
            blocks.append(block_record(path, start_index, name, span))
    return blocks


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


def brace_blocks(path: Path, lines: list[str], max_block_lines: int) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if "{" not in stripped or not starts_review_block(path, stripped):
            continue
        span = brace_block_span(lines, index)
        if span > max_block_lines:
            label = stripped[:80].replace("`", "'")
            blocks.append(block_record(path, index, label, span))
    return blocks


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


def block_record(path: Path, start_index: int, label: str, span: int) -> dict[str, Any]:
    return {
        "path": path,
        "line": start_index + 1,
        "label": label,
        "span": span,
    }


def block_failure(record: dict[str, Any], max_block_lines: int) -> str:
    return (
        f"{record['path']}:{record['line']} block `{record['label']}` spans {record['span']} lines; "
        f"limit is {max_block_lines}; split responsibilities or justify why the unit "
        "must stay together before approval"
    )


def preexisting_block_warning(
    record: dict[str, Any],
    previous_span: int,
    max_block_lines: int,
) -> str:
    return (
        f"{record['path']}:{record['line']} block `{record['label']}` is a pre-existing "
        f"oversized unit spanning {record['span']} lines (previously {previous_span}); "
        f"limit is {max_block_lines}; structure-review evidence is required, but this "
        "does not block the current scoped change unless the diff grows the unit or adds "
        "a new responsibility"
    )
