"""Focused validators for route gates with larger evidence contracts."""

from __future__ import annotations

import re


def has_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


DOC_ARTIFACT_PHRASES = (
    "artifact", "doc type", "doc class", "prd", "product requirements",
    "spec", "feature spec", "functional spec", "ard", "architecture note",
    "architecture doc", "adr", "rfc", "decision record", "module readme", "readme",
    "api contract", "api reference", "schema", "event contract",
    "runbook", "ops guide", "operator guide", "migration note",
    "release note", "changelog", "test plan", "qa plan", "skill card",
    "platform card", "workflow card", "agent instruction", "agents.md",
    "contributing", "wiki", "knowledge-base", "요구사항", "스펙",
    "아키텍처", "런북", "마이그레이션", "릴리즈", "테스트 계획",
)

NO_DURABLE_DOC_REASONS = (
    "answer-only", "purely local", "local-only", "mechanical",
    "no durable behavior", "no durable change", "no user-visible",
    "no workflow policy", "no public contract", "no operator action",
    "no acceptance criteria", "no product behavior", "no architecture",
    "no runtime behavior", "docs-only typo", "format-only",
    "no workflow policy changed", "no public contract changed",
    "no operator action changed", "no acceptance criteria changed",
    "no product behavior changed", "no architecture changed",
    "no release behavior changed", "no test plan changed",
    "답변만", "기계적", "동작 변경 없음", "문서 영향 없음",
)

NON_CREATION_DECISIONS = (
    "unchanged", "not applicable", "no doc", "no docs",
    "변경 없음", "해당 없음",
)

UNCHANGED_DECISIONS = ("unchanged", "변경 없음")

NO_DOC_DECISIONS = ("not applicable", "no doc", "no docs", "해당 없음")

UNCHANGED_COVERAGE_PHRASES = (
    "already covered", "already covers", "already documented",
    "existing doc", "existing docs", "inspected", "current doc",
    "current docs", "up to date", "still current", "no edit needed",
    "covered by", "coverage:", "covered_by=", "covers the",
    "이미", "커버", "반영되어", "반영됨", "현재 문서",
)

# An `unchanged` documentation decision must prove the doc was actually opened
# and read, not merely asserted to already cover the change. These phrases are
# the inspection proof; a bare coverage claim without one of them is a
# self-granted exception and must fail the gate.
DOC_INSPECTION_PROOF_PHRASES = (
    "inspected", "opened", "re-read", "reread", "read the",
    "reviewed", "checked ", "verified", "looked at", "examined",
    "confirmed by reading", "opened and", "re-opened",
    "열어", "열람", "확인", "검토", "재검토", "읽어", "읽고",
)

# The coverage-state claim that pairs with the inspection proof: why the opened
# doc already reflects the change.
DOC_COVERAGE_STATE_PHRASES = (
    "already covered", "already covers", "already documented",
    "existing doc", "existing docs", "current doc", "current docs",
    "up to date", "still current", "no edit needed", "covered by",
    "coverage:", "covered_by=", "covers the",
    "remains accurate", "remain accurate", "still accurate",
    "stays accurate", "stays correct", "still correct",
    "accurate as written", "correct as written",
    "이미", "커버", "반영되어", "반영됨", "현재 문서", "여전히 정확",
)

DURABLE_DOC_CHANGE_PATTERNS = (
    r"\b(planning|plan|requirements?|spec|scope|acceptance criteria)\b.*\b(changed?|updated?|new|added|removed|revised?)\b",
    r"\b(changed?|updated?|new|added|removed|revised?)\b.*\b(planning|plan|requirements?|spec|scope|acceptance criteria)\b",
    r"\b(product behavior|workflow policy|public contract|operator action|architecture|api contract|schema|migration|release|runbook|test plan)\b.*\b(changed?|updated?|new|added|removed|revised?)\b",
    r"\b(changed?|updated?|new|added|removed|revised?)\b.*\b(product behavior|workflow policy|public contract|operator action|architecture|api contract|schema|migration|release|runbook|test plan)\b",
    r"(기획|요구사항|요건|스펙|범위|수용 기준|수락 기준|제품 동작|워크플로우 정책|공개 계약|운영자 조치|아키텍처|api|스키마|마이그레이션|배포|릴리즈|런북|테스트 계획)\s*(변경|수정|갱신|추가|삭제)",
    r"(변경|수정|갱신|추가|삭제).*(기획|요구사항|요건|스펙|범위|수용 기준|수락 기준|제품 동작|워크플로우 정책|공개 계약|운영자 조치|아키텍처|api|스키마|마이그레이션|배포|릴리즈|런북|테스트 계획)",
)


