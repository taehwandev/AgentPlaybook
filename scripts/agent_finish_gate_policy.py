"""Evidence validation rules for finish-check route gates."""

from __future__ import annotations

from agent_finish_gate_validators import (
    validate_documentation_impact_evidence,
    validate_documentation_source_to_artifact_evidence,
    validate_platform_selection_evidence,
    validate_prd_draft_evidence,
    validate_review_readiness_evidence,
    validate_source_docs_evidence,
)


AMBIGUITY_GATE = "ambiguity check"
ROUTE_DOCS_READ_GATE = "route docs read"
ALIGNMENT_BRIEF_GATE = "alignment brief"
DOCUMENTATION_IMPACT_GATE = "documentation impact"
DOCUMENTATION_GATE = "documentation"
TEST_GATE = "tests"
BOUNDARY_PLAN_GATE = "boundary plan"
MULTI_AGENT_GATE = "multi-agent split decision"
SIDE_EFFECT_AUDIT_GATE = "side-effect audit"
AGENTIC_RUN_STATE_GATE = "agentic run state"
SOURCE_DOCS_GATE = "source docs"
PLATFORM_SELECTION_GATE = "platform selection"
REVIEW_READINESS_GATE = "review readiness"
PRD_DRAFT_GATE = "PRD draft"
MULTI_AGENT_ROLES_GATE = "roles"
MULTI_AGENT_WRITE_SCOPES_GATE = "write scopes"
MULTI_AGENT_BRIEFS_GATE = "agent briefs"
MULTI_AGENT_INTEGRATION_REVIEW_GATE = "integration review"
WORKSPACE_SCOPE_CHECKPOINT_GATES = (
    "workspace scope checkpoint",
    "scope expansion checkpoint",
    "cross-repo scope checkpoint",
)
VALIDATED_GATES = {
    ROUTE_DOCS_READ_GATE,
    AMBIGUITY_GATE,
    ALIGNMENT_BRIEF_GATE,
    DOCUMENTATION_IMPACT_GATE,
    DOCUMENTATION_GATE,
    TEST_GATE,
    BOUNDARY_PLAN_GATE,
    MULTI_AGENT_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    AGENTIC_RUN_STATE_GATE,
    SOURCE_DOCS_GATE,
    PLATFORM_SELECTION_GATE,
    REVIEW_READINESS_GATE,
    PRD_DRAFT_GATE,
    MULTI_AGENT_ROLES_GATE,
    MULTI_AGENT_WRITE_SCOPES_GATE,
    MULTI_AGENT_BRIEFS_GATE,
    MULTI_AGENT_INTEGRATION_REVIEW_GATE,
    *WORKSPACE_SCOPE_CHECKPOINT_GATES,
}


