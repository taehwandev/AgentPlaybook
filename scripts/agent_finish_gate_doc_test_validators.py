"""Documentation and test finish gate validators."""

from __future__ import annotations

from agent_finish_gate_skip_policy import _evidence_records_skip_reason
from agent_finish_gate_validators import (
    NO_DOC_DECISIONS,
    UNCHANGED_DECISIONS,
    _has_durable_doc_change_signal,
    _unchanged_evidence_is_grounded,
    has_any,
)


DOCUMENTATION_EVIDENCE_REQUIRED = (
    "documentation evidence is required and cannot be empty: name the "
    "documentation decision (updated/created/unchanged), the affected "
    "source-of-truth doc path, and why that decision matches the change"
)

# Skipping documentation is never self-approved. When the agent believes docs
# should truly not be written, it must ask the user ("문서를 스킵할까요?" /
# "Should I skip the doc?") and record their explicit approval. A reason alone
# is not enough — these phrases prove the human review happened.
DOC_SKIP_APPROVAL_PHRASES = (
    "user approved", "user confirmed", "user agreed", "user reviewed and approved",
    "approved skipping", "approved the skip", "skip approved by",
    "user said skip", "user asked to skip", "user chose to skip",
    "human approved", "operator approved", "confirmed with the user to skip",
    "user approved skipping",
    "사용자 승인", "사용자가 승인", "사용자 확인", "사용자 검토 후",
    "검토받아", "검토받고", "스킵 승인", "문서 스킵 승인", "물어보고 승인",
    "사용자에게 확인받",
)

DOCUMENTATION_SKIP_NEEDS_APPROVAL = (
    "documentation cannot be skipped (not-applicable/no-docs/skipped) on the "
    "agent's own judgment or a reason alone: ask the user '문서를 스킵할까요?' / "
    "'Should I skip the doc?', get explicit approval, and record that approval "
    "in the evidence — otherwise write the doc"
)


def validate_documentation(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return [DOCUMENTATION_EVIDENCE_REQUIRED]
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
    if _is_documentation_skip_decision(text) and not has_any(text, DOC_SKIP_APPROVAL_PHRASES):
        return [DOCUMENTATION_SKIP_NEEDS_APPROVAL]
    if has_any(text, UNCHANGED_DECISIONS) and not _unchanged_evidence_is_grounded(text):
        return [
            "documentation evidence can use unchanged only when it names the "
            "existing doc path it opened/inspected and states why that "
            "already-read doc covers the planning, behavior, contract, or "
            "acceptance change; a bare coverage claim is not enough"
        ]
    if has_decision and names_target and explains_reason:
        return []
    return [
        "documentation evidence must name the documentation decision "
        "(updated/created/unchanged/not applicable), the affected source-of-truth "
        "doc path or doc class, and why that decision matches the behavior, "
        "workflow policy, public contract, or durable acceptance criteria changed"
    ]


def _is_documentation_skip_decision(text: str) -> bool:
    """True when the documentation evidence declares a skip: an explicit
    not-applicable/no-docs decision or any recorded skip/생략 reason."""
    return has_any(text, NO_DOC_DECISIONS) or _evidence_records_skip_reason(text)


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