def validate_source_docs_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_discovery = has_any(
        text,
        (
            "searched", "discovered", "found", "opened", "read", "checked",
            "no prd", "no spec", "none found",
            "검색", "발견", "열", "읽", "확인", "없음",
        ),
    )
    names_source = has_any(
        text,
        (
            "prd", "spec", "ard", "requirements", "acceptance criteria",
            "design note", "issue", "source-of-truth", "source of truth",
            "product docs", "task doc", "planning doc",
            "adr", "rfc", "module readme", "api contract", "runbook",
            "migration note", "release note", "test plan", "skill card",
            "platform card", "workflow card", "agent instruction",
            "문서", "요구사항", "스펙", "기획",
        ),
    )
    before_work = has_any(
        text,
        (
            "before code", "before coding", "before implementation",
            "before edit", "before edits", "before work",
            "pre-code", "pre implementation",
            "구현 전", "수정 전", "작업 전",
        ),
    )
    explains_outcome = has_any(
        text,
        (
            "used", "applied", "updated", "created", "unchanged",
            "not applicable", "none found", "no prd", "no spec",
            "user request as source", "source of truth", "source-of-truth",
            "반영", "적용", "갱신", "없음", "기준",
        ),
    )
    if has_discovery and names_source and before_work and explains_outcome:
        return []
    return [
        "source docs evidence must state that relevant source-of-truth docs "
        "were searched and opened/read before implementation or edits, or that "
        "none were found. Source docs can be PRD/spec/ARD, issue/design note, "
        "ADR/RFC, module README, API contract, runbook, migration note, release "
        "note, test plan, skill/platform/workflow card, or agent instruction. "
        "Evidence must explain how that source affected the work or "
        "documentation artifact decision"
    ]


def validate_documentation_impact_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    pre_edit = has_any(
        text,
        (
            "before code", "before implementation", "before edit",
            "before edits", "pre-code", "pre-edit", "구현 전", "수정 전",
        ),
    )
    selects_artifact = has_any(text, DOC_ARTIFACT_PHRASES)
    has_decision = has_any(
        text,
        (
            "impact", "affected", "documentation decision", "update",
            "create", "unchanged", "not applicable", "no doc", "no docs",
            "갱신", "생성", "영향", "변경 없음", "해당 없음",
        ),
    )
    has_reason = has_any(
        text,
        (
            "because", "reason", "why", "changed", "behavior",
            "workflow policy", "public contract", "acceptance criteria",
            "operator action", "이유", "왜", "변경",
        ),
    )
    no_doc_decision = has_any(text, NO_DOC_DECISIONS)
    unchanged_decision = has_any(text, UNCHANGED_DECISIONS)
    if no_doc_decision and _has_durable_doc_change_signal(text):
        return [
            "documentation impact evidence cannot use not-applicable/no-docs "
            "when it also names a durable planning, requirements, acceptance, "
            "workflow policy, public contract, operator, architecture, API, "
            "release, or test-plan change"
        ]
    if unchanged_decision and not _unchanged_evidence_is_grounded(text):
        return [
            "documentation impact evidence can use unchanged only when it names "
            "the existing doc path it opened/inspected and states why that "
            "already-read doc covers the planning, behavior, contract, or "
            "acceptance change; a bare coverage claim is not enough"
        ]
    if no_doc_decision and not has_any(text, NO_DURABLE_DOC_REASONS):
        return [
            "documentation impact evidence cannot use not-applicable/no-docs "
            "without a no-durable-doc reason such as answer-only, purely local, "
            "mechanical, no durable behavior, no public contract, no operator "
            "action, or no acceptance criteria"
        ]
    if pre_edit and selects_artifact and has_decision and has_reason:
        return []
    return [
        "documentation impact evidence must state the pre-code/pre-edit "
        "documentation artifact selection, the impact decision, and why "
        "behavior, workflow policy, public contract, operator action, or "
        "acceptance criteria do or do not require creating/updating that artifact"
    ]


