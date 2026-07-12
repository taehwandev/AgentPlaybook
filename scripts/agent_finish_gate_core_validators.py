"""Core finish gate evidence validators."""

from __future__ import annotations

import re


GENERIC_ROUTE_DOCS_TAKEAWAY_PHRASES = (
    "docs-read receipt",
    "docs read receipt",
    "route docs receipt",
    "receipt matched",
    "receipt completed",
    "current preflight manifest",
    "preflight manifest",
    "required docs read",
    "routed docs read",
    "checked docs",
    "read docs",
)

SPECIFIC_ROUTE_DOCS_TAKEAWAY_MARKERS = (
    "alignment",
    "ambiguity",
    "boundary",
    "cycle",
    "documentation",
    "evidence",
    "gate",
    "policy",
    "criterion",
    "criteria",
    "review",
    "scope",
    "source",
    "test",
    "verify",
    "vibeguard",
    "workflow",
    "적용",
    "반영",
    "기준",
    "규칙",
    "증거",
)

NEXT_ACTION_WORD_MARKERS = (
    "analyze",
    "apply",
    "ask",
    "block",
    "check",
    "choose",
    "compare",
    "diagnose",
    "enforce",
    "fix",
    "implement",
    "inspect",
    "read",
    "record",
    "review",
    "rerun",
    "run",
    "search",
    "stop",
    "test",
    "trace",
    "update",
    "verify",
    "write",
)

NEXT_ACTION_PHRASE_MARKERS = (
    "continue by",
)

NEXT_ACTION_KOREAN_STEMS = (
    "검색",
    "검토",
    "검증",
    "기록",
    "비교",
    "분석",
    "선택",
    "실행",
    "작성",
    "적용",
    "점검",
    "조사",
    "질문",
    "중단",
    "추적",
    "확인",
    "반영",
    "수정",
    "구현",
)

NEXT_ACTION_NEGATIONS = (
    "do not",
    "don't",
    "never",
    "not yet",
)


def validate_route_docs_application_fields(takeaway: str, next_action: str) -> list[str]:
    failures: list[str] = []
    if _is_generic_route_docs_takeaway(takeaway):
        failures.append(
            "route docs read evidence must name a task-specific rule, criterion, "
            "policy, or takeaway from the required docs; receipt or manifest "
            "matching alone is not enough"
        )
    if not _has_actionable_next_action(next_action):
        failures.append(
            "route docs read evidence must name the immediate next action that "
            "applies the discovered docs to the current task"
        )
    return failures


