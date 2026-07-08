"""Documentation and test finish gate validators."""

from __future__ import annotations

from agent_finish_gate_validators import (
    NO_DOC_DECISIONS,
    UNCHANGED_COVERAGE_PHRASES,
    UNCHANGED_DECISIONS,
    _has_durable_doc_change_signal,
    has_any,
)


def validate_documentation(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_decision = any(
        phrase in text
        for phrase in (
            "updated",
            "created",
            "added",
            "not applicable",
            "unchanged",
            "no doc update",
            "no docs update",
            "docs unchanged",
            "source-of-truth updated",
            "source of truth updated",
        )
    )
    names_target = any(
        phrase in text
        for phrase in (
            ".md",
            "readme",
            "agents",
            "prd",
            "spec",
            "ard",
            "runbook",
            "wiki",
            "source-of-truth",
            "source of truth",
            "docs/",
            "workflows/",
            "common/",
            "platforms/",
            "product-patterns/",
        )
    )
    explains_reason = any(
        phrase in text
        for phrase in (
            "because",
            "reason",
            "why",
            "due to",
            "changed",
            "no durable",
            "no user-visible",
            "workflow policy",
            "public contract",
            "acceptance criteria",
            "behavior",
            "architecture",
            "operator action",
            "왜",
            "이유",
            "변경",
            "문서 영향",
        )
    )
    if has_any(text, NO_DOC_DECISIONS) and _has_durable_doc_change_signal(text):
        return [
            "documentation evidence cannot use not-applicable/no-docs when it "
            "also names a durable planning, requirements, acceptance, workflow "
            "policy, public contract, operator, architecture, API, release, or "
            "test-plan change"
        ]
    if has_any(text, UNCHANGED_DECISIONS) and not has_any(text, UNCHANGED_COVERAGE_PHRASES):
        return [
            "documentation evidence can use unchanged only when it names the "
            "existing doc path/class inspected and why that doc already covers "
            "the planning, behavior, contract, or acceptance change"
        ]
    if has_decision and names_target and explains_reason:
        return []
    return [
        "documentation evidence must name the documentation decision "
        "(updated/created/unchanged/not applicable), the affected source-of-truth "
        "doc path or doc class, and why that decision matches the behavior, "
        "workflow policy, public contract, or durable acceptance criteria changed"
    ]


def validate_tests(evidence: str) -> list[str]:
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
