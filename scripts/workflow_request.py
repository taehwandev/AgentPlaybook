"""Request classification and concern inference for workflow routing."""

from __future__ import annotations

import re
from typing import Optional

from workflow_catalog import REQUEST_CONCERN_HINTS
from workflow_common import ANSWER_ONLY_CLARITY, QUESTION_ROUTE_COMMANDS, unique
from workflow_request_patterns import (
    BROAD_PATTERNS,
    DIRECT_QUESTION_PATTERNS,
    GRILL_ME_REQUEST_PATTERNS,
    EXACT_PATTERNS,
    INSPECTION_PATTERNS,
    QUESTION_ACTION_PATTERNS,
    RISKY_PATTERNS,
    SCOPED_PATTERNS,
    VAGUE_PATTERNS,
)


def infer_concerns_from_request(text: str) -> list[str]:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return []
    inferred: list[str] = []
    for concern, patterns in REQUEST_CONCERN_HINTS:
        if _matches(patterns, normalized, re.IGNORECASE):
            inferred.append(concern)
    return unique(inferred)


def classify_request(text: str) -> dict[str, object]:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    flags = _request_flags(normalized, lowered)
    route, question_drill, response_mode, reason = _classification_decision(flags)

    return {
        "request": normalized,
        "clarity": flags["clarity"],
        "effort": flags["effort"],
        "recommended_route": route,
        "grill_me": question_drill,
        "question_drill": question_drill,
        "response_mode": response_mode,
        "reason": reason,
        "notes": [
            "Answer direct user questions before routing, editing, or running project work.",
            "Use repo-local instructions before editing.",
            "Escalate effort if local inspection finds broader risk.",
            "Use the lowest capable model or reasoning depth when the runtime supports it.",
        ],
    }


def _request_flags(normalized: str, lowered: str) -> dict[str, object]:
    has_exact = _matches(EXACT_PATTERNS, normalized, re.IGNORECASE)
    has_scoped = _matches(SCOPED_PATTERNS, normalized)
    has_broad = _matches(BROAD_PATTERNS, lowered)
    has_risky = _matches(RISKY_PATTERNS, lowered)
    has_vague = _matches(VAGUE_PATTERNS, lowered)
    has_inspection = _matches(INSPECTION_PATTERNS, lowered)
    has_direct_question = _matches(DIRECT_QUESTION_PATTERNS, lowered)
    asks_agent_action = _matches(QUESTION_ACTION_PATTERNS, lowered)
    short_without_target = len(normalized.split()) <= 8 and not (has_exact or has_scoped)
    asks_drill = _matches(GRILL_ME_REQUEST_PATTERNS, lowered)
    underspecified_action = (
        asks_agent_action
        and not (has_exact or has_scoped or has_inspection)
        and not (has_direct_question and not asks_agent_action)
    )
    return {
        "has_exact": has_exact,
        "has_scoped": has_scoped,
        "has_broad": has_broad,
        "has_risky": has_risky,
        "has_vague": has_vague,
        "has_inspection": has_inspection,
        "has_direct_question": has_direct_question,
        "asks_agent_action": asks_agent_action,
        "short_without_target": short_without_target,
        "asks_drill": asks_drill,
        "underspecified_action": underspecified_action,
    }


