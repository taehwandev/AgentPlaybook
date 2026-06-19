"""Review-hook execution for AgentPlaybook."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent_review_boundary import format_boundary_note_requirements, missing_boundary_note_fields
from agent_review_structure import structure_review


CommandRunner = Callable[[list[str], Path], dict[str, Any]]


def review_hook(
    args: Any,
    run_command: CommandRunner,
    git_status: Callable[[Path], tuple[dict[str, Any], list[str]]],
    vibeguard_command: Callable[[Path, Path], list[str]],
    parse_overall: Callable[[str], str],
    finish_with_result: Callable[[str, bool, list[str], Path | None, dict[str, Any], int], int],
) -> int:
    checks: dict[str, Any] = {}
    failures: list[str] = []
    review_evidence = (args.code_review_evidence or "").strip()
    docs_evidence = (args.docs_freshness_evidence or "").strip()
    structure_evidence = (args.structure_review_evidence or "").strip()
    checks.update(
        code_review_evidence=review_evidence,
        docs_freshness_evidence=docs_evidence,
        structure_review_evidence=structure_evidence,
    )
    if not review_evidence:
        failures.append("code review evidence is required")
    if not docs_evidence:
        failures.append("docs freshness evidence is required")

    status_before, status_before_lines = git_status(args.project)
    checks["git_status_before"] = status_before
    checks["changed_path_count"] = len(status_before_lines)
    checks["changed_path_limit"] = args.max_changed_paths
    if status_before["returncode"] != 0:
        failures.append("git status failed")
    elif len(status_before_lines) > args.max_changed_paths:
        failures.append(
            f"review scope has {len(status_before_lines)} changed paths; "
            f"limit is {args.max_changed_paths}; split the change or run a smaller review scope"
        )

    structure = structure_review(args.project, args.max_source_file_lines, args.max_function_lines, run_command)
    checks["structure_review"] = structure
    failures.extend(f"structure review: {failure}" for failure in structure["failures"])
    failures.extend(structure_evidence_failures(structure, structure_evidence))

    diff_check = run_command(["git", "diff", "--check"], args.project)
    checks["diff_check"] = diff_check
    if diff_check["returncode"] != 0:
        failures.append("git diff --check failed")

    validate_script = args.rules / "scripts" / "workflow.py"
    if validate_script.exists():
        validate = run_command([sys.executable, str(validate_script), "validate"], args.rules)
        checks["workflow_validate"] = validate
        if validate["returncode"] != 0:
            failures.append("workflow validate failed")
    else:
        failures.append(f"workflow validate script missing at {validate_script}")

    vibeguard = run_command(vibeguard_command(args.project, args.rules), args.project)
    vibeguard["overall"] = parse_overall(vibeguard["stdout"] + "\n" + vibeguard["stderr"])
    checks["vibeguard"] = vibeguard
    if vibeguard["returncode"] != 0:
        failures.append("VibeGuard audit failed")
    elif vibeguard["overall"] != "Ready":
        failures.append(f"VibeGuard overall is {vibeguard['overall']}")

    status_after, status_after_lines = git_status(args.project)
    checks["git_status_after"] = status_after
    if status_after["returncode"] != 0:
        failures.append("git status failed")
    elif status_after_lines != status_before_lines:
        failures.append("review hook changed the worktree; review hooks must stay read-only")

    details = review_failure_details(failures, structure) if failures else review_success_details(structure)
    return finish_with_result("review", not failures, details, args.output, checks, args.retry_attempt)


def structure_evidence_failures(structure: dict[str, Any], structure_evidence: str) -> list[str]:
    failures: list[str] = []
    if structure["warnings"] and not structure_evidence:
        warning_summary = "; ".join(structure["warnings"][:5])
        if len(structure["warnings"]) > 5:
            warning_summary += "; ..."
        failures.append(f"structure review evidence is required: {warning_summary}")
    boundary_requirements = structure.get("boundary_note_requirements", [])
    missing_fields = missing_boundary_note_fields(structure_evidence) if boundary_requirements else []
    if missing_fields:
        failures.append(
            "structure boundary note evidence is required for "
            f"{format_boundary_note_requirements(boundary_requirements)}; "
            "structure-review-evidence must explicitly include owner, allowed imports, "
            f"forbidden imports, callers/tests, and verification. Missing: {', '.join(missing_fields)}"
        )
    return failures


def review_success_details(structure: dict[str, Any]) -> list[str]:
    return [
        "code review evidence recorded",
        "docs freshness evidence recorded",
        f"structure review passed for {structure['checked_path_count']} development source/style file(s)",
        f"structure scope: {structure['scope']}",
        "review scope guard passed",
        "review hook left worktree unchanged",
        "diff whitespace check passed",
        "workflow validation passed",
        "VibeGuard audit passed",
    ]


def review_failure_details(failures: list[str], structure: dict[str, Any]) -> list[str]:
    details = [
        f"structure scope: {structure['scope']}",
        f"checked development source/style files: {format_checked_paths(structure.get('checked_paths', []))}",
    ]
    details.extend(f"failure detail: {failure}" for failure in failures)
    details.append("required recovery: fix scoped and safe code/docs issues immediately outside the hook, then rerun this same review hook once with --retry-attempt 1")
    details.append("do not finalize with FAIL; ask only when recovery needs a scope decision, destructive action, credential change, external state, or a broader refactor")
    return details


def format_checked_paths(paths: list[str]) -> str:
    if not paths:
        return "none"
    visible = paths[:8]
    suffix = "" if len(paths) <= len(visible) else f" ... (+{len(paths) - len(visible)} more)"
    return ", ".join(visible) + suffix