def validate_gate_evidence(gate_evidence: dict[str, str], required_gates: list[str]) -> list[str]:
    failures: list[str] = []
    required = set(required_gates)
    if ROUTE_DOCS_READ_GATE in required:
        failures.extend(_validate_route_docs_read(gate_evidence.get(ROUTE_DOCS_READ_GATE, "")))
    if AMBIGUITY_GATE in required:
        failures.extend(_validate_ambiguity(gate_evidence.get(AMBIGUITY_GATE, "")))
    if ALIGNMENT_BRIEF_GATE in required:
        failures.extend(_validate_alignment_brief(gate_evidence.get(ALIGNMENT_BRIEF_GATE, "")))
    if DOCUMENTATION_IMPACT_GATE in required:
        failures.extend(
            validate_documentation_impact_evidence(
                gate_evidence.get(DOCUMENTATION_IMPACT_GATE, "")
            )
        )
    if DOCUMENTATION_GATE in required:
        failures.extend(_validate_documentation(gate_evidence.get(DOCUMENTATION_GATE, "")))
    if SOURCE_DOCS_GATE in required:
        failures.extend(validate_source_docs_evidence(gate_evidence.get(SOURCE_DOCS_GATE, "")))
    if SOURCE_DOCS_GATE in required and DOCUMENTATION_IMPACT_GATE in required:
        failures.extend(
            validate_documentation_source_to_artifact_evidence(
                gate_evidence.get(SOURCE_DOCS_GATE, ""),
                gate_evidence.get(DOCUMENTATION_IMPACT_GATE, ""),
            )
        )
    if PRD_DRAFT_GATE in required:
        failures.extend(validate_prd_draft_evidence(gate_evidence.get(PRD_DRAFT_GATE, "")))
    if PLATFORM_SELECTION_GATE in required:
        failures.extend(validate_platform_selection_evidence(gate_evidence.get(PLATFORM_SELECTION_GATE, "")))
    if REVIEW_READINESS_GATE in required:
        failures.extend(validate_review_readiness_evidence(gate_evidence.get(REVIEW_READINESS_GATE, "")))
    if TEST_GATE in required:
        failures.extend(_validate_tests(gate_evidence.get(TEST_GATE, "")))
    if BOUNDARY_PLAN_GATE in required:
        failures.extend(_validate_boundary_plan(gate_evidence.get(BOUNDARY_PLAN_GATE, "")))
    if MULTI_AGENT_GATE in required:
        failures.extend(_validate_multi_agent(gate_evidence.get(MULTI_AGENT_GATE, "")))
    if SIDE_EFFECT_AUDIT_GATE in required:
        failures.extend(_validate_side_effect_audit(gate_evidence.get(SIDE_EFFECT_AUDIT_GATE, "")))
    if AGENTIC_RUN_STATE_GATE in required:
        failures.extend(_validate_agentic_run_state(gate_evidence.get(AGENTIC_RUN_STATE_GATE, "")))
    if MULTI_AGENT_ROLES_GATE in required:
        failures.extend(_validate_multi_agent_roles(gate_evidence.get(MULTI_AGENT_ROLES_GATE, "")))
    if MULTI_AGENT_WRITE_SCOPES_GATE in required:
        failures.extend(_validate_multi_agent_write_scopes(gate_evidence.get(MULTI_AGENT_WRITE_SCOPES_GATE, "")))
    if MULTI_AGENT_BRIEFS_GATE in required:
        failures.extend(_validate_multi_agent_briefs(gate_evidence.get(MULTI_AGENT_BRIEFS_GATE, "")))
    if MULTI_AGENT_INTEGRATION_REVIEW_GATE in required:
        failures.extend(
            _validate_multi_agent_integration_review(
                gate_evidence.get(MULTI_AGENT_INTEGRATION_REVIEW_GATE, "")
            )
        )
    for gate in WORKSPACE_SCOPE_CHECKPOINT_GATES:
        if gate in gate_evidence:
            failures.extend(_validate_workspace_scope_checkpoint(gate_evidence[gate]))
    return failures


def _validate_route_docs_read(evidence: str) -> list[str]:
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
        "route docs read evidence must state that the routed skill/guidance docs "
        "were read before code, implementation, or editing, and name the applied "
        "rule, criterion, or takeaway used for this task"
    ]


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