def _classification_decision(flags: dict[str, object]) -> tuple[str, bool, str, str]:
    has_broad = bool(flags["has_broad"])
    has_exact = bool(flags["has_exact"])
    has_scoped = bool(flags["has_scoped"])
    has_risky = bool(flags["has_risky"])
    has_vague = bool(flags["has_vague"])
    has_inspection = bool(flags["has_inspection"])
    asks_drill = bool(flags["asks_drill"])

    if flags["has_direct_question"] and not flags["asks_agent_action"]:
        flags["clarity"] = ANSWER_ONLY_CLARITY
        flags["effort"] = "standard" if has_broad else "quick"
        route = "product" if has_broad else "none"
        reason = _direct_question_reason(has_broad)
        return route, False, "answer_first", reason
    if has_risky and not has_broad and not (has_exact or has_scoped):
        flags["clarity"] = "risky-unclear"
        flags["effort"] = "deep"
        return "ambiguity", True, "clarify_first", "Risk-sensitive terms appear without an exact implementation target."
    if asks_drill:
        flags["clarity"] = "vague-action"
        flags["effort"] = "deep" if has_broad or has_risky else "standard"
        return "triage", True, "clarify_first", "The request explicitly asks for the Grill-Me protocol before work."
    if has_broad and not has_exact:
        flags["clarity"] = "broad-product"
        flags["effort"] = "deep"
        return (
            "product",
            True,
            "clarify_first",
            "Broad product or architecture work needs Grill-Me blocker-question discovery before PRD, ARD, or implementation unless existing acceptance criteria are already known.",
        )
    if has_exact:
        flags["clarity"] = "clear-exact"
        flags["effort"] = "quick"
        return "task", False, "work", "The request names an exact file, symbol, command, or error signal."
    if has_scoped:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "feature", False, "work", "The request names a scoped UI, code, or feature owner."
    if has_inspection and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "task", False, "work", "The request asks for inspection, review, status, or documentation summary work with an inspectable target."
    if asks_drill or has_vague or flags["short_without_target"] or flags["underspecified_action"]:
        flags["clarity"] = "vague-action"
        flags["effort"] = "standard"
        return "triage", True, "clarify_first", "The request asks for action but lacks a precise target, inspection target, or acceptance criteria."
    flags["clarity"] = "clear-scoped"
    flags["effort"] = "standard"
    return "task", False, "work", "No high-risk ambiguity was detected, but local context is still needed."


def _direct_question_reason(has_broad: bool) -> str:
    if has_broad:
        return (
            "The request asks how to approach app/product/feature work. Answer first, "
            "but include the PRD -> ARD -> implementation gate before lower-level steps."
        )
    return "The request is a direct question, so answer it before starting any workflow or edit."


def _matches(patterns: object, text: str, flags: int = 0) -> bool:
    return any(re.search(pattern, text, flags) for pattern in patterns)


def print_classification(result: dict[str, object]) -> None:
    print("# AgentPlaybook Request Classification")
    print()
    print(f"Clarity: `{result['clarity']}`")
    print(f"Effort: `{result['effort']}`")
    print(f"Recommended route: `{result['recommended_route']}`")
    print(f"Grill-Me protocol: `{str(result['grill_me']).lower()}`")
    print(f"Response mode: `{result['response_mode']}`")
    print()
    print(f"Reason: {result['reason']}")
    print()
    print("## Next")
    if result["clarity"] == ANSWER_ONLY_CLARITY:
        print("- Answer the user's direct question first.")
        if result["recommended_route"] == "product":
            print("- Include PRD -> ARD -> implementation first; if work proceeds, run the `product` route.")
        print("- Do not start a workflow route, edit files, or run project-specific work unless a separate action remains.")
    elif result["question_drill"]:
        print("- Run `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route triage --request \"<request text>\"`.")
        print("- Use the Grill-Me `/grilling` protocol after checking available local context.")
        print("- If an external Grill-Me skill is unavailable, run the built-in blocker-question protocol and record its output.")
    else:
        print(
            f"- Run `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route {result['recommended_route']} "
            "--request \"<request text>\"` with matching platform/concerns when needed."
        )
        print("- Inspect the named target or smallest relevant local context first.")
    print("- Keep the route gate ledger current if a workflow route is used.")


def route_block_reason(
    command: str,
    classification: Optional[dict[str, object]],
) -> Optional[str]:
    if not classification:
        return None
    if classification["clarity"] == ANSWER_ONLY_CLARITY:
        reason = (
            "The current request is a direct question. Answer it in the conversation "
            "before starting a workflow route, editing files, or running project-specific work."
        )
        if classification["recommended_route"] == "product":
            reason += " Include PRD -> ARD -> implementation gates before lower-level coding steps."
        return reason
    if classification["question_drill"] and command not in QUESTION_ROUTE_COMMANDS:
        return (
            f"The current request needs clarification before route `{command}`. "
            "Use `triage` or `ambiguity`, run the Grill-Me `/grilling` protocol, "
            "and rerun the work route only after the request is clear."
        )
    if classification["recommended_route"] == "product" and command == "feature":
        return (
            "The current request is broad app/product/feature work. Use route `product` "
            "so PRD and ARD gates run before implementation; do not route it as `feature`."
        )
    return None
