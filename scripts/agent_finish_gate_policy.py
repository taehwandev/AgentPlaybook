"""Evidence validation rules for finish-check route gates."""

from __future__ import annotations


AMBIGUITY_GATE = "ambiguity check"
ALIGNMENT_BRIEF_GATE = "alignment brief"
DOCUMENTATION_GATE = "documentation"
TEST_GATE = "tests"
BOUNDARY_PLAN_GATE = "boundary plan"
MULTI_AGENT_GATE = "multi-agent split decision"
SIDE_EFFECT_AUDIT_GATE = "side-effect audit"


def validate_gate_evidence(gate_evidence: dict[str, str], required_gates: list[str]) -> list[str]:
    failures: list[str] = []
    required = set(required_gates)
    if AMBIGUITY_GATE in required:
        failures.extend(_validate_ambiguity(gate_evidence.get(AMBIGUITY_GATE, "")))
    if ALIGNMENT_BRIEF_GATE in required:
        failures.extend(_validate_alignment_brief(gate_evidence.get(ALIGNMENT_BRIEF_GATE, "")))
    if DOCUMENTATION_GATE in required:
        failures.extend(_validate_documentation(gate_evidence.get(DOCUMENTATION_GATE, "")))
    if TEST_GATE in required:
        failures.extend(_validate_tests(gate_evidence.get(TEST_GATE, "")))
    if BOUNDARY_PLAN_GATE in required:
        failures.extend(_validate_boundary_plan(gate_evidence.get(BOUNDARY_PLAN_GATE, "")))
    if MULTI_AGENT_GATE in required:
        failures.extend(_validate_multi_agent(gate_evidence.get(MULTI_AGENT_GATE, "")))
    if SIDE_EFFECT_AUDIT_GATE in required:
        failures.extend(_validate_side_effect_audit(gate_evidence.get(SIDE_EFFECT_AUDIT_GATE, "")))
    return failures


def _validate_ambiguity(evidence: str) -> list[str]:
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


def _validate_alignment_brief(evidence: str) -> list[str]:
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
    if has_shared and has_difference and has_assumption:
        return []
    return [
        "alignment brief evidence must state shared understanding, possible differences, "
        "and unsupported assumptions/unknowns or minimal blocker questions before requirements "
        "analysis or modification work"
    ]


def _validate_documentation(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    documented = any(
        phrase in text
        for phrase in (
            "updated",
            "created",
            "added",
            "not applicable",
            "unchanged",
            "no docs",
            "docs freshness",
            "source of truth",
        )
    )
    if documented:
        return []
    return [
        "documentation evidence must state docs updated, docs created, source-of-truth checked, "
        "or why docs are not applicable/unchanged"
    ]


def _validate_tests(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_test_signal = any(
        phrase in text
        for phrase in (
            "test",
            "pytest",
            "unittest",
            "unit",
            "integration",
            "regression",
            "smoke",
            "verification",
            "manual",
            "not applicable",
        )
    )
    skipped = any(phrase in text for phrase in ("skipped", "not run", "unable", "cannot run"))
    explained_skip = any(phrase in text for phrase in ("because", "reason", "not applicable", "docs-only", "no useful test"))
    if has_test_signal and (not skipped or explained_skip):
        return []
    return [
        "tests evidence must name the test/check run or explain skipped/not-applicable tests with a reason"
    ]


def _validate_boundary_plan(evidence: str) -> list[str]:
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


def _validate_multi_agent(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_decision = any(
        phrase in text
        for phrase in (
            "multi-agent",
            "subagent",
            "sub-agent",
            "parallel",
            "split",
            "serial",
            "single-agent",
            "not applicable",
        )
    )
    has_scope_reason = any(
        phrase in text
        for phrase in (
            "owned",
            "scope",
            "disjoint",
            "small",
            "single-file",
            "same file",
            "contract",
            "not applicable",
        )
    )
    if has_decision and has_scope_reason:
        return []
    return [
        "multi-agent split decision evidence must state parallel/split or serial/single-agent, "
        "with owned scopes or the reason parallel work is not applicable"
    ]


def _validate_side_effect_audit(evidence: str) -> list[str]:
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
