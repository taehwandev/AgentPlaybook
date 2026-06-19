"""Evidence validation rules for finish-check route gates."""

from __future__ import annotations


AMBIGUITY_GATE = "ambiguity check"
DOCUMENTATION_GATE = "documentation"
TEST_GATE = "tests"
MULTI_AGENT_GATE = "multi-agent split decision"


def validate_gate_evidence(gate_evidence: dict[str, str], required_gates: list[str]) -> list[str]:
    failures: list[str] = []
    required = set(required_gates)
    if AMBIGUITY_GATE in required:
        failures.extend(_validate_ambiguity(gate_evidence.get(AMBIGUITY_GATE, "")))
    if DOCUMENTATION_GATE in required:
        failures.extend(_validate_documentation(gate_evidence.get(DOCUMENTATION_GATE, "")))
    if TEST_GATE in required:
        failures.extend(_validate_tests(gate_evidence.get(TEST_GATE, "")))
    if MULTI_AGENT_GATE in required:
        failures.extend(_validate_multi_agent(gate_evidence.get(MULTI_AGENT_GATE, "")))
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


def _validate_multi_agent(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_decision = any(
        phrase in text
        for phrase in (
            "multi-agent",
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
