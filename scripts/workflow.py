#!/usr/bin/env python3
"""Resolve shared AgentPlaybook workflow routes.

This script is intentionally small and dependency-free. It does not run project
commands. It produces the document route and gates an agent should use before it
executes work in a target repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from workflow_catalog import (
    BASELINE_CONCERNS,
    COMMANDS,
    CONCERNS,
    CORE_DOCS,
    PLATFORM_CONCERNS,
    PLATFORMS,
    REQUEST_CONCERN_HINTS,
    SPILL_ACTION_LABELS,
    SPILL_ROUTE_LABELS,
)


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_REQUIRED_KEYS = ("keyflow_id:", "status:", "type:")
QUESTION_ROUTE_COMMANDS = {"triage", "ambiguity"}
ANSWER_ONLY_CLARITY = "direct-question"
RETRY_LIMIT = 1
ATTEMPT_LIMIT = RETRY_LIMIT + 1
RETRY_SCOPE = "first_missed_gate"
SPILL_SETUP_HELPER = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Spill"
    / "adapters"
    / "setup"
    / "spill-token-metering-setup.mjs"
)
SPILL_ALLOWED_TOOLS = {"codex", "claude", "antigravity", "openai"}
SAFE_WORKFLOW_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")
REQUIRED_SPILL_ACTION_LABELS = {"classify", "list", "validate"}
SIGNAL_DISPLAY = {
    "SUCCESS": "\U0001f431\U0001f7e2 SUCCESS",
    "FAIL": "\U0001f431\U0001f534 FAIL",
}


def spill_tool_label() -> str:
    tool = (
        os.environ.get("SPILL_AI_TOOL")
        or os.environ.get("SPILL_TOKEN_USAGE_AI_TOOL")
        or "codex"
    )
    return tool if tool in SPILL_ALLOWED_TOOLS else "codex"


def write_spill_label(task_type: str, stage: str) -> None:
    if not SPILL_SETUP_HELPER.exists():
        return
    try:
        subprocess.run(
            [
                "node",
                str(SPILL_SETUP_HELPER),
                "--label",
                spill_tool_label(),
                "--task-type",
                task_type,
                "--stage",
                stage,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def spill_label_for_args(args: argparse.Namespace) -> Tuple[str, str]:
    if args.action == "route":
        return SPILL_ROUTE_LABELS[args.command]
    return SPILL_ACTION_LABELS.get(args.action, ("analysis", "classify"))


def display_signal(signal: object) -> str:
    return SIGNAL_DISPLAY.get(str(signal), str(signal))


def unique(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def infer_concerns_from_request(text: str) -> List[str]:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return []
    inferred: List[str] = []
    for concern, patterns in REQUEST_CONCERN_HINTS:
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            inferred.append(concern)
    return unique(inferred)


def classify_request(text: str) -> Dict[str, object]:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    tokens = normalized.split()

    direct_question_patterns = (
        r"\?",
        r"\b(what|when|where|why|how|which|who|should|do i|does|is|are|can i)\b",
        "\uc5b8\uc81c",
        "\ubb34\uc5c7",
        "\ubb50",
        "\uc5b4\ub5bb\uac8c",
        "\uc65c",
        "\uc5b4\ub514",
        "\uc5b4\ub290",
        "\ub204\uac00",
        "\uc778\uac00",
        "\ub9de\uc544",
        "\uac70\uc57c",
        "\uac74\uac00",
        "\ub098\uc694",
        "\ud569\ub2c8\uae4c",
        "\ud560\uae4c",
    )
    question_action_patterns = (
        r"\b(can you|could you|would you|please|go ahead and)\b",
        "\ud574\uc918",
        "\ud574\uc8fc\uc138\uc694",
        "\ud574\uc904\ub798",
        "\ubc14\uafd4\uc918",
        "\uace0\uccd0\uc918",
        "\uc218\uc815\ud574\uc918",
        "\uc801\uc6a9\ud574\uc918",
        "\ucd94\uac00\ud574\uc918",
        "\uba85\uc2dc\ud574\uc918",
        "\ub123\uc5b4\uc918",
        "\ub2f4\uc544\uc918",
        "\uc801\uc6a9",
        "\ub2e4\uc2dc \uc801\uc6a9",
        "\ucee4\ubc0b\ud574\uc918",
        "\ud478\uc26c\ud574\uc918",
        "\uc2e4\ud589\ud574\uc918",
        "\ub9cc\ub4e4\uc5b4\uc918",
        r"(\ud574\ubcf4\uc790|\uc9c4\ud589\ud574\uc918|\ud30c\uc545\ud574\uc918|\ud30c\uc545\uc880)",
    )
    exact_patterns = (
        r"`[^`]+`",
        r"(?:^|\s)(?:~|\.{1,2}|/)[\w./-]+",
        r"\b[\w./-]+\.(kt|swift|tsx|ts|jsx|js|py|go|rs|java|md|json|yml|yaml|toml)\b",
        r":\d+\b",
        r"\b(error|exception|traceback|stack trace|compiler|lint|test failed|failing test)\b",
        r"\b(nullpointer|typeerror|referenceerror|syntaxerror|segmentation fault)\b",
    )
    scoped_patterns = (
        r"\b[A-Z][A-Za-z0-9]*(Screen|View|ViewModel|Controller|Route|Page|Component|Service|Repository|UseCase)",
        r"\b(home|settings|profile|checkout|billing|invite|member|login|signup)\b.*\b(button|form|screen|page|modal|dialog|tab)\b",
    )
    broad_patterns = (
        r"\b(build|implement|design|create|add|plan)\b.*\b(feature|flow|system|architecture|prd|ard|product)\b",
        r"\b(auth|rbac|permission|billing|entitlement|invite|tenant|migration|release|deployment)\b",
        r"(\uc571|\uae30\ub2a5|\ud654\uba74|\uc81c\ud488|\ud50c\ub85c\uc6b0|\uc11c\ube44\uc2a4).*(\ub9cc\ub4e4|\ub9cc\ub4dc|\uad6c\ud604|\uc124\uacc4|\ucd94\uac00|\uc791\uc5c5|\uc9c4\ud589)|prd|ard|\uc694\uad6c\uc0ac\ud56d|\uc544\ud0a4\ud14d\ucc98",
    )
    risky_patterns = (
        r"\b(delete|drop|destroy|migrate|deploy|release|publish|payment|billing|secret|token|credential|permission|security|tenant)\b",
    )
    vague_patterns = (
        r"\b(fix|improve|clean up|make better|change|update|adjust|modify)\b",
        r"\b(button|home|screen|ui|layout|style)\b",
    )

    has_exact = any(re.search(pattern, normalized, re.IGNORECASE) for pattern in exact_patterns)
    has_scoped = any(re.search(pattern, normalized) for pattern in scoped_patterns)
    has_broad = any(re.search(pattern, lowered) for pattern in broad_patterns)
    has_risky = any(re.search(pattern, lowered) for pattern in risky_patterns)
    has_vague = any(re.search(pattern, lowered) for pattern in vague_patterns)
    has_direct_question = any(re.search(pattern, lowered) for pattern in direct_question_patterns)
    asks_agent_action = any(re.search(pattern, lowered) for pattern in question_action_patterns)
    short_without_target = len(tokens) <= 8 and not (has_exact or has_scoped)
    asks_drill = any(
        phrase in lowered
        for phrase in (
            "grill me",
            "ask me questions",
            "help define requirements",
            "question drill",
            "\uadf8\ub9b4\ubbf8",
        )
    )

    if has_direct_question and not asks_agent_action:
        clarity = ANSWER_ONLY_CLARITY
        effort = "standard" if has_broad else "quick"
        route = "product" if has_broad else "none"
        question_drill = False
        response_mode = "answer_first"
        reason = ("The request asks how to approach app/product/feature work. Answer first, but include the PRD -> ARD -> implementation gate before lower-level steps." if has_broad else "The request is a direct question, so answer it before starting any workflow or edit.")
    elif has_risky and not has_broad and not (has_exact or has_scoped):
        clarity = "risky-unclear"
        effort = "deep"
        route = "ambiguity"
        question_drill = True
        response_mode = "clarify_first"
        reason = "Risk-sensitive terms appear without an exact implementation target."
    elif asks_drill:
        clarity = "vague-action"
        effort = "deep" if has_broad or has_risky else "standard"
        route = "triage"
        question_drill = True
        response_mode = "clarify_first"
        reason = "The request explicitly asks for a question drill before work."
    elif has_broad and not has_exact:
        clarity = "broad-product"
        effort = "deep"
        route = "product"
        question_drill = False
        response_mode = "work"
        reason = "The request appears to define product or architecture behavior."
    elif has_exact:
        clarity = "clear-exact"
        effort = "quick"
        route = "task"
        question_drill = False
        response_mode = "work"
        reason = "The request names an exact file, symbol, command, or error signal."
    elif has_scoped:
        clarity = "clear-scoped"
        effort = "standard"
        route = "feature"
        question_drill = False
        response_mode = "work"
        reason = "The request names a scoped UI, code, or feature owner."
    elif asks_drill or has_vague or short_without_target:
        clarity = "vague-action"
        effort = "standard"
        route = "triage"
        question_drill = True
        response_mode = "clarify_first"
        reason = "The request asks for action but lacks a precise target or acceptance criteria."
    else:
        clarity = "clear-scoped"
        effort = "standard"
        route = "task"
        question_drill = False
        response_mode = "work"
        reason = "No high-risk ambiguity was detected, but local context is still needed."

    return {
        "request": normalized,
        "clarity": clarity,
        "effort": effort,
        "recommended_route": route,
        "question_drill": question_drill,
        "response_mode": response_mode,
        "reason": reason,
        "notes": [
            "Answer direct user questions before routing, editing, or running project work.",
            "Use repo-local instructions before editing.",
            "Escalate effort if local inspection finds broader risk.",
            "Use the lowest capable model or reasoning depth when the runtime supports it.",
        ],
    }


def print_classification(result: Dict[str, object]) -> None:
    print("# AgentPlaybook Request Classification")
    print()
    print(f"Clarity: `{result['clarity']}`")
    print(f"Effort: `{result['effort']}`")
    print(f"Recommended route: `{result['recommended_route']}`")
    print(f"Question drill: `{str(result['question_drill']).lower()}`")
    print(f"Response mode: `{result['response_mode']}`")
    print()
    print(f"Reason: {result['reason']}")
    print()
    print("## Next")
    if result["clarity"] == ANSWER_ONLY_CLARITY:
        print("- Answer the user's direct question first.")
        if result["recommended_route"] == "product":
            print("- Include PRD -> ARD -> implementation first; if work proceeds, run the `product` route.")
        print("- Do not start a workflow route, edit files, or run project-specific work unless a separate action remains.")
    elif result["question_drill"]:
        print("- Run `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route triage --request \"<request text>\"`.")
        print("- Ask only blocker questions after checking available local context.")
    else:
        print(
            f"- Run `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route {result['recommended_route']} "
            "--request \"<request text>\"` with matching platform/concerns when needed."
        )
        print("- Inspect the named target or smallest relevant local context first.")
    print("- Keep the route gate ledger current if a workflow route is used.")


def route_block_reason(command: str, classification: Optional[Dict[str, object]]) -> Optional[str]:
    if not classification:
        return None
    if classification["clarity"] == ANSWER_ONLY_CLARITY:
        reason = "The current request is a direct question. Answer it in the conversation before starting a workflow route, editing files, or running project-specific work."
        if classification["recommended_route"] == "product":
            reason += " Include PRD -> ARD -> implementation gates before lower-level coding steps."
        return reason
    if classification["recommended_route"] == "product" and command == "feature":
        return "The current request is broad app/product/feature work. Use route `product` so PRD and ARD gates run before implementation; do not route it as `feature`."
    if classification["question_drill"] and command not in QUESTION_ROUTE_COMMANDS:
        return (
            f"The current request needs clarification before route `{command}`. "
            "Use `triage` or `ambiguity`, ask the blocker questions, and rerun the work route "
            "only after the request is clear."
        )
    return None


def resolve_docs(
    command: str,
    platform: Optional[str],
    concerns: List[str],
    request_classification: Optional[Dict[str, object]] = None,
    request_classified: bool = False,
) -> Dict[str, object]:
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
    for concern in concerns:
        if concern in BASELINE_CONCERNS:
            notes.append(f"Concern `{concern}` is {BASELINE_CONCERNS[concern]}")

    gates = list(profile.gates)
    if command not in QUESTION_ROUTE_COMMANDS:
        gates = ["request intake", *gates]

    if request_classification:
        notes.append(
            "Request classification is attached to this route; keep it as evidence for the request intake or classify request gate."
        )
    elif request_classified:
        notes.append(
            "Caller asserted the request was already classified or answered; record that evidence for the request intake gate."
        )

    return {
        "root": str(ROOT),
        "command": command,
        "platform": platform,
        "concerns": concerns,
        "request_classification": request_classification,
        "request_classified": request_classified,
        "docs": unique(docs),
        "gates": gates,
        "attempt_limit": ATTEMPT_LIMIT,
        "retry_limit": RETRY_LIMIT,
        "retry_scope": RETRY_SCOPE,
        "gate_ledger": [
            {
                "gate": gate,
                "status": "not_started",
                "signal": "",
                "evidence": "",
            }
            for gate in gates
        ],
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
    if route["request_classification"]:
        classification = route["request_classification"]
        print("## Request Classification")
        print(f"- Clarity: `{classification['clarity']}`")
        print(f"- Effort: `{classification['effort']}`")
        print(f"- Recommended route: `{classification['recommended_route']}`")
        print(f"- Question drill: `{str(classification['question_drill']).lower()}`")
        print(f"- Response mode: `{classification['response_mode']}`")
        print(f"- Reason: {classification['reason']}")
        print()
    elif route["request_classified"]:
        print("## Request Classification")
        print("- Caller asserted the current request was already classified or answered before this route.")
        print("- Record that evidence before reporting `request intake` SUCCESS.")
        print()
    print("## Read In Order")
    for doc in route["docs"]:
        print(f"- `{doc}`")
    print()
    print("## Gates")
    for gate in route["gates"]:
        print(f"- {gate}")
    print()
    print("## Gate Execution Ledger")
    print(f"Attempt limit: `{ATTEMPT_LIMIT}`")
    print(f"Recovery retry limit: `{RETRY_LIMIT}`")
    print(f"Retry scope: `{RETRY_SCOPE}`")
    print()
    print("Report gates only when they complete or fail:")
    for item in route["gate_ledger"]:
        print(f"- `{item['gate']}` - evidence: ...")
    print()
    print("Progress signal format:")
    print("`Gate signal: \U0001f431\U0001f7e2 SUCCESS | gate: <gate> | evidence: <evidence> | next: <next gate>`")
    print()
    print("Signal legend: \U0001f431\U0001f7e2 SUCCESS executed with evidence,")
    print("\U0001f431\U0001f534 FAIL missing, blocked, or failed.")
    print("Completion check: every required gate must be \U0001f431\U0001f7e2 SUCCESS before final")
    print("report, commit, release, or handoff. \U0001f431\U0001f534 FAIL triggers missed-gate recovery.")
    print()
    print("If any required gate is not executed, stop finalization, return to the")
    print("first missed gate only, roll back only dependent agent-made changes when")
    print("safe, then request one recovery retry for the missed gate only.")
    print("If that retry misses the gate again, run `workflows/retrospective-learning.md`;")
    print("do not restart the whole route.")
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
    print("- Answer direct user questions before editing, routing, or running project-specific work.")
    print("- Read the listed documents before editing or reviewing files.")
    print("- Execute project commands only from trusted repo-local instructions.")
    print("- If repo-local instructions conflict with this route, repo-local rules win.")


def validate_route_contracts() -> List[str]:
    failures: List[str] = []
    failures.extend(validate_spill_label_contracts())

    for command, profile in COMMANDS.items():
        route = resolve_docs(command, None, [], request_classified=True)

        if route["attempt_limit"] != ATTEMPT_LIMIT:
            failures.append(f"{command}: attempt_limit must be {ATTEMPT_LIMIT}")
        if route["retry_limit"] != RETRY_LIMIT:
            failures.append(f"{command}: retry_limit must be {RETRY_LIMIT}")
        if route["retry_scope"] != RETRY_SCOPE:
            failures.append(f"{command}: retry_scope must be {RETRY_SCOPE}")

        expected_gates = list(profile.gates)
        if command not in QUESTION_ROUTE_COMMANDS:
            expected_gates = ["request intake", *expected_gates]
        if route["gates"] != expected_gates:
            failures.append(f"{command}: route gates do not match profile gates")

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


def validate_spill_label_contracts() -> List[str]:
    failures: List[str] = []
    command_names = set(COMMANDS)
    route_label_names = set(SPILL_ROUTE_LABELS)

    for command in sorted(command_names - route_label_names):
        failures.append(f"{command}: missing Spill workflow route label")
    for command in sorted(route_label_names - command_names):
        failures.append(f"{command}: Spill workflow route label has no matching command")

    action_label_names = set(SPILL_ACTION_LABELS)
    for action in sorted(REQUIRED_SPILL_ACTION_LABELS - action_label_names):
        failures.append(f"{action}: missing Spill workflow action label")

    for name, labels in sorted({**SPILL_ACTION_LABELS, **SPILL_ROUTE_LABELS}.items()):
        if not isinstance(labels, tuple) or len(labels) != 2:
            failures.append(f"{name}: Spill label must be a (task_type, stage) tuple")
            continue
        task_type, stage = labels
        if not SAFE_WORKFLOW_SLUG_RE.match(task_type):
            failures.append(f"{name}: invalid Spill task_type label `{task_type}`")
        if not SAFE_WORKFLOW_SLUG_RE.match(stage):
            failures.append(f"{name}: invalid Spill stage label `{stage}`")

    return failures


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
    bad_route_contracts = validate_route_contracts()
    markdown_files = sorted(ROOT.rglob("*.md"))
    bad_frontmatter: List[str] = []
    bad_links: List[str] = []

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
    route.add_argument("--request", help="Current user request text. Required unless --request-classified is used.")
    route.add_argument(
        "--request-classified",
        action="store_true",
        help="Assert the current request was already classified or answered before routing.",
    )
    route.add_argument("--format", choices=("markdown", "json"), default="markdown")

    classify = subparsers.add_parser("classify", help="Classify request clarity and effort.")
    classify.add_argument("request", help="User request text to classify.")
    classify.add_argument("--format", choices=("markdown", "json"), default="markdown")

    subparsers.add_parser("list", help="List available commands, platforms, and concerns.")
    subparsers.add_parser("validate", help="Validate route references, markdown frontmatter, and links.")
    return parser


def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    task_type, stage = spill_label_for_args(args)
    write_spill_label(task_type, stage)

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

    if args.action == "classify":
        result = classify_request(args.request)
        if args.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print_classification(result)
        return 0

    request_classification = classify_request(args.request) if args.request else None
    if not request_classification and not args.request_classified:
        print(
            "Route requires request intake evidence. Pass --request \"<USER_REQUEST>\" "
            "or --request-classified after answering/classifying the current request.",
            file=sys.stderr,
        )
        return 2

    block_reason = route_block_reason(args.command, request_classification)
    if block_reason:
        print(block_reason, file=sys.stderr)
        if request_classification:
            print(
                f"Classification: {request_classification['clarity']} / "
                f"response_mode: {request_classification['response_mode']} / "
                f"question_drill: {str(request_classification['question_drill']).lower()}",
                file=sys.stderr,
            )
        return 2

    inferred_concerns = infer_concerns_from_request(args.request or "")
    concerns = unique([*args.concern, *inferred_concerns])
    newly_inferred = [concern for concern in inferred_concerns if concern not in args.concern]

    route = resolve_docs(
        args.command,
        args.platform,
        concerns,
        request_classification=request_classification,
        request_classified=args.request_classified,
    )
    if newly_inferred:
        route["inferred_concerns"] = newly_inferred
        notes = route.get("notes")
        if isinstance(notes, list):
            joined = ", ".join(f"`{concern}`" for concern in newly_inferred)
            notes.append(f"Inferred concern(s) from request keywords: {joined}.")
    if args.format == "json":
        print(json.dumps(route, indent=2, sort_keys=True))
    else:
        print_markdown(route)
    return 1 if route["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
