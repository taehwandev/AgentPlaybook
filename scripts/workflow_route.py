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
from workflow_doc_graph import expand_doc_matches, graph_required_docs
from workflow_gate_policy import add_automatic_gates, automatic_docs
from workflow_doc_surfaces import infer_surface_docs
from workflow_parallel import parallel_execution_plan
from workflow_skill_paths import canonical_doc_path


CORE_REQUIRED_DOCS = (
    "AGENTS.md",
    "common/skills/agent-operating-skill/SKILL.md",
)

CODE_WORK_REQUIRED_DOCS = (
    "common/skills/llm-coding-discipline/SKILL.md",
    "common/skills/code-conventions/SKILL.md",
    "common/skills/agent-editing-safety/SKILL.md",
)

COMMAND_REQUIRED_DOCS = {
    "ambiguity": ("workflows/skills/ambiguity-gate/SKILL.md",),
    "bugfix": ("workflows/skills/bugfix-debugging/SKILL.md",),
    "build": ("workflows/skills/feature-implementation/SKILL.md",),
    "code-simplify": ("workflows/skills/refactor-cleanup/SKILL.md", "common/skills/refactoring/SKILL.md"),
    "commit": ("workflows/skills/review-and-commit/SKILL.md", "common/skills/commit-workflow/SKILL.md"),
    "git_commit": ("workflows/skills/review-and-commit/SKILL.md", "common/skills/commit-workflow/SKILL.md"),
    "docs": ("workflows/skills/documentation-update/SKILL.md",),
    "docs-review": ("workflows/skills/review-and-commit/SKILL.md", "common/skills/code-review/SKILL.md"),
    "feature": ("workflows/skills/feature-implementation/SKILL.md",),
    "multi-agent": ("workflows/skills/multi-agent-collaboration/SKILL.md",),
    "plan": ("workflows/skills/planning-research/SKILL.md",),
    "planning": ("workflows/skills/planning-research/SKILL.md",),
    "prd": ("workflows/skills/prd-creation/SKILL.md", "common/skills/product-spec-to-implementation/SKILL.md"),
    "product": ("workflows/skills/product-architecture-delivery/SKILL.md", "common/skills/architecture-selection/SKILL.md"),
    "refactor": ("workflows/skills/refactor-cleanup/SKILL.md", "common/skills/refactoring/SKILL.md"),
    "release": ("workflows/skills/release-readiness/SKILL.md", "common/skills/release-deployment/SKILL.md", "common/skills/release-versioning/SKILL.md"),
    "retrospective": ("workflows/skills/retrospective-learning/SKILL.md",),
    "review": ("workflows/skills/review-and-commit/SKILL.md", "common/skills/code-review/SKILL.md"),
    "ship": ("workflows/skills/release-readiness/SKILL.md", "common/skills/release-deployment/SKILL.md", "common/skills/release-versioning/SKILL.md"),
    "spec": ("workflows/skills/prd-creation/SKILL.md", "common/skills/product-spec-to-implementation/SKILL.md"),
    "task": ("workflows/skills/agent-task-lifecycle/SKILL.md",),
    "test": ("common/skills/testing/SKILL.md", "common/skills/verification-policy/SKILL.md"),
    "triage": ("workflows/skills/request-triage/SKILL.md", "common/skills/task-intake-effort-routing/SKILL.md"),
    "webperf": ("common/skills/performance-verification/SKILL.md", "common/skills/web-performance-verification/SKILL.md"),
    "workflow-setup": ("workflows/skills/agent-task-lifecycle/SKILL.md", "common/skills/tool-failure-recovery/SKILL.md"),
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
    request_text: str = "",
    surface_paths: Optional[list[str]] = None,
) -> dict[str, object]:
    profile = COMMANDS[command]
    docs: list[str] = [*CORE_DOCS, *profile.docs]
    docs.extend(automatic_docs(command))
    surface_docs, surface_matches = infer_surface_docs(
        command=command,
        platform=platform,
        request_text=request_text,
        surface_paths=surface_paths or [],
    )
    doc_graph_matches = expand_doc_matches(
        ROOT,
        surface_docs,
        max_depth=1,
        max_docs=24,
        relation_prefixes=("frontmatter:", "markdown:", "compat:"),
    )
    graph_docs = [str(match["path"]) for match in doc_graph_matches]
    graph_required = graph_required_docs(doc_graph_matches)
    docs.extend(surface_docs)
    docs.extend(graph_docs)

    if platform:
        docs.extend(PLATFORMS[platform])

    for concern in concerns:
        docs.extend(CONCERNS.get(concern, ()))
        if platform:
            docs.extend(PLATFORM_CONCERNS.get((platform, concern), ()))

    routed_docs = unique(canonical_doc_path(doc) for doc in docs)
    required_docs = route_required_docs(command, platform, concerns, profile.docs, [*surface_docs, *graph_required])
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
    if surface_matches:
        notes.append(
            "Promoted required docs from request intent or touched path surfaces using `workflow-doc-surfaces.json`."
        )
    if doc_graph_matches:
        notes.append(
            "Expanded related candidate docs from the local document graph; explicit `requires_docs` edges become required docs."
        )

    route = {
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
    if surface_paths:
        route["surface_paths"] = surface_paths
    if surface_matches:
        route["doc_surface_matches"] = surface_matches
    if doc_graph_matches:
        route["doc_graph_matches"] = doc_graph_matches
    return route


def route_required_docs(
    command: str,
    platform: Optional[str],
    concerns: list[str],
    profile_docs: tuple[str, ...],
    surface_docs: list[str] | None = None,
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

    docs.extend(surface_docs or [])
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
