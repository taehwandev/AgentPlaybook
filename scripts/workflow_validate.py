"""Validation checks for workflow documents and route manifests."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from agent_finish_gate_policy import VALIDATED_GATES
from workflow_catalog import COMMANDS, CONCERNS, CORE_DOCS, PLATFORM_CONCERNS, PLATFORMS
from workflow_common import (
    ATTEMPT_LIMIT,
    QUESTION_ROUTE_COMMANDS,
    RETRY_LIMIT,
    RETRY_SCOPE,
    ROOT,
)
from workflow_doc_surfaces import load_doc_surface_rules, surface_rule_doc_refs
from workflow_gate_policy import automatic_gates
from workflow_parallel_validate import validate_parallel_execution_plan
from workflow_route import REVIEW_HOOK_REQUIRED_COMMANDS, resolve_docs, route_gates
from workflow_spill import validate_spill_label_contracts


MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_REQUIRED_KEYS = ("keyflow_id:", "status:", "type:")
STRICT_CARD_MARKER = "agentplaybook_card_contract: strict"
STRICT_CARD_REQUIRED_HEADINGS = (
    "## Use When",
    "## Decision Rule",
    "## Common Rationalizations",
    "## Red Flags",
    "## Do Not",
    "## Stop If",
    "## Verification",
)
MARKDOWN_VALIDATE_IGNORED_DIRS = {
    ".agentplaybook",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}
MULTI_AGENT_VALIDATED_GATES = {
    "roles",
    "write scopes",
    "agent briefs",
    "integration review",
}
PROFILE_VALIDATED_GATES = {
    "docs-review": {"review readiness"},
    "product": {"platform selection"},
}


def validate_route_contracts() -> list[str]:
    failures: list[str] = []
    failures.extend(validate_spill_label_contracts(set(COMMANDS)))

    for command in COMMANDS:
        route = resolve_docs(command, None, [], request_classified=True)
        if route.get("missing"):
            failures.append(f"{command}: route has missing docs: {', '.join(route['missing'])}")

        if route["attempt_limit"] != ATTEMPT_LIMIT:
            failures.append(f"{command}: attempt_limit must be {ATTEMPT_LIMIT}")
        if route["retry_limit"] != RETRY_LIMIT:
            failures.append(f"{command}: retry_limit must be {RETRY_LIMIT}")
        if route["retry_scope"] != RETRY_SCOPE:
            failures.append(f"{command}: retry_scope must be {RETRY_SCOPE}")
        for failure in validate_parallel_execution_plan(route.get("parallel_execution"), route["gates"]):
            failures.append(f"{command}: {failure}")

        expected_gates = route_gates(command)
        if command not in QUESTION_ROUTE_COMMANDS:
            expected_gates = ["request intake", *expected_gates]
        if route["gates"] != expected_gates:
            failures.append(f"{command}: route gates do not match profile gates")
        for gate in automatic_gates(command):
            if gate not in route["gates"]:
                failures.append(f"{command}: automatic gate `{gate}` is missing")
            if gate not in VALIDATED_GATES:
                failures.append(f"{command}: automatic gate `{gate}` has no finish evidence validator")

        hooks = route.get("hooks")
        if not isinstance(hooks, list):
            failures.append(f"{command}: route hooks must be a list")
            hooks = []
        hook_names = [hook.get("hook") for hook in hooks if isinstance(hook, dict)]
        expected_hook_names = ["start", "review", "finish"]
        if "route docs read" in route["gates"]:
            expected_hook_names.insert(1, "docs-read")
        if hook_names != expected_hook_names:
            failures.append(f"{command}: route hooks must be {', '.join(expected_hook_names)}")
        hook_required = {
            hook.get("hook"): hook.get("required")
            for hook in hooks
            if isinstance(hook, dict)
        }
        if hook_required.get("start") is not True:
            failures.append(f"{command}: start hook must be required")
        if "route docs read" in route["gates"] and hook_required.get("docs-read") is not True:
            failures.append(f"{command}: docs-read hook must be required")
        if hook_required.get("finish") is not True:
            failures.append(f"{command}: finish hook must be required")
        expected_review_required = command in REVIEW_HOOK_REQUIRED_COMMANDS
        if hook_required.get("review") is not expected_review_required:
            failures.append(
                f"{command}: review hook required state must be {expected_review_required}"
            )
        if expected_review_required and "review hook" not in route["gates"]:
            failures.append(f"{command}: required review hook is missing from route gates")
        if command == "multi-agent":
            missing_validators = sorted(MULTI_AGENT_VALIDATED_GATES - VALIDATED_GATES)
            if missing_validators:
                failures.append(
                    f"{command}: missing finish evidence validators for {', '.join(missing_validators)}"
                )
        for gate in sorted(PROFILE_VALIDATED_GATES.get(command, set())):
            if gate not in route["gates"]:
                failures.append(f"{command}: validated profile gate `{gate}` is not in route gates")
            if gate not in VALIDATED_GATES:
                failures.append(f"{command}: validated profile gate `{gate}` has no finish evidence validator")

        ledger = route["gate_ledger"]
        if len(ledger) != len(route["gates"]):
            failures.append(f"{command}: gate_ledger length does not match gates")
            continue

        for gate, item in zip(route["gates"], ledger):
            if item["gate"] != gate:
                failures.append(f"{command}: ledger gate `{item['gate']}` does not match `{gate}`")
            if item["status"] != "not_started":
                failures.append(f"{command}: initial ledger status for `{gate}` must be not_started")
            if item["signal"] != "":
                failures.append(f"{command}: initial ledger signal for `{gate}` must be empty")
            if item["evidence"] != "":
                failures.append(f"{command}: initial ledger evidence for `{gate}` must be empty")

    return failures


def validate() -> int:
    refs: set[str] = set(CORE_DOCS)
    for profile in COMMANDS.values():
        refs.update(profile.docs)
    for docs in PLATFORMS.values():
        refs.update(docs)
    for docs in CONCERNS.values():
        refs.update(docs)
    for docs in PLATFORM_CONCERNS.values():
        refs.update(docs)
    surface_rules = load_doc_surface_rules(ROOT)
    surface_docs, bad_surface_refs = surface_rule_doc_refs(surface_rules)
    refs.update(surface_docs)

    missing = sorted(doc for doc in refs if not (ROOT / doc).exists())
    bad_route_contracts = validate_route_contracts()
    markdown_files = markdown_files_to_validate(ROOT)
    bad_frontmatter: list[str] = []
    bad_links: list[str] = []
    bad_card_quality: list[str] = []

    for path in markdown_files:
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            bad_frontmatter.append(f"{relative}: missing frontmatter")
            continue
        end = text.find("\n---", 4)
        if end == -1:
            bad_frontmatter.append(f"{relative}: unterminated frontmatter")
            continue
        header = text[4:end]
        missing_keys = [key[:-1] for key in FRONTMATTER_REQUIRED_KEYS if key not in header]
        if missing_keys:
            bad_frontmatter.append(f"{relative}: missing {', '.join(missing_keys)}")
        if STRICT_CARD_MARKER in header:
            missing_headings = [
                heading for heading in STRICT_CARD_REQUIRED_HEADINGS if not _has_heading(text, heading)
            ]
            if missing_headings:
                bad_card_quality.append(
                    f"{relative}: strict card missing {', '.join(missing_headings)}"
                )

        for raw_link in MARKDOWN_LINK_RE.findall(text):
            link = raw_link.strip()
            target = link.split("#", 1)[0].split(" ", 1)[0].strip("<>")
            if not target or target.startswith("#"):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            if not (path.parent / target).resolve().exists():
                bad_links.append(f"{relative}: {raw_link}")

    if missing:
        print("Missing workflow references:", file=sys.stderr)
        for doc in missing:
            print(f"- {doc}", file=sys.stderr)
    if bad_frontmatter:
        print("Invalid markdown frontmatter:", file=sys.stderr)
        for item in bad_frontmatter:
            print(f"- {item}", file=sys.stderr)
    if bad_links:
        print("Broken markdown links:", file=sys.stderr)
        for item in bad_links:
            print(f"- {item}", file=sys.stderr)
    if bad_route_contracts:
        print("Invalid workflow route contracts:", file=sys.stderr)
        for item in bad_route_contracts:
            print(f"- {item}", file=sys.stderr)
    if bad_surface_refs:
        print("Invalid workflow document surface rules:", file=sys.stderr)
        for item in bad_surface_refs:
            print(f"- {item}", file=sys.stderr)
    if bad_card_quality:
        print("Invalid strict card anatomy:", file=sys.stderr)
        for item in bad_card_quality:
            print(f"- {item}", file=sys.stderr)

    if missing or bad_frontmatter or bad_links or bad_route_contracts or bad_surface_refs or bad_card_quality:
        return 1

    print(
        f"OK: {len(refs)} workflow references exist; "
        f"{len(markdown_files)} markdown frontmatter blocks and links are valid; "
        f"{len(COMMANDS)} route contracts are valid."
    )
    return 0


def _has_heading(text: str, heading: str) -> bool:
    return re.search(rf"^{re.escape(heading)}(?:\s|$)", text, re.MULTILINE) is not None


def markdown_files_to_validate(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not MARKDOWN_VALIDATE_IGNORED_DIRS.intersection(path.relative_to(root).parts)
    )
