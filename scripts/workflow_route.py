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


REVIEW_HOOK_REQUIRED_COMMANDS = {
    "build",
    "bugfix",
    "code-simplify",
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

    missing = [doc for doc in unique(docs) if not (ROOT / doc).exists()]
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

    return {
        "root": str(ROOT),
        "command": command,
        "platform": platform,
        "concerns": concerns,
        "request_classification": request_classification,
        "request_classified": request_classified,
        "docs": unique(docs),
        "gates": gates,
        "hooks": route_hooks(command),
        "attempt_limit": ATTEMPT_LIMIT,
        "retry_limit": RETRY_LIMIT,
        "retry_scope": RETRY_SCOPE,
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
                "when": "after start/preflight and after reading routed docs, before edits, reviews, commits, or completion reports",
                "command": (
                    "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py docs-read "
                    "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT>"
                ),
            }
        )
    hooks.extend(
        [
        {
            "hook": "review",
            "required": review_required,
            "when": _review_hook_timing(review_required),
            "command": (
                "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py review "
                "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
                "--code-review-evidence \"<evidence>\" "
                "--docs-freshness-evidence \"<evidence>\" "
                "--structure-review-evidence \"<owner/imports/callers/verification when structure changed>\" "
                "--boundary-plan-evidence \"<owned boundary/scope and nearest verification>\" "
                "--side-effect-audit-evidence \"<final diff and side-effect audit>\""
            ),
        },
        {
            "hook": "finish",
            "required": True,
            "when": "before final report, commit, release, or handoff",
            "command": (
                "python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py finish "
                "--project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> "
                "--gate \"<gate>=<evidence>\""
            ),
        },
        ]
    )
    return hooks


def _review_hook_timing(required: bool) -> str:
    if required:
        return "after meaningful edits and before finish, commit, release, or handoff"
    return "conditional: run if the route creates or changes a diff, or before any commit"
