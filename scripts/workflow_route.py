"""Build workflow route manifests."""

from __future__ import annotations

from typing import Optional

from workflow_catalog import (
    BASELINE_CONCERNS,
    COMMANDS,
    CONCERNS,
    CORE_DOCS,
    PLATFORM_CONCERNS,
    PLATFORMS,
)
from workflow_common import (
    ATTEMPT_LIMIT,
    RETRY_LIMIT,
    RETRY_SCOPE,
    ROOT,
    QUESTION_ROUTE_COMMANDS,
    unique,
)
from workflow_gate_policy import add_automatic_gates, automatic_docs
from workflow_parallel import parallel_execution_plan
from workflow_skill_paths import canonical_doc_path


CORE_REQUIRED_DOCS = (
    "AGENTS.md",
    "common/agent-operating-skill.md",
)

CODE_WORK_REQUIRED_DOCS = (
    "common/llm-coding-discipline.md",
    "common/code-conventions.md",
    "common/agent-editing-safety.md",
)

COMMAND_REQUIRED_DOCS = {
    "ambiguity": ("workflows/ambiguity-gate.md",),
    "bugfix": ("workflows/bugfix-debugging.md",),
    "build": ("workflows/feature-implementation.md",),
    "code-simplify": ("workflows/refactor-cleanup.md", "common/refactoring.md"),
    "commit": ("workflows/review-and-commit.md", "common/commit-workflow.md"),
    "git_commit": ("workflows/review-and-commit.md", "common/commit-workflow.md"),
    "docs": ("workflows/documentation-update.md",),
    "docs-review": ("workflows/review-and-commit.md", "common/code-review.md"),
    "feature": ("workflows/feature-implementation.md",),
    "multi-agent": ("workflows/multi-agent-collaboration.md",),
    "plan": ("workflows/planning-research.md",),
    "planning": ("workflows/planning-research.md",),
    "prd": ("workflows/prd-creation.md", "common/product-spec-to-implementation.md"),
    "product": ("workflows/product-architecture-delivery.md", "common/architecture-selection.md"),
    "refactor": ("workflows/refactor-cleanup.md", "common/refactoring.md"),
    "release": ("workflows/release-readiness.md", "common/release-deployment.md", "common/release-versioning.md"),
    "retrospective": ("workflows/retrospective-learning.md",),
    "review": ("workflows/review-and-commit.md", "common/code-review.md"),
    "ship": ("workflows/release-readiness.md", "common/release-deployment.md", "common/release-versioning.md"),
    "spec": ("workflows/prd-creation.md", "common/product-spec-to-implementation.md"),
    "task": ("workflows/agent-task-lifecycle.md",),
    "test": ("common/testing.md", "common/verification-policy.md"),
    "triage": ("workflows/request-triage.md", "common/task-intake-effort-routing.md"),
    "webperf": ("common/performance-verification.md", "common/web-performance-verification.md"),
    "workflow-setup": ("workflows/agent-task-lifecycle.md", "common/tool-failure-recovery.md"),
}

REVIEW_HOOK_REQUIRED_COMMANDS = {
    "build",
    "bugfix",
    "code-simplify",
    "commit",
    "git_commit",
    "docs",
    "docs-review",
    "feature",
    "multi-agent",
    "prd",
    "product",
    "refactor",
    "release",
    "ship",
    "spec",
    "retrospective",
    "review",
    "task",
    "workflow-setup",
}


def resolve_docs(
    command: str,
    platform: Optional[str],
    concerns: list[str],
    request_classification: Optional[dict[str, object]] = None,
    request_classified: bool = False,
    classification_evidence: str = "",
) -> dict[str, object]:
    profile = COMMANDS[command]
    docs: list[str] = [*CORE_DOCS, *profile.docs]
    docs.extend(automatic_docs(command))

    if platform:
        docs.extend(PLATFORMS[platform])

    for concern in concerns:
        docs.extend(CONCERNS.get(concern, ()))
        if platform:
            docs.extend(PLATFORM_CONCERNS.get((platform, concern), ()))

    routed_docs = unique(canonical_doc_path(doc) for doc in docs)
    required_docs = route_required_docs(command, platform, concerns, profile.docs)
    reference_docs = [doc for doc in routed_docs if doc not in set(required_docs)]
    missing = [doc for doc in routed_docs if not (ROOT / doc).exists()]
    notes = list(profile.notes)
    if command == "product" and not platform:
        notes.append("Select at least one platform card before writing ARD.")
    for concern in concerns:
        if concern in BASELINE_CONCERNS:
            notes.append(f"Concern `{concern}` is {BASELINE_CONCERNS[concern]}")

    gates = route_gates(command)
    if command not in QUESTION_ROUTE_COMMANDS:
        gates = ["request intake", *gates]

    if request_classification:
        notes.append(
            "Request classification is attached to this route; keep it as evidence for the request intake or classify request gate."
        )
    elif request_classified:
        notes.append(
            "Caller asserted the request was already classified or answered; record that evidence for the request intake gate."
        )
        if classification_evidence:
            notes.append("Request classification evidence was provided to the route command.")
    if reference_docs:
        notes.append(
            "Read `required_docs` before work; treat `reference_docs` as on-demand context only when the current task touches that concern."
        )

    return {
        "root": str(ROOT),
        "command": command,
        "platform": platform,
        "concerns": concerns,
        "request_classification": request_classification,
        "request_classified": request_classified,
        "classification_evidence": classification_evidence,
        "docs": routed_docs,
        "required_docs": required_docs,
        "reference_docs": reference_docs,
        "gates": gates,
        "hooks": route_hooks(command),
        "attempt_limit": ATTEMPT_LIMIT,
        "retry_limit": RETRY_LIMIT,
        "retry_scope": RETRY_SCOPE,
        "parallel_execution": parallel_execution_plan(command, gates),
        "gate_ledger": [
            {
                "gate": gate,
                "status": "not_started",
                "signal": "",
                "evidence": "",
            }
            for gate in gates
        ],
        "notes": notes,
        "missing": missing,
    }