def _validate_documentation(evidence: str) -> list[str]:
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
    if has_decision and names_target and explains_reason:
        return []
    return [
        "documentation evidence must name the documentation decision "
        "(updated/created/unchanged/not applicable), the affected source-of-truth "
        "doc path or doc class, and why that decision matches the behavior, "
        "workflow policy, public contract, or durable acceptance criteria changed"
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
    serial = any(
        phrase in text
        for phrase in (
            "serial",
            "single-agent",
            "single agent",
            "not applicable",
            "no subagent",
            "no sub-agent",
            "no parallel",
        )
    )
    parallel = any(
        phrase in text
        for phrase in (
            "multi-agent",
            "subagent",
            "sub-agent",
            "parallel",
            "split",
            "worker",
        )
    )
    has_serial_reason = any(
        phrase in text
        for phrase in (
            "small",
            "single-file",
            "same file",
            "contract",
            "unstable",
            "overlap",
            "dirty worktree",
            "migration",
            "dependency",
            "release",
            "not applicable",
            "not safe",
        )
    )
    if serial and has_serial_reason:
        return []
    has_owned = "owned" in text or "owner" in text or "scope" in text
    has_forbidden = "forbidden" in text or "do not touch" in text or "excluded" in text
    has_contract = "contract" in text or "brief" in text or "input" in text or "output" in text
    has_verification = any(
        phrase in text
        for phrase in (
            "verification",
            "verify",
            "test",
            "check",
            "manual",
            "smoke",
        )
    )
    if parallel and has_owned and has_forbidden and has_contract and has_verification:
        return []
    return [
        "multi-agent split decision evidence must state either serial/single-agent with a concrete "
        "reason, or parallel/subagent work with owned scope, forbidden scope, contract/brief, and "
        "verification"
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


def _validate_agentic_run_state(evidence: str) -> list[str]:
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


def _validate_multi_agent_roles(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_lead = "lead" in text or "owner" in text
    has_worker_or_verifier = any(phrase in text for phrase in ("worker", "builder", "verifier", "reviewer"))
    if has_lead and has_worker_or_verifier:
        return []
    return ["roles evidence must name the lead/owner role and worker/builder/verifier roles"]


def _validate_multi_agent_write_scopes(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_owned = any(phrase in text for phrase in ("owned", "owner", "write scope", "writes:", "scope:"))
    has_forbidden = any(
        phrase in text for phrase in ("forbidden", "do not touch", "excluded", "read-only", "readonly")
    )
    if has_owned and has_forbidden:
        return []
    return ["write scopes evidence must name owned write scope and forbidden/read-only scope"]


def _validate_multi_agent_briefs(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    checks = {
        "worker": any(phrase in text for phrase in ("worker", "agent", "task id")),
        "role": "role" in text,
        "owned": any(phrase in text for phrase in ("owned", "scope")),
        "forbidden": any(phrase in text for phrase in ("forbidden", "do not touch", "excluded")),
        "contract": any(phrase in text for phrase in ("contract", "input", "expected output", "output")),
        "acceptance": "acceptance" in text,
        "verification": any(phrase in text for phrase in ("verification", "verify", "test", "check", "smoke")),
    }
    if all(checks.values()):
        return []
    missing = ", ".join(name for name, present in checks.items() if not present)
    return [f"agent briefs evidence must include worker id, role, owned scope, forbidden scope, contract/output, acceptance checks, and verification; missing: {missing}"]


def _validate_multi_agent_integration_review(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_integration = any(phrase in text for phrase in ("integration", "merged", "merge", "combined"))
    has_contract = any(phrase in text for phrase in ("contract", "drift", "schema", "route", "state model", "config"))
    has_final_check = any(
        phrase in text for phrase in ("verification", "verify", "test", "check", "smoke", "final")
    )
    if has_integration and has_contract and has_final_check:
        return []
    return ["integration review evidence must name integration/merge review, contract-drift check, and final verification"]


def _validate_workspace_scope_checkpoint(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_primary = any(
        phrase in text
        for phrase in (
            "starting primary",
            "primary repo",
            "primary:",
            "primary=",
            "시작 primary",
            "기준 repo",
        )
    )
    has_secondary = any(
        phrase in text
        for phrase in (
            "secondary repo",
            "secondary:",
            "secondary=",
            "source of truth",
            "new source",
            "추가 repo",
            "소스 오브 트루스",
        )
    )
    has_mode = any(
        phrase in text
        for phrase in (
            "single-repo",
            "single_repo",
            "primary-led",
            "primary_led",
            "secondary read",
            "secondary write",
            "multi-session",
            "multi_session",
            "mode:",
            "mode=",
            "모드",
        )
    )
    has_verification = any(
        phrase in text
        for phrase in (
            "verification",
            "verify",
            "test",
            "smoke",
            "check",
            "검증",
            "테스트",
        )
    )
    if has_primary and has_secondary and has_mode and has_verification:
        return []
    return [
        "workspace scope checkpoint evidence must state the starting primary repo, "
        "secondary/source-of-truth repo, chosen mode, and cross-repo verification before "
        "writing to a secondary repo"
    ]
