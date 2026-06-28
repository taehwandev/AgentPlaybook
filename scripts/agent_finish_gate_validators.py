"""Focused validators for route gates with larger evidence contracts."""

from __future__ import annotations


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
    "답변만", "기계적", "동작 변경 없음", "문서 영향 없음",
)

NON_CREATION_DECISIONS = (
    "unchanged", "not applicable", "no doc", "no docs",
    "변경 없음", "해당 없음",
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
    non_creation = has_any(text, NON_CREATION_DECISIONS)
    if non_creation and not has_any(text, NO_DURABLE_DOC_REASONS):
        return [
            "documentation impact evidence cannot use unchanged/not-applicable/no-docs "
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