def route_required_docs(
    command: str,
    platform: Optional[str],
    concerns: list[str],
    profile_docs: tuple[str, ...],
) -> list[str]:
    docs: list[str] = [*CORE_REQUIRED_DOCS, *COMMAND_REQUIRED_DOCS.get(command, profile_docs)]

    if command in {"build", "bugfix", "code-simplify", "feature", "product", "refactor", "task", "workflow-setup"}:
        docs.extend(CODE_WORK_REQUIRED_DOCS)

    if platform:
        docs.extend(PLATFORMS[platform])

    for concern in concerns:
        docs.extend(CONCERNS.get(concern, ()))
        if platform:
            docs.extend(PLATFORM_CONCERNS.get((platform, concern), ()))

    return unique(canonical_doc_path(doc) for doc in docs)


def route_gates(command: str) -> list[str]:
    gates = add_automatic_gates(command, list(COMMANDS[command].gates))
    if command not in REVIEW_HOOK_REQUIRED_COMMANDS or "review hook" in gates:
        return gates

    for anchor in ("commit readiness", "handoff", "report"):
        if anchor in gates:
            gates.insert(gates.index(anchor), "review hook")
            return gates
    gates.append("review hook")
    return gates


def route_hooks(command: str) -> list[dict[str, object]]:
    review_required = command in REVIEW_HOOK_REQUIRED_COMMANDS
    hooks: list[dict[str, object]] = [
        {
            "hook": "start",
            "required": True,
            "when": "before edits, reviews, commits, or completion reports",
            "command": (
                "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py start "
                "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
                f"--command {command} --request \"<USER_REQUEST>\""
            ),
        },
    ]
    if "route docs read" in route_gates(command):
        hooks.append(
            {
                "hook": "docs-read",
                "required": True,
                "when": "after start/preflight and before edits, reviews, commits, or completion reports; writes the required-doc receipt",
                "command": (
                    "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py docs-read "
                    "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
                    "--takeaway \"<doc-derived rule/takeaway>\" "
                    "--next-action \"<immediate task action>\" "
                    "[--receipt-output <TARGET_REPO>/.agentplaybook/route-docs-read.json]"
                ),
            }
        )
    hooks.extend(
        [
        {
            "hook": "review",
            "required": review_required,
            "when": _review_hook_timing(review_required),
            "command": _review_hook_command(command),
        },
        {
            "hook": "finish",
            "required": True,
            "when": "before final report, commit, release, or handoff",
            "command": (
                "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py finish "
                "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
                "[--gate \"<gate>=<evidence override>\"]"
            ),
        },
        ]
    )
    return hooks


def _review_hook_timing(required: bool) -> str:
    if required:
        return "after meaningful edits and before finish, commit, release, or handoff"
    return "conditional: run if the route creates or changes a diff, or before any commit"


def _review_hook_command(command: str) -> str:
    base = (
        "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py review "
        "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
        "--review-scope working-tree "
        "--code-review-evidence \"<evidence>\" "
        "--docs-freshness-evidence \"<evidence>\" "
    )
    if command in {"commit", "git_commit"}:
        return base + "[--review-path <commit-owned-path>]"
    return (
        base
        + "--structure-review-evidence \"<owner/imports/callers/verification when structure changed>\" "
        "--boundary-plan-evidence \"<owned boundary/scope and nearest verification>\" "
        "--side-effect-audit-evidence \"<final diff and side-effect audit>\" "
        "[--review-path <task-owned-path>]"
    )
