"""Natural-language query facets for AgentPlaybook document search."""

from __future__ import annotations

import re
from typing import Iterable, Sequence


FACET_BOOST = 30

QUERY_FACETS: tuple[dict[str, object], ...] = (
    {
        "name": "code_cleanup",
        "patterns": (
            r"\b(refactor|cleanup|clean up|clean-up|simplify)\b",
            r"\bcode\b.*\b(clean|cleanup|simplify)\b",
            r"코드.*정리", r"리팩터", r"단순화",
        ),
        "terms": ("refactor", "cleanup", "simplification", "behavior-preserving", "ownership", "equivalence", "verification", "testing"),
        "docs": ("workflows/refactor-cleanup.md", "common/refactoring.md", "common/code-structure-ownership.md", "common/testing.md", "common/verification-policy.md"),
    },
    {
        "name": "change_review",
        "patterns": (
            r"\b(review|inspect|check|verify)\b.*\b(diff|changes?|patch|working tree|worktree|work)\b",
            r"\b(diff|changes?|patch|working tree|worktree)\b.*\b(review|inspect|check|verify)\b",
            r"변경사항.*(검토|확인|체크)", r"작업.*(검토|확인|체크)",
        ),
        "terms": ("review", "diff", "risk", "verification", "worktree", "commit readiness"),
        "docs": ("workflows/review-and-commit.md", "workflows/multi-perspective-review.md", "common/code-review.md", "common/worktree-hygiene.md", "common/verification-policy.md"),
    },
    {
        "name": "verification",
        "patterns": (r"\b(run|execute)\s+(tests?|checks?)\b", r"\bverify\b.*\b(tests?|checks?)\b", r"\bverification\b", r"테스트.*(실행|검증|확인)", r"검증"),
        "terms": ("testing", "scenario", "verification", "evidence", "definition of done"),
        "docs": ("common/testing.md", "common/scenario-driven-testing.md", "common/verification-policy.md", "common/definition-of-done.md"),
    },
    {
        "name": "android_compose_ui",
        "patterns": (
            r"\bandroid\b.*\b(screen|screens|ui|layout|list|lists|favorite|favorites|navigation|tab|compose)\b",
            r"\bcompose\b.*\b(screen|screens|ui|layout|list|lists|favorite|favorites)\b",
            r"(안드로이드|android).*(화면|목록|리스트|즐겨찾기|탭|네비|내비|컴포즈)",
            r"(compose|컴포즈).*(screen|ui|화면|작성|구성|구현)",
        ),
        "terms": ("android", "compose", "screen", "state", "viewmodel", "ui", "preview", "performance"),
        "docs": (
            "platforms/android/android-compose-ui.md", "platforms/android/android-module-structure.md",
            "platforms/android/android-viewmodel-state.md", "platforms/android/android-state-data.md",
            "platforms/android/android-review.md", "platforms/android/android-external-skill-source-coverage.md",
            "platforms/android/skills/source-coverage/references/compose-performance-source-map.md",
        ),
    },
    {
        "name": "ui_feature",
        "patterns": (
            r"\b(screen|screens|ui|layout|list|lists|favorite|favorites|navigation|tab|page|component)\b.*\b(build|create|implement|design|add|make)\b",
            r"\b(build|create|implement|design|add|make)\b.*\b(screen|screens|ui|layout|list|lists|favorite|favorites|navigation|tab|page|component)\b",
            r"(화면|목록|리스트|즐겨찾기|탭|네비|내비).*(구성|구현|만들|작성|추가|짜줘)",
            r"(첫|1|one).*화면.*(두|2|two).*화면",
        ),
        "terms": ("ui", "screen", "state", "structure", "review", "visual verification", "performance"),
        "docs": ("common/ui-visual-verification.md", "common/performance-verification.md", "platforms/web/web-react-ui.md", "platforms/web/web-state-data.md", "platforms/flutter/flutter-widget-ui.md", "platforms/ios/ios-swiftui-ui.md", "platforms/kmp/kmp-compose-ui.md", "platforms/application/application-command-ui.md"),
    },
    {
        "name": "skill_docs",
        "patterns": (r"\b(skill cards?|skill docs?|skill anatomy|agent skills?)\b", r"스킬\s*문서", r"스킬\s*카드"),
        "terms": ("skill", "card", "anatomy", "progressive disclosure", "source"),
        "docs": ("common/agent-skill-card-anatomy.md", "workflows/documentation-update.md", "common/source-driven-development.md"),
    },
    {
        "name": "natural_language_doc_routing",
        "patterns": (
            r"\b(natural language|semantic|document routing|doc routing|doc-route|route docs|docs-read|hook|hooks?)\b",
            r"\b(search|retrieval)\b.*\b(docs?|documents?|skills?)\b",
            r"(자연어|의미).*(검색|문서|라우팅)",
            r"(문서|스킬).*(검색|라우팅|불러|읽)",
            r"(훅|hook).*(문서|검색|읽)",
        ),
        "terms": ("workflow", "routing", "required docs", "reference docs", "docs-read", "source-driven", "task intake", "skill card"),
        "docs": ("workflows/scripted-agent-workflow.md", "workflows/agent-task-lifecycle.md", "common/task-intake-effort-routing.md", "common/source-driven-development.md", "common/agent-skill-card-anatomy.md", "common/tool-failure-recovery.md"),
    },
)


def query_terms(query: str) -> tuple[list[str], list[str], list[str], dict[str, int]]:
    normalized = " ".join(query.strip().split())
    raw_terms = tokenize(normalized)
    expanded_terms: list[str] = []
    matched_facets: list[str] = []
    doc_boosts: dict[str, int] = {}

    for facet in QUERY_FACETS:
        patterns = tuple(str(pattern) for pattern in facet.get("patterns", ()))
        if not any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            continue
        name = str(facet["name"])
        matched_facets.append(name)
        expanded_terms.extend(tokenize(" ".join(str(term) for term in facet.get("terms", ()))))
        for doc in facet_docs(name):
            doc_boosts[doc] = doc_boosts.get(doc, 0) + FACET_BOOST

    return raw_terms, dedupe(expanded_terms), matched_facets, doc_boosts


def facet_docs(name: str) -> set[str]:
    for facet in QUERY_FACETS:
        if facet.get("name") == name:
            return {str(doc) for doc in facet.get("docs", ())}
    return set()


def tokenize(text: str) -> list[str]:
    return dedupe(t.lower() for t in re.split(r"[\s,/|()]+", text.strip()) if t)


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
