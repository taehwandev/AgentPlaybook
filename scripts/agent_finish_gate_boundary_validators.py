"""Boundary, side-effect, and run-state finish gate validators."""

from __future__ import annotations


def validate_boundary_plan(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_boundary = any(
        phrase in text
        for phrase in (
            "boundary",
            "owner",
            "owned",
            "scope",
            "same file",
            "single-file",
            "existing",
            "contract",
            "allowed import",
            "forbidden import",
            "no new package",
        )
    )
    has_verification = any(
        phrase in text
        for phrase in (
            "verification",
            "verify",
            "test",
            "check",
            "manual",
            "pytest",
            "unittest",
            "typecheck",
            "smoke",
            "validate",
        )
    )
    if has_boundary and has_verification:
        return []
    return [
        "boundary plan evidence must name the owned boundary/scope or contract, "
        "plus the nearest verification/check before implementation"
    ]


def validate_side_effect_audit(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_audit = any(
        phrase in text
        for phrase in (
            "side-effect",
            "side effect",
            "diff",
            "audit",
            "reviewed",
            "checked",
        )
    )
    has_scope = any(
        phrase in text
        for phrase in (
            "no unexpected",
            "none",
            "unrelated",
            "generated",
            "lockfile",
            "docs",
            "public api",
            "contract",
            "auth",
            "data",
            "release",
            "external",
            "risk",
        )
    )
    if has_audit and has_scope:
        return []
    return [
        "side-effect audit evidence must state that the final diff/side effects were checked "
        "and name unexpected changes, public-contract risk, generated/lockfile churn, or that none were found"
    ]


def validate_agentic_run_state(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_state = any(
        phrase in text
        for phrase in (
            "run state",
            "state:",
            "state=",
            "intake",
            "oriented",
            "scoped",
            "acting",
            "verifying",
            "reviewing",
            "done",
            "blocked",
            "retrospective",
            "상태",
        )
    )
    has_transition = any(
        phrase in text
        for phrase in (
            "transition",
            "next",
            "entered",
            "moved",
            "from",
            "to",
            "resume",
            "restart",
            "다음",
            "전환",
            "재시작",
            "이어",
        )
    )
    has_evidence = any(
        phrase in text
        for phrase in (
            "evidence",
            "gate",
            "command",
            "check",
            "test",
            "hook",
            "diff",
            "verification",
            "증거",
            "게이트",
            "검증",
        )
    )
    if has_state and has_transition and has_evidence:
        return []
    return [
        "agentic run state evidence must state the current run state, "
        "the next transition or resume point, and the gate/command/check evidence"
    ]
