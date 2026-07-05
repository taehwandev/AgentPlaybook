"""Static route and platform catalogs for workflow.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from workflow_concern_docs import BASELINE_CONCERNS, CONCERNS, PUBLIC_DISCOVERY_DOCS
from workflow_concern_hints import REQUEST_CONCERN_HINTS
from workflow_platform_concerns import PLATFORM_CONCERNS


@dataclass(frozen=True)
class Profile:
    docs: Tuple[str, ...]
    gates: Tuple[str, ...]
    notes: Tuple[str, ...] = ()


CORE_DOCS = (
    "AGENTS.md",
    "index.md",
    "common/agent-operating-skill.md",
    "common/stack-discovery.md",
    "common/llm-coding-discipline.md",
    "common/code-conventions.md",
    "common/tool-failure-recovery.md",
    "common/agent-interaction.md",
    "common/agent-editing-safety.md",
)


COMMANDS: Dict[str, Profile] = {
    "triage": Profile(
        docs=(
            "workflows/request-triage.md",
            "common/task-intake-effort-routing.md",
            "workflows/ambiguity-gate.md",
        ),
        gates=("classify request", "select effort", "grill-me if needed", "route recommendation"),
        notes=("Use before loading broad context when request clarity or effort level is uncertain.",),
    ),
    "task": Profile(
        docs=("workflows/agent-task-lifecycle.md",),
        gates=("orient", "scope", "act", "verify", "report"),
        notes=("Use for general multi-step agent work.",),
    ),
    "workflow-setup": Profile(
        docs=("workflows/agent-task-lifecycle.md", "common/tool-failure-recovery.md"),
        gates=("orient", "install or repair", "runtime label handoff", "verify", "handoff"),
        notes=(
            "Use when the task changes local agent prompts, runtime hooks, "
            "workflow label bridges, or metering setup.",
        ),
    ),
    "product": Profile(
        docs=(
            "workflows/scripted-agent-workflow.md",
            "workflows/ambiguity-gate.md",
            "workflows/product-architecture-delivery.md",
            "workflows/multi-perspective-review.md",
            "workflows/development-cycle.md",
            "common/product-spec-to-implementation.md",
            "common/architecture-selection.md",
            "common/architecture-design.md",
        ),
        gates=(
            "platform selection",
            "PRD",
            "ARD",
            "pre-code review",
            "code work",
            "review",
            "tests",
            "UI tests when applicable",
            "commit readiness",
        ),
        notes=("Use when product intent must become architecture and code.",),
    ),
    "prd": Profile(
        docs=(
            "workflows/ambiguity-gate.md",
            "workflows/prd-creation.md",
            "common/product-spec-to-implementation.md",
        ),
        gates=(
            "local product docs",
            "ambiguity check",
            "PRD draft",
            "acceptance criteria",
            "open decisions",
            "handoff",
        ),
        notes=("Use when the deliverable is a PRD or product requirements note before ARD or code.",),
    ),
    "spec": Profile(
        docs=(
            "workflows/ambiguity-gate.md",
            "workflows/prd-creation.md",
            "common/product-spec-to-implementation.md",
        ),
        gates=(
            "local product docs",
            "ambiguity check",
            "PRD draft",
            "acceptance criteria",
            "open decisions",
            "handoff",
        ),
        notes=("Lifecycle alias for PRD/specification work; keep `prd` as the canonical route.",),
    ),
    "plan": Profile(
        docs=("workflows/planning-research.md", "common/doubt-driven-development.md"),
        gates=("question", "sources", "options", "recommendation"),
        notes=("Lifecycle alias for planning and research before implementation.",),
    ),
    "build": Profile(
        docs=(
            "workflows/feature-implementation.md",
            "workflows/product-architecture-delivery.md",
            "workflows/development-cycle.md",
            "common/product-spec-to-implementation.md",
            "common/incremental-implementation.md",
            "common/source-driven-development.md",
            "common/doubt-driven-development.md",
        ),
        gates=("PRD/ARD applicability", "acceptance criteria", "implementation", "verification", "handoff"),
        notes=("Lifecycle alias for a scoped build slice; use `product` for broad product delivery.",),
    ),
    "test": Profile(
        docs=(
            "common/testing.md",
            "common/scenario-driven-testing.md",
            "common/verification-policy.md",
            "common/browser-runtime-testing.md",
        ),
        gates=("test scope", "run checks", "evidence", "handoff"),
        notes=("Lifecycle alias for verification-only work or test evidence collection.",),
    ),
    "webperf": Profile(
        docs=(
            "common/performance-verification.md",
            "common/web-performance-verification.md",
            "common/browser-runtime-testing.md",
            "common/ui-visual-verification.md",
        ),
        gates=("baseline", "measure", "risk review", "recommendation", "handoff"),
        notes=("Lifecycle alias for browser and web performance review.",),
    ),
    "code-simplify": Profile(
        docs=(
            "workflows/refactor-cleanup.md",
            "common/refactoring.md",
            "common/incremental-implementation.md",
            "common/code-structure-ownership.md",
        ),
        gates=("behavior baseline", "simplification plan", "small refactor", "equivalence check", "handoff"),
        notes=("Lifecycle alias for behavior-preserving simplification.",),
    ),
    "ambiguity": Profile(
        docs=("workflows/ambiguity-gate.md", "common/product-spec-to-implementation.md"),
        gates=("classify unknowns", "research repo-answerable items", "ask blockers", "record assumptions"),
        notes=("Use before PRD, ARD, task breakdown, or implementation when unknowns can change behavior or risk.",),
    ),
    "feature": Profile(
        docs=(
            "workflows/feature-implementation.md",
            "workflows/product-architecture-delivery.md",
            "workflows/development-cycle.md",
            "common/product-spec-to-implementation.md",
        ),
        gates=("PRD/ARD applicability", "acceptance criteria", "implementation", "verification", "handoff"),
    ),
    "bugfix": Profile(
        docs=("workflows/bugfix-debugging.md", "workflows/development-cycle.md"),
        gates=("reproduce", "isolate", "fix", "regression check", "handoff"),
    ),
    "refactor": Profile(
        docs=("workflows/refactor-cleanup.md", "common/refactoring.md"),
        gates=("behavior baseline", "small refactor", "equivalence check", "handoff"),
    ),
    "docs": Profile(
        docs=("workflows/documentation-update.md",),
        gates=("source of truth", "edit", "link/path check", "handoff"),
    ),
    "docs-review": Profile(
        docs=(
            "workflows/review-and-commit.md",
            "workflows/documentation-update.md",
            "workflows/multi-perspective-review.md",
            "common/code-review.md",
            "common/llm-wiki-documentation.md",
        ),
        gates=(
            "review readiness",
            "source review",
            "structure review",
            "link/path check",
            "verification",
            "handoff",
        ),
        notes=("Use for reviewing durable docs, wiki pages, playbooks, and runbooks.",),
    ),
    "planning": Profile(
        docs=("workflows/planning-research.md",),
        gates=("question", "sources", "options", "recommendation"),
    ),
    "review": Profile(
        docs=(
            "workflows/review-and-commit.md",
            "workflows/multi-perspective-review.md",
            "common/code-review.md",
        ),
        gates=("diff review", "risk review", "verification", "commit readiness"),
    ),
    "multi-agent": Profile(
        docs=("workflows/multi-agent-collaboration.md", "workflows/agent-handoff-continuation.md"),
        gates=("roles", "write scopes", "agent briefs", "integration review", "handoff"),
        notes=("Use when work is delegated, parallelized, or split into builder/verifier roles.",),
    ),
    "release": Profile(
        docs=(
            "workflows/release-readiness.md",
            "common/release-deployment.md",
            "common/release-versioning.md",
            "common/ci-cd-automation.md",
            "common/deprecation-migration.md",
        ),
        gates=("package", "config", "smoke", "rollback", "handoff"),
    ),
    "ship": Profile(
        docs=(
            "workflows/release-readiness.md",
            "common/release-deployment.md",
            "common/release-versioning.md",
            "common/ci-cd-automation.md",
            "common/deprecation-migration.md",
        ),
        gates=("package", "config", "smoke", "rollback", "handoff"),
        notes=("Lifecycle alias for release and shipping readiness; keep `release` as the canonical route.",),
    ),
    "retrospective": Profile(
        docs=("workflows/retrospective-learning.md",),
        gates=("trigger", "lesson", "promotion check", "doc update"),
    ),
}


SPILL_ACTION_LABELS: Dict[str, Tuple[str, str]] = {
    "classify": ("analysis", "classify"),
    "list": ("analysis", "classify"),
    "query": ("analysis", "classify"),
    "validate": ("build_verification", "verify"),
}


SPILL_ROUTE_LABELS: Dict[str, Tuple[str, str]] = {
    "ambiguity": ("analysis", "classify"),
    "bugfix": ("debugging", "implement"),
    "docs": ("documentation", "draft"),
    "docs-review": ("code_review", "verify"),
    "feature": ("code_generation", "implement"),
    "build": ("code_generation", "implement"),
    "multi-agent": ("architecture", "plan"),
    "plan": ("analysis", "plan"),
    "planning": ("analysis", "plan"),
    "prd": ("prd_drafting", "draft"),
    "spec": ("prd_drafting", "draft"),
    "product": ("architecture", "plan"),
    "refactor": ("refactoring", "implement"),
    "code-simplify": ("refactoring", "implement"),
    "release": ("release_packaging", "verify"),
    "ship": ("release_packaging", "verify"),
    "retrospective": ("documentation", "revise"),
    "review": ("code_review", "verify"),
    "task": ("analysis", "plan"),
    "test": ("testing", "verify"),
    "triage": ("analysis", "classify"),
    "webperf": ("build_verification", "verify"),
    "workflow-setup": ("workflow_setup", "implement"),
}


PLATFORMS: Dict[str, Tuple[str, ...]] = {
    "android": (
        "platforms/android/android-architecture.md",
        "platforms/android/android-module-structure.md",
        "platforms/android/android-viewmodel-state.md",
        "platforms/android/android-state-data.md",
        "platforms/android/android-review.md",
    ),
    "kmp": (
        "platforms/kmp/kmp-architecture.md",
        "platforms/kmp/kmp-module-structure.md",
        "platforms/kmp/kmp-compose-ui.md",
        "platforms/kmp/kmp-state-data.md",
        "platforms/kmp/kmp-platform-integration.md",
        "platforms/kmp/kmp-review.md",
    ),
    "flutter": (
        "platforms/flutter/flutter-architecture.md",
        "platforms/flutter/flutter-project-structure.md",
        "platforms/flutter/flutter-widget-ui.md",
        "platforms/flutter/flutter-state-data.md",
        "platforms/flutter/flutter-platform-integration.md",
        "platforms/flutter/flutter-review.md",
    ),
    "swift": (
        "platforms/swift/swift-architecture.md",
        "platforms/swift/swift-code-structure.md",
        "platforms/swift/swift-design-system.md",
        "platforms/swift/swift-review.md",
    ),
    "ios": (
        "platforms/swift/swift-architecture.md",
        "platforms/swift/swift-code-structure.md",
        "platforms/swift/swift-design-system.md",
        "platforms/swift/swift-review.md",
        "platforms/ios/ios-architecture.md",
        "platforms/ios/ios-module-structure.md",
        "platforms/ios/ios-state-concurrency.md",
        "platforms/ios/ios-review.md",
    ),
    "web": (
        "platforms/web/web-architecture.md",
        "platforms/web/web-code-structure.md",
        "platforms/web/web-react-ui.md",
        "platforms/web/web-state-data.md",
        "platforms/web/web-review.md",
    ),
    "server": (
        "platforms/server/server-architecture.md",
        "platforms/server/server-api-implementation.md",
        "platforms/server/server-data-jobs.md",
        "platforms/server/server-review.md",
    ),
    "application": (
        "platforms/application/application-architecture.md",
        "platforms/application/application-command-ui.md",
        "platforms/application/application-system-integration.md",
        "platforms/application/application-review.md",
    ),
}
