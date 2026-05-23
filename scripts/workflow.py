#!/usr/bin/env python3
"""Resolve shared AgentPlaybook workflow routes.

This script is intentionally small and dependency-free. It does not run project
commands. It produces the document route and gates an agent should use before it
executes work in a target repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]


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
)


COMMANDS: Dict[str, Profile] = {
    "task": Profile(
        docs=("workflows/agent-task-lifecycle.md",),
        gates=("orient", "scope", "act", "verify", "report"),
        notes=("Use for general multi-step agent work.",),
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
    "ambiguity": Profile(
        docs=("workflows/ambiguity-gate.md", "common/product-spec-to-implementation.md"),
        gates=("classify unknowns", "research repo-answerable items", "ask blockers", "record assumptions"),
        notes=("Use before PRD, ARD, task breakdown, or implementation when unknowns can change behavior or risk.",),
    ),
    "feature": Profile(
        docs=(
            "workflows/feature-implementation.md",
            "workflows/development-cycle.md",
            "common/product-spec-to-implementation.md",
        ),
        gates=("acceptance criteria", "implementation", "verification", "handoff"),
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
        gates=("source review", "structure review", "link/path check", "verification", "handoff"),
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
        ),
        gates=("package", "config", "smoke", "rollback", "handoff"),
    ),
    "retrospective": Profile(
        docs=("workflows/retrospective-learning.md",),
        gates=("trigger", "lesson", "promotion check", "doc update"),
    ),
}


PLATFORMS: Dict[str, Tuple[str, ...]] = {
    "android": (
        "platforms/android/android-architecture.md",
        "platforms/android/android-state-data.md",
        "platforms/android/android-review.md",
    ),
    "ios": (
        "platforms/ios/ios-architecture.md",
        "platforms/ios/ios-state-concurrency.md",
        "platforms/ios/ios-review.md",
    ),
    "web": (
        "platforms/web/web-architecture.md",
        "platforms/web/web-state-data.md",
        "platforms/web/web-review.md",
    ),
    "server": (
        "platforms/server/server-architecture.md",
        "platforms/server/server-data-jobs.md",
        "platforms/server/server-review.md",
    ),
    "application": (
        "platforms/application/application-architecture.md",
        "platforms/application/application-system-integration.md",
        "platforms/application/application-review.md",
    ),
}


CONCERNS: Dict[str, Tuple[str, ...]] = {
    "security": ("common/secure-development-baseline.md", "common/security-privacy-review.md"),
    "api": ("common/api-contract-compatibility.md",),
    "ui": ("common/design-system.md", "common/ui-visual-verification.md"),
    "accessibility": ("common/accessibility-i18n.md",),
    "persistence": ("common/data-persistence-sync.md",),
    "cache": ("common/server-side-caching.md",),
    "release": ("common/release-deployment.md", "common/release-versioning.md"),
    "dependency": ("common/dependency-policy.md",),
    "generated": ("common/generated-files-policy.md",),
    "worktree": ("common/worktree-hygiene.md",),
    "stack": ("common/stack-discovery.md",),
    "failure": ("common/tool-failure-recovery.md",),
    "interaction": ("common/agent-interaction.md",),
    "defensive": ("common/defensive-boundaries.md",),
    "observability": ("common/observability-error-handling.md",),
    "wiki": ("workflows/documentation-update.md", "common/llm-wiki-documentation.md"),
    "auth": ("product-patterns/auth-rbac-permissions.md",),
    "invite": ("product-patterns/invitation-workflows.md",),
    "billing": ("product-patterns/billing-entitlements.md",),
}


PLATFORM_CONCERNS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("android", "security"): ("platforms/android/android-security.md",),
    ("android", "background"): ("platforms/android/android-background-work.md",),
    ("ios", "security"): ("platforms/ios/ios-security.md",),
    ("web", "accessibility"): ("platforms/web/web-accessibility-i18n.md",),
    ("application", "security"): ("platforms/application/application-security.md",),
}


def unique(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def resolve_docs(command: str, platform: Optional[str], concerns: List[str]) -> Dict[str, object]:
    profile = COMMANDS[command]
    docs: List[str] = [*CORE_DOCS, *profile.docs]

    if platform:
        docs.extend(PLATFORMS[platform])

    for concern in concerns:
        docs.extend(CONCERNS.get(concern, ()))
        if platform:
            docs.extend(PLATFORM_CONCERNS.get((platform, concern), ()))

    missing = [doc for doc in unique(docs) if not (ROOT / doc).exists()]
    notes = list(profile.notes)
    if command == "product" and not platform:
        notes.append("Select at least one platform card before writing ARD.")

    return {
        "root": str(ROOT),
        "command": command,
        "platform": platform,
        "concerns": concerns,
        "docs": unique(docs),
        "gates": list(profile.gates),
        "notes": notes,
        "missing": missing,
    }


def print_markdown(route: Dict[str, object]) -> None:
    print("# AgentPlaybook Workflow Route")
    print()
    print(f"Command: `{route['command']}`")
    if route["platform"]:
        print(f"Platform: `{route['platform']}`")
    if route["concerns"]:
        concerns = ", ".join(f"`{item}`" for item in route["concerns"])
        print(f"Concerns: {concerns}")
    print()
    print("## Read In Order")
    for doc in route["docs"]:
        print(f"- `{doc}`")
    print()
    print("## Gates")
    for gate in route["gates"]:
        print(f"- {gate}")
    if route["notes"]:
        print()
        print("## Notes")
        for note in route["notes"]:
            print(f"- {note}")
    if route["missing"]:
        print()
        print("## Missing Documents")
        for doc in route["missing"]:
            print(f"- `{doc}`")
    print()
    print("## Agent Contract")
    print("- Treat this route as the command manifest for the task.")
    print("- Read the listed documents before editing or reviewing files.")
    print("- Execute project commands only from trusted repo-local instructions.")
    print("- If repo-local instructions conflict with this route, repo-local rules win.")


def validate() -> int:
    refs: Set[str] = set(CORE_DOCS)
    for profile in COMMANDS.values():
        refs.update(profile.docs)
    for docs in PLATFORMS.values():
        refs.update(docs)
    for docs in CONCERNS.values():
        refs.update(docs)
    for docs in PLATFORM_CONCERNS.values():
        refs.update(docs)

    missing = sorted(doc for doc in refs if not (ROOT / doc).exists())
    if missing:
        print("Missing workflow references:", file=sys.stderr)
        for doc in missing:
            print(f"- {doc}", file=sys.stderr)
        return 1

    print(f"OK: {len(refs)} workflow references exist.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve AgentPlaybook workflow routes.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    route = subparsers.add_parser("route", help="Print a workflow route manifest.")
    route.add_argument("command", choices=sorted(COMMANDS), help="Task command profile.")
    route.add_argument("--platform", choices=sorted(PLATFORMS), help="Affected platform.")
    route.add_argument(
        "--concern",
        action="append",
        default=[],
        choices=sorted(set(CONCERNS) | {key[1] for key in PLATFORM_CONCERNS}),
        help="Affected concern. Can be repeated.",
    )
    route.add_argument("--format", choices=("markdown", "json"), default="markdown")

    subparsers.add_parser("list", help="List available commands, platforms, and concerns.")
    subparsers.add_parser("validate", help="Validate referenced document paths.")
    return parser


def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.action == "list":
        print("Commands:")
        for name in sorted(COMMANDS):
            print(f"- {name}")
        print("Platforms:")
        for name in sorted(PLATFORMS):
            print(f"- {name}")
        print("Concerns:")
        for name in sorted(set(CONCERNS) | {key[1] for key in PLATFORM_CONCERNS}):
            print(f"- {name}")
        return 0

    if args.action == "validate":
        return validate()

    route = resolve_docs(args.command, args.platform, args.concern)
    if args.format == "json":
        print(json.dumps(route, indent=2, sort_keys=True))
    else:
        print_markdown(route)
    return 1 if route["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