def validate_route_docs_read(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_read_action = any(
        phrase in text
        for phrase in (
            "read",
            "opened",
            "loaded",
            "consulted",
            "checked",
            "읽",
            "확인",
        )
    )
    names_route_docs = any(
        phrase in text
        for phrase in (
            "route docs",
            "routed docs",
            "read in order",
            "required docs",
            "required_docs",
            "read first",
            "skill docs",
            "guidance docs",
            ".md",
            "agents.md",
            "index.md",
        )
    )
    before_work = any(
        phrase in text
        for phrase in (
            "before code",
            "before coding",
            "before implementation",
            "before edit",
            "before edits",
            "before commit",
            "before commits",
            "before committing",
            "before stage",
            "before staging",
            "before work",
            "pre-code",
            "pre implementation",
            "코드 전",
            "구현 전",
            "수정 전",
            "작업 전",
        )
    )
    applied_to_work = any(
        phrase in text
        for phrase in (
            "applied",
            "used",
            "takeaway",
            "takeaways",
            "criterion",
            "criteria",
            "rule",
            "policy",
            "checked against",
            "matched against",
            "적용",
            "반영",
            "기준",
            "규칙",
        )
    )
    names_next_action = any(
        phrase in text
        for phrase in (
            "next action",
            "next step",
            "immediate next",
            "continue by",
            "then ",
            "다음 행동",
            "다음 작업",
            "바로",
        )
    )
    if (
        has_read_action
        and names_route_docs
        and before_work
        and applied_to_work
        and names_next_action
        and not _is_generic_route_docs_evidence(text)
    ):
        return []
    return [
        "route docs read evidence must state that the required skill/guidance docs "
        "were read before code, implementation, or editing, name the applied "
        "rule, criterion, or takeaway used for this task, and name the immediate "
        "next action that applies those docs to the work"
    ]


def _is_generic_route_docs_takeaway(value: str) -> bool:
    text = value.strip().lower()
    if len(text) < 16:
        return True
    generic_hit = any(phrase in text for phrase in GENERIC_ROUTE_DOCS_TAKEAWAY_PHRASES)
    specific_hit = any(marker in text for marker in SPECIFIC_ROUTE_DOCS_TAKEAWAY_MARKERS)
    return generic_hit and not specific_hit


def _has_actionable_next_action(value: str) -> bool:
    text = value.strip().lower()
    tokens = re.findall(r"[a-z0-9]+|[가-힣]+", text)
    if len(tokens) < 2 or len(set(tokens)) < 2:
        return False
    if any(negation in text for negation in NEXT_ACTION_NEGATIONS):
        return False
    english_action = any(
        re.search(rf"(?<![a-z0-9_]){re.escape(marker)}(?![a-z0-9_])", text)
        for marker in NEXT_ACTION_WORD_MARKERS
    )
    phrase_action = any(marker in text for marker in NEXT_ACTION_PHRASE_MARKERS)
    korean_action = any(marker in text for marker in NEXT_ACTION_KOREAN_STEMS)
    return english_action or phrase_action or korean_action


def _is_generic_route_docs_evidence(text: str) -> bool:
    generic_hit = any(phrase in text for phrase in GENERIC_ROUTE_DOCS_TAKEAWAY_PHRASES)
    specific_hit = any(
        marker in text
        for marker in (
            "alignment",
            "ambiguity",
            "boundary",
            "cycle",
            "documentation",
            "gate evidence",
            "policy",
            "criterion",
            "criteria",
            "review",
            "source docs",
            "test",
            "vibeguard",
            "workflow",
            "적용",
            "반영",
            "기준",
        )
    )
    return generic_hit and not specific_hit


def validate_ambiguity(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    resolved = (
        "no blocker" in text
        or "no blocking" in text
        or "blockers resolved" in text
        or "asked" in text
        or "clarified" in text
        or "assumption" in text
        or "not ambiguous" in text
    )
    if resolved:
        return []
    return [
        "ambiguity check evidence must state no blockers, blockers resolved, "
        "questions asked, clarified decisions, or explicit safe assumptions"
    ]


def validate_alignment_brief(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_shared = any(
        phrase in text
        for phrase in (
            "same understanding",
            "shared understanding",
            "aligned",
            "explicit goal",
            "confirmed fact",
            "같은 이해",
            "같이 이해",
            "명시된 목표",
            "확인된 사실",
        )
    )
    has_difference = any(
        phrase in text
        for phrase in (
            "may differ",
            "different understanding",
            "could differ",
            "possible difference",
            "possible differences",
            "possible mismatch",
            "uncertain scope",
            "다를 수",
            "다른 이해",
            "불확실한 범위",
        )
    )
    has_assumption = any(
        phrase in text
        for phrase in (
            "assumption",
            "unknown",
            "unsupported",
            "no evidence",
            "default",
            "blocker question",
            "minimal question",
            "가정",
            "근거 없음",
            "미확인",
            "질문",
        )
    )
    has_user_visible_checkpoint = any(
        phrase in text
        for phrase in (
            "user-visible",
            "told the user",
            "told user",
            "presented to the user",
            "presented to user",
            "reported to the user",
            "reported to user",
            "asked the user",
            "asked user",
            "choice question",
            "choices presented",
            "presented choices",
            "confirmed with user",
            "shared with user",
            "sent to user",
            "before edits",
            "before editing",
            "사용자에게",
            "유저에게",
            "전달",
            "물어",
            "확인받",
            "수정 전",
            "작업 전",
        )
    )
    if has_shared and has_difference and has_assumption and has_user_visible_checkpoint:
        return []
    return [
        "alignment brief evidence must state shared understanding, possible differences, "
        "unsupported assumptions/unknowns or minimal blocker questions, and the user-visible "
        "checkpoint before requirements analysis or modification work"
    ]
