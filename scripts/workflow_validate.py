"""Validation checks for workflow documents and route manifests."""

from __future__ import annotations

import re
import sys

from workflow_catalog import COMMANDS, CONCERNS, CORE_DOCS, PLATFORM_CONCERNS, PLATFORMS
from workflow_common import (
    ATTEMPT_LIMIT,
    QUESTION_ROUTE_COMMANDS,
    RETRY_LIMIT,
    RETRY_SCOPE,
    ROOT,
)
from workflow_route import REVIEW_HOOK_REQUIRED_COMMANDS, resolve_docs, route_gates
from workflow_spill import validate_spill_label_contracts


MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_REQUIRED_KEYS = ("keyflow_id:", "status:", "type:")


def validate_route_contracts() -> list[str]:
    failures: list[str] = []
    failures.extend(validate_spill_label_contracts(set(COMMANDS)))

    for command in COMMANDS:
        route = resolve_docs(command, None, [], request_classified=True)

        if route["attempt_limit"] != ATTEMPT_LIMIT:
            failures.append(f"{command}: attempt_limit must be {ATTEMPT_LIMIT}")
        if route["retry_limit"] != RETRY_LIMIT:
            failures.append(f"{command}: retry_limit must be {RETRY_LIMIT}")
        if route["retry_scope"] != RETRY_SCOPE:
            failures.append(f"{command}: retry_scope must be {RETRY_SCOPE}")

        expected_gates = route_gates(command)
        if command not in QUESTION_ROUTE_COMMANDS:
            expected_gates = ["request intake", *expected_gates]
        if route["gates"] != expected_gates:
            failures.append(f"{command}: route gates do not match profile gates")

        hooks = route.get("hooks")
        if not isinstance(hooks, list):
            failures.append(f"{command}: route hooks must be a list")
            hooks = []
        hook_names = [hook.get("hook") for hook in hooks if isinstance(hook, dict)]
        if hook_names != ["start", "review", "finish"]:
            failures.append(f"{command}: route hooks must be start, review, finish")
        hook_required = {
            hook.get("hook"): hook.get("required")
            for hook in hooks
            if isinstance(hook, dict)
        }
        if hook_required.get("start") is not True:
            failures.append(f"{command}: start hook must be required")
        if hook_required.get("finish") is not True:
            failures.append(f"{command}: finish hook must be required")
        expected_review_required = command in REVIEW_HOOK_REQUIRED_COMMANDS
        if hook_required.get("review") is not expected_review_required:
            failures.append(
                f"{command}: review hook required state must be {expected_review_required}"
            )
        if expected_review_required and "review hook" not in route["gates"]:
            failures.append(f"{command}: required review hook is missing from route gates")

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

    missing = sorted(doc for doc in refs if not (ROOT / doc).exists())
    bad_route_contracts = validate_route_contracts()
    markdown_files = sorted(ROOT.rglob("*.md"))
    bad_frontmatter: list[str] = []
    bad_links: list[str] = []

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

    if missing or bad_frontmatter or bad_links or bad_route_contracts:
        return 1

    print(
        f"OK: {len(refs)} workflow references exist; "
        f"{len(markdown_files)} markdown frontmatter blocks and links are valid; "
        f"{len(COMMANDS)} route contracts are valid."
    )
    return 0