def validate_documentation_source_to_artifact_evidence(
    source_evidence: str,
    impact_evidence: str,
) -> list[str]:
    source_text = source_evidence.lower()
    impact_text = impact_evidence.lower()
    if not source_text or not impact_text:
        return []
    no_source_found = has_any(
        source_text,
        (
            "none found", "no source", "no source docs",
            "no source-of-truth", "source not found", "not found", "없음",
        ),
    )
    non_creation = has_any(impact_text, NON_CREATION_DECISIONS)
    if no_source_found and non_creation and not has_any(impact_text, NO_DURABLE_DOC_REASONS):
        return [
            "when source docs are missing, documentation impact cannot choose "
            "unchanged/not-applicable/no-docs unless it states why the work has "
            "no durable documentation artifact. New durable behavior should "
            "create the smallest useful PRD/spec, ADR/RFC, module README, API "
            "contract, runbook, migration note, release note, test plan, skill "
            "card, platform card, workflow card, or agent instruction update"
        ]
    return []


def _has_existing_doc_coverage(text: str) -> bool:
    return has_any(text, UNCHANGED_COVERAGE_PHRASES)


def _names_doc_path(text: str) -> bool:
    """True when the evidence points at a concrete doc file, not just a class."""
    return ".md" in text or "docs/" in text or "/" in text


def _unchanged_evidence_is_grounded(text: str) -> bool:
    """An `unchanged` doc decision is grounded only when it names the doc path,
    proves the doc was opened/inspected, and states why it already covers the
    change. All three are required so the agent cannot self-except by asserting
    coverage without checking."""
    return (
        _names_doc_path(text)
        and has_any(text, DOC_INSPECTION_PROOF_PHRASES)
        and has_any(text, DOC_COVERAGE_STATE_PHRASES)
    )


def _has_durable_doc_change_signal(text: str) -> bool:
    searchable = text
    for phrase in NO_DURABLE_DOC_REASONS:
        searchable = searchable.replace(phrase, "")
    return any(re.search(pattern, searchable) for pattern in DURABLE_DOC_CHANGE_PATTERNS)


PRD_CONTENT_PHRASES = (
    "acceptance criteria", "given", "when", "then",
    "in scope", "out of scope", "actor", "outcome", "user story",
    "states", "open decisions", "desired outcome", "proposed behavior",
    "요구사항", "수용 기준", "범위", "액터", "결과", "수락 기준",
)


def validate_prd_draft_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    has_created = has_any(
        text,
        (
            "created", "drafted", "written", "saved", "wrote",
            "file", ".md", "doc path", "path:", "artifact", "document",
            "생성", "작성", "저장", "파일",
        ),
    )
    has_prd_content = has_any(text, PRD_CONTENT_PHRASES)
    if has_created and has_prd_content:
        return []
    return [
        "PRD draft evidence must confirm the PRD was created or drafted (name the file "
        "path or artifact) and include content evidence such as acceptance criteria, "
        "scope, actor/outcome, states, or open decisions"
    ]


IMPLEMENTATION_PROPOSAL_PHRASES = (
    "implementation", "implement", "build the", "roadmap", "backlog",
    "milestone", "phase 1", "phase 2", "next feature", "new feature",
    "task list", "epic", "user story", "deliver the", "build out",
    "구현", "로드맵", "백로그", "기능 추가", "마일스톤", "다음 기능",
)

NO_PROPOSAL_PHRASES = (
    "no implementation", "no new product", "no roadmap", "no backlog",
    "status only", "classification only", "recommendation only",
    "no product work", "triage only", "no feature proposed",
    "no implementation proposed", "no new work proposed",
    "구현 없음", "구현 제안 없음", "제안 없음", "현황만", "분류만", "추천만",
)

