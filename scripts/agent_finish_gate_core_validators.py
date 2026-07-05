"""Core finish gate evidence validators."""

from __future__ import annotations


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
    if has_read_action and names_route_docs and before_work and applied_to_work:
        return []
    return [
        "route docs read evidence must state that the required skill/guidance docs "
        "were read before code, implementation, or editing, and name the applied "
        "rule, criterion, or takeaway used for this task"
    ]


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
