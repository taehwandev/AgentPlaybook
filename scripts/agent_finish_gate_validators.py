"""Focused validators for route gates with larger evidence contracts."""

from __future__ import annotations


def has_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


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
        "source docs evidence must state that PRD/spec/ARD/source-of-truth docs "
        "were searched and opened/read before implementation or edits, or that "
        "none were found, and must explain how that source affected the work or "
        "documentation decision"
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
    names_docs = has_any(
        text,
        (
            ".md", "readme", "agents", "prd", "spec", "ard", "docs/",
            "workflows/", "common/", "platforms/", "source-of-truth",
            "source of truth", "doc class", "문서",
        ),
    )
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
    if pre_edit and names_docs and has_decision and has_reason:
        return []
    return [
        "documentation impact evidence must state the pre-code/pre-edit "
        "documentation impact decision, affected doc path or doc class, and "
        "why behavior, workflow policy, public contract, operator action, or "
        "acceptance criteria do or do not require a doc update"
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