PRD_COVERAGE_PHRASES = (
    "accepted prd", "prd coverage", "prd link", "linked prd", "prd:",
    "product route", "product re-entry", "product reentry",
    "re-enter product", "reenter product", "coverage matrix",
    "product 재진입", "prd 커버리지", "prd 링크", "수락된 prd",
)


def validate_product_reentry_evidence(evidence: str) -> list[str]:
    """Force a triage/plan to declare product-route coverage before it can hand
    off implementation work. Either it states no new product/implementation work
    was proposed, or, when it proposes a roadmap/backlog/implementation ordering,
    it must name PRD coverage (an Accepted PRD link or an explicit product-route
    re-entry to create/accept the PRD, plus ARD when structure changes). The
    silent path — proposing implementation without PRD coverage — fails."""
    text = evidence.lower()
    if not text:
        return [
            "product route re-entry evidence is required and cannot be empty: "
            "state whether the triage/plan proposed any new product or "
            "implementation work, and if so name the PRD coverage or product-"
            "route re-entry that must precede implementation"
        ]
    disclaims = has_any(text, NO_PROPOSAL_PHRASES)
    # Strip the disclaimer phrases before scanning for proposal keywords so a
    # negated mention ("no implementation proposed") is not read as a proposal.
    searchable = text
    for phrase in NO_PROPOSAL_PHRASES:
        searchable = searchable.replace(phrase, " ")
    proposes = has_any(searchable, IMPLEMENTATION_PROPOSAL_PHRASES)
    if disclaims and not proposes:
        return []
    if proposes and has_any(text, PRD_COVERAGE_PHRASES):
        return []
    return [
        "product route re-entry evidence must either state that the triage/plan "
        "proposed no new product or implementation work, or, when it proposes "
        "implementation ordering/roadmap/backlog, name the PRD coverage (Accepted "
        "PRD link, or explicit product-route re-entry to create and accept the "
        "PRD, plus an ARD link when structure/module boundaries change) that must "
        "precede any implementation task or PR"
    ]


def validate_platform_selection_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    if ("not applicable" in text or "no platform" in text) and has_any(
        text,
        (
            "because", "reason", "not affected", "docs-only",
            "workflow-only", "no ui", "no runtime", "no platform-specific",
        ),
    ):
        return []
    selected = has_any(
        text,
        (
            "selected platform", "platform:", "platforms:",
            "android", "ios", "swift", "web", "server", "application",
            "flutter", "kmp",
        ),
    )
    docs = has_any(
        text,
        (
            "platform card", "platform cards", "platforms/",
            "android-", "ios-", "swift-", "web-", "server-", "application-",
            "read", "loaded",
        ),
    )
    before_architecture = has_any(
        text,
        (
            "before prd", "before ard", "before architecture",
            "before implementation", "before code", "pre-code", "prd/ard",
        ),
    )
    if selected and docs and before_architecture:
        return []
    return [
        "platform selection evidence must name the selected platform(s) and "
        "platform card/docs read before PRD/ARD/architecture work, or state no "
        "platform is applicable with a reason"
    ]


def validate_review_readiness_evidence(evidence: str) -> list[str]:
    text = evidence.lower()
    if not text:
        return []
    if (
        has_any(
            text,
            (
                "review readiness", "readiness", "frontmatter", "status",
                "type", "human-reviewed-needed", "ai-generated", "review queue",
            ),
        )
        and has_any(
            text,
            (
                ".md", "markdown", "docs", "common/", "workflows/",
                "platforms/", "templates/", "product-patterns/",
                "agents.md", "readme", "index.md",
            ),
        )
        and has_any(text, ("count", "counts", "queue", "missing", "malformed", "none", "0", "stable", "review", "risk", "needs", "found"))
    ):
        return []
    return [
        "review readiness evidence must report markdown/frontmatter status/type "
        "readiness or human-review queue results for the reviewed doc scope"
    ]
