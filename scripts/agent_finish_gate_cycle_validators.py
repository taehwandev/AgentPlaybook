"""Cycle, boundary, and run-state finish gate validators."""

from __future__ import annotations


def validate_cycle_contract(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_cycle_type = any(
        phrase in text
        for phrase in (
            "cycle type",
            "cycle_type",
            "cycle:",
            "cycle=",
            "implementation cycle",
            "review cycle",
            "review-response cycle",
            "review response cycle",
            "release cycle",
            "docs sweep",
            "refactor cycle",
            "workflow setup cycle",
            "사이클",
        )
    )
    has_scope = any(
        phrase in text
        for phrase in (
            "input scope",
            "input_scope",
            "source of truth",
            "source-of-truth",
            "scope:",
            "scope=",
            "acceptance source",
            "스코프",
            "범위",
        )
    )
    has_boundary = any(
        phrase in text
        for phrase in (
            "allowed",
            "forbidden",
            "permission boundary",
            "allowed changes",
            "forbidden changes",
            "do not touch",
            "boundary",
            "허용",
            "금지",
        )
    )
    has_acceptance_or_verification = any(
        phrase in text
        for phrase in (
            "acceptance",
            "success criteria",
            "verification",
            "verify",
            "test",
            "check",
            "scenario",
            "criteria",
            "검증",
            "테스트",
            "수용 기준",
        )
    )
    has_stop_condition = any(
        phrase in text
        for phrase in (
            "stop condition",
            "stop when",
            "exit condition",
            "done when",
            "handoff when",
            "iteration limit",
            "중단 조건",
            "완료 조건",
        )
    )
    has_next_or_checkpoint = any(
        phrase in text
        for phrase in (
            "next cycle",
            "checkpoint",
            "handoff",
            "review separately",
            "separate review",
            "commit checkpoint",
            "next:",
            "다음",
            "체크포인트",
            "인계",
        )
    )
    if (
        has_cycle_type
        and has_scope
        and has_boundary
        and has_acceptance_or_verification
        and has_stop_condition
        and has_next_or_checkpoint
    ):
        return []
    return [
        "cycle contract evidence must name the cycle type, input/source scope, "
        "allowed or forbidden change boundary, acceptance or verification method, "
        "stop condition, and next cycle/checkpoint or handoff"
    ]
