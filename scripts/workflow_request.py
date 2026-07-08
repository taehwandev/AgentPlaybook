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
    RELEASE_ACTION_PATTERNS,
    REFACTOR_ACTION_PATTERNS,
    QUESTION_ACTION_PATTERNS,
    REVIEW_ACTION_PATTERNS,
    RISKY_PATTERNS,
    SCOPED_PATTERNS,
    TEST_ACTION_PATTERNS,
    WORKFLOW_SETUP_ACTION_PATTERNS,
    UI_FEATURE_ACTION_PATTERNS,
    VAGUE_PATTERNS,
)

UNRESOLVED_ANSWER_FIRST_PATTERNS = (
    r"\bdirect-question\b",
    r"\bdirect question\b",
    r"\bdirect_question\b",
    r"\banswer_first\b",
    r"\banswer-first\b",
    r"\banswer first\b",
)
UNRESOLVED_CLARIFICATION_PATTERNS = (
    r"\bvague-action\b",
    r"\bbroad-product\b",
    r"\brisky-unclear\b",
    r"\bclarify_first\b",
    r"\bclarify-first\b",
    r"\bclarify first\b",
    r"\bneeds clarification\b",
    r"\bambiguous\b",
    r"\bunclear\b",
    r"\bunknowns?\b",
    r"\bblocker questions?\b",
    r"\bask (the )?user\b",
    r"\bneeds? (a )?question\b",
    r"\bgrill_me\s*[:=]?\s*true\b",
    r"\bgrill[- ]?me\s*[:=]?\s*true\b",
    r"\bquestion_drill\s*[:=]?\s*true\b",
    r"\bquestion[- ]drill\s*[:=]?\s*true\b",
    r"\bquestion drill\s*[:=]?\s*true\b",
    r"\b모호\b",
    r"\b불명확\b",
    r"\b불확실\b",
    r"\b미정\b",
    r"\b질문 필요\b",
    r"\b확인 필요\b",
    r"\b블로커\b",
    r"\b그릴미\b",
)
EXPLICIT_UNRESOLVED_PATTERNS = (
    r"\bnot\s+(?:yet\s+)?(?:answered|clarified|resolved)\b",
    r"\bstill\s+(?:needs?|requires?)\s+(?:clarification|questions?|answers?|resolution)\b",
    r"\bstill\s+(?:ambiguous|unclear|unresolved)\b",
    r"\bunresolved\b",
    r"\bpending\s+(?:clarification|questions?|answers?|resolution)\b",
    r"(?<!\bno\s)\bopen\s+(?:questions?|blockers?)\b",
    r"(?<!\bno\s)\bblockers?\s+(?:remain|pending|open|unresolved)\b",
    r"\b아직\b.*(?:모호|불명확|불확실|미정|질문|확인|해결)",
    r"\b미해결\b",
    r"\b해결\s*(?:안|되지\s*않)",
)
CLASSIFICATION_RESOLVED_PATTERNS = (
    r"\bclear-exact\b",
    r"\bclear-scoped\b",
    r"\banswered\b.*\buser asked\b",
    r"\banswered\b.*\bseparate actionable\b",
    r"\banswered\b.*\bseparate action\b",
    r"\bblockers?\s+resolved\b",
    r"\bresolved blockers?\b",
    r"\bambiguity resolved\b",
    r"\bunknowns? resolved\b",
    r"\bno open (?:questions?|blockers?)\b",
    r"\bno blockers?\s+remain\b",
    r"\bscope clarified\b",
    r"\bdecisions? clarified\b",
    r"\bclarified decisions?\b",
    r"명확(?:한)?\s*(?:범위|스코프)",
    r"(?:질문|직접\s*질문)\s*해결.*(?:별도|추가)\s*(?:작업|요청)",
    r"(?:블로커|차단|막힌)\s*(?:질문|사항)?\s*해결",
    r"(?:모호성|불명확성|미정사항)\s*해결",
)
COMMIT_ACTION_PATTERNS = (
    r"\bcommit(?:ting|s)?\b",
    r"\bgit commit\b",
    r"\bmake a commit\b",
    r"\bcreate a commit\b",
    r"\bcommit message\b",
    r"\b커밋\b",
)
COMMIT_RELEASE_SUBSTEP_PATTERNS = (
    r"\b(first|before|current|pending|staged|working tree|worktree|warning cleanup)\b",
    r"\bbefore\s+(?:continuing|release|deploy|publishing|tagging)\b",
    r"\bcommit\b.*\b(?:then|next|after)\b",
    r"\b(?:release|deploy|publish|tag)\b.*\b(?:after|once)\b.*\bcommit\b",
    r"\b(\uba3c\uc800|\uc6b0\uc120|\ud604\uc7ac|\uc21c\uc11c\ub300\ub85c)\b",
)
COMMIT_BLOCKING_RISK_PATTERNS = (
    r"\b(delete|drop|destroy|migrate|payment|billing|secret|token|credential|permission|security|tenant)\b",
    r"\b(force[- ]?push|reset|rebase|amend)\b",
    r"\b(\uc0ad\uc81c|\ub9c8\uc774\uadf8\ub808\uc774\uc158|\ube44\ubc00|secret|token|credential|\uad8c\ud55c|\ubcf4\uc548)\b",
)
RELEASE_BLOCKING_RISK_PATTERNS = (
    r"\b(delete|drop|destroy|migrate|payment|billing|secret|token|credential|permission|security|tenant)\b",
    r"\b(\uc0ad\uc81c|\ub9c8\uc774\uadf8\ub808\uc774\uc158|\ube44\ubc00|secret|token|credential|\uad8c\ud55c|\ubcf4\uc548)\b",
)
RELEASE_SCOPE_SIGNAL_PATTERNS = (
    (
        r"\b(?:v)?\d{2,4}\.\d{1,2}\.\d+(?:[-+][A-Za-z0-9.-]+)?\b",
        r"\bversion\b",
        r"\brelease candidate\b",
        "\ubc84\uc804",
    ),
    (
        r"\b(?:source revision|commit|sha|head|main|branch|tag target|peeled target)\b",
        r"\b[0-9a-f]{7,40}\b",
        "\ucee4\ubc0b",
        "\uc18c\uc2a4",
    ),
    (
        r"\b(?:artifact|package|build|app|binary|dmg|zip|installer|bundle|appcast)\b",
        "\uc0b0\ucd9c\ubb3c",
        "\ud328\ud0a4\uc9c0",
        "\uc571",
    ),
    (
        r"\b(?:push|publish|github release|remote|origin|tag|deploy|release workflow)\b",
        "\uc6d0\uaca9",
        "\ud478\uc26c",
        "\ud0dc\uadf8",
        "\uac8c\uc2dc",
    ),
    (
        r"\b(?:verify|verification|test|build|smoke|package|sign|signed|notary|notarize|rollback|forward-fix)\b",
        "\uac80\uc99d",
        "\ud14c\uc2a4\ud2b8",
        "\ube4c\ub4dc",
        "\ub864\ubc31",
    ),
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
    has_refactor_action = _matches(REFACTOR_ACTION_PATTERNS, lowered)
    has_review_action = _matches(REVIEW_ACTION_PATTERNS, lowered)
    has_test_action = _matches(TEST_ACTION_PATTERNS, lowered)
    has_workflow_setup_action = _matches(WORKFLOW_SETUP_ACTION_PATTERNS, lowered)
    has_ui_feature_action = _matches(UI_FEATURE_ACTION_PATTERNS, lowered)
    has_commit_action = _matches(COMMIT_ACTION_PATTERNS, normalized, re.IGNORECASE)
    has_release_action = _matches(RELEASE_ACTION_PATTERNS, normalized, re.IGNORECASE)
    release_scope_signal_count = _release_scope_signal_count(normalized)
    has_release_scope = release_scope_signal_count >= 2
    commit_release_substep = has_commit_action and (
        not has_release_action or _matches(COMMIT_RELEASE_SUBSTEP_PATTERNS, normalized, re.IGNORECASE)
    )
    inspection_lacks_target = has_inspection and _inspection_lacks_target(lowered)
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
        "normalized": normalized,
        "lowered": lowered,
        "has_exact": has_exact,
        "has_scoped": has_scoped,
        "has_broad": has_broad,
        "has_risky": has_risky,
        "has_vague": has_vague,
        "has_inspection": has_inspection,
        "has_refactor_action": has_refactor_action,
        "has_review_action": has_review_action,
        "has_test_action": has_test_action,
        "has_workflow_setup_action": has_workflow_setup_action,
        "has_ui_feature_action": has_ui_feature_action,
        "has_commit_action": has_commit_action,
        "has_release_action": has_release_action,
        "has_release_scope": has_release_scope,
        "release_scope_signal_count": release_scope_signal_count,
        "commit_release_substep": commit_release_substep,
        "inspection_lacks_target": inspection_lacks_target,
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
    has_refactor_action = bool(flags["has_refactor_action"])
    has_review_action = bool(flags["has_review_action"])
    has_test_action = bool(flags["has_test_action"])
    has_workflow_setup_action = bool(flags["has_workflow_setup_action"])
    has_ui_feature_action = bool(flags["has_ui_feature_action"])
    has_commit_action = bool(flags["has_commit_action"])
    has_release_action = bool(flags["has_release_action"])
    has_release_scope = bool(flags["has_release_scope"])
    commit_release_substep = bool(flags["commit_release_substep"])
    lowered = str(flags.get("lowered") or "")
    inspection_lacks_target = bool(flags["inspection_lacks_target"])
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
    if has_commit_action and commit_release_substep and not _commit_risk_blocks(lowered):
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "quick"
        return (
            "commit",
            False,
            "work",
            "The request asks for local commit preparation or commit creation; use the lightweight commit route.",
        )
    if has_release_action and has_release_scope and not _release_risk_blocks(lowered):
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "deep"
        return (
            "release",
            False,
            "work",
            "The request names enough release context to run the release readiness route without Grill-Me.",
        )
    if has_workflow_setup_action and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return (
            "workflow-setup",
            False,
            "work",
            "The request changes document routing, natural-language discovery, or hook enforcement behavior.",
        )
    if has_ui_feature_action and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "feature", False, "work", "The request describes a scoped UI or screen feature to implement."
    if has_broad and not has_exact:
        flags["clarity"] = "broad-product"
        flags["effort"] = "deep"
        return (
            "product",
            True,
            "clarify_first",
            "Broad product or architecture work needs Grill-Me blocker-question discovery before PRD, ARD, or implementation unless existing acceptance criteria are already known.",
        )
    if has_review_action and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "review", False, "work", "The request asks to review inspectable changes or the current work surface."
    if has_refactor_action and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "code-simplify", False, "work", "The request asks for behavior-preserving code cleanup or simplification."
    if has_test_action and not has_risky:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "quick"
        return "test", False, "work", "The request asks for verification or test execution."
    if has_exact:
        flags["clarity"] = "clear-exact"
        flags["effort"] = "quick"
        return "task", False, "work", "The request names an exact file, symbol, command, or error signal."
    if has_scoped:
        flags["clarity"] = "clear-scoped"
        flags["effort"] = "standard"
        return "feature", False, "work", "The request names a scoped UI, code, or feature owner."
    if has_inspection and not has_risky and not inspection_lacks_target:
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


def _release_scope_signal_count(text: str) -> int:
    return sum(1 for patterns in RELEASE_SCOPE_SIGNAL_PATTERNS if _matches(patterns, text, re.IGNORECASE))


def _commit_risk_blocks(text: str) -> bool:
    return _matches(COMMIT_BLOCKING_RISK_PATTERNS, text.lower())


def _release_risk_blocks(text: str) -> bool:
    return _matches(RELEASE_BLOCKING_RISK_PATTERNS, text.lower())


def _inspection_lacks_target(lowered: str) -> bool:
    compact = lowered.strip(" .,!?:;")
    if not compact:
        return False
    targetless_patterns = (
        r"^(?:please\s+)?(?:check|review|inspect|verify|status|summarize|report)(?:\s+(?:it|this|that|please))?$",
        r"^(?:can you|could you|would you)\s+(?:check|review|inspect|verify|summarize|report)(?:\s+(?:it|this|that))?$",
        r"^(?:이거|그거|저거)?\s*(?:확인|체크|검토|점검|상태|파악|정리)\s*(?:해줘|해주세요|해줄래|좀)?$",
    )
    return _matches(targetless_patterns, compact)


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
        print(
            "- Start the user-visible clarification with `Grill-Me protocol /grilling session`, "
            "ask one blocker question with a recommended answer and tradeoff, then wait for feedback before work."
        )
        print("- If an external Grill-Me skill is unavailable, run the built-in blocker-question protocol and record its output.")
        print("- Record finish evidence as `grill-me if needed=</grilling session/output evidence>`.")
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


def classified_route_block_reason(command: str, classification_evidence: str) -> Optional[str]:
    """Block work routes unless --request-classified proves the request is actionable."""
    if command in QUESTION_ROUTE_COMMANDS:
        return None
    if classification_evidence_allows_command_work(command, classification_evidence):
        return None
    return (
        f"The prior request classification evidence does not prove work can start before route `{command}`. "
        "Answer direct questions first, or use `triage`/`ambiguity` and run Grill-Me or the blocker-question protocol. "
        "Rerun the work route only after evidence states clear scope, a separate actionable request, or resolved blockers."
    )


def classification_evidence_blocks_work(evidence: str) -> bool:
    normalized = " ".join(evidence.strip().lower().split())
    if not normalized:
        return True
    if _matches(EXPLICIT_UNRESOLVED_PATTERNS, normalized):
        return True
    return not _has_resolution_signal(normalized)


def _commit_evidence_allows_work(command: str, evidence: str) -> bool:
    if command not in {"commit", "git_commit"}:
        return False
    normalized = " ".join(evidence.strip().lower().split())
    if not normalized or _matches(EXPLICIT_UNRESOLVED_PATTERNS, normalized):
        return False
    return _matches(COMMIT_ACTION_PATTERNS, evidence, re.IGNORECASE)


def _release_evidence_allows_work(command: str, evidence: str) -> bool:
    if command not in {"release", "ship"}:
        return False
    normalized = " ".join(evidence.strip().lower().split())
    if not normalized or _matches(EXPLICIT_UNRESOLVED_PATTERNS, normalized):
        return False
    has_release_action = _matches(RELEASE_ACTION_PATTERNS, evidence, re.IGNORECASE)
    enough_context_without_action = _release_scope_signal_count(evidence) >= 3
    return (
        (has_release_action or enough_context_without_action)
        and _release_scope_signal_count(evidence) >= 2
        and not _release_risk_blocks(evidence)
    )


def classification_evidence_allows_command_work(command: str, evidence: str) -> bool:
    if _commit_evidence_allows_work(command, evidence):
        return True
    if _release_evidence_allows_work(command, evidence):
        return True
    return classification_evidence_allows_work(evidence)


def classification_evidence_allows_work(evidence: str) -> bool:
    return not classification_evidence_blocks_work(evidence)


def classification_evidence_requires_clarification(evidence: str) -> bool:
    normalized = " ".join(evidence.strip().lower().split())
    if not normalized:
        return False
    has_unresolved_signal = _matches(UNRESOLVED_CLARIFICATION_PATTERNS, normalized)
    has_explicit_unresolved = _matches(EXPLICIT_UNRESOLVED_PATTERNS, normalized)
    return has_explicit_unresolved or (has_unresolved_signal and not _has_resolution_signal(normalized))


def _has_resolution_signal(normalized: str) -> bool:
    return _matches(CLASSIFICATION_RESOLVED_PATTERNS, normalized)
