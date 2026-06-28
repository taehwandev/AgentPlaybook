#!/usr/bin/env python3
"""Resolve shared AgentPlaybook workflow routes.

This CLI does not run project commands. It produces the document route and
gates an agent should use before it executes work in a target repository.
"""

from __future__ import annotations

import argparse
import json
import sys

from workflow_catalog import COMMANDS, CONCERNS, PLATFORM_CONCERNS, PLATFORMS
from workflow_common import ROOT, unique
from workflow_request import (
    classify_request,
    infer_concerns_from_request,
    print_classification,
    route_block_reason,
)
from workflow_output import print_markdown
from workflow_route import resolve_docs
from workflow_search import print_query_results, search_docs
from workflow_spill import spill_label_for_args, write_spill_label
from workflow_validate import validate


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
    route.add_argument(
        "--classification-evidence",
        help="Required with --request-classified; describes the prior classification or answer-first handling.",
    )
    route.add_argument("--format", choices=("markdown", "json"), default="markdown")

    classify = subparsers.add_parser("classify", help="Classify request clarity and effort.")
    classify.add_argument("request", help="User request text to classify.")
    classify.add_argument("--format", choices=("markdown", "json"), default="markdown")

    query = subparsers.add_parser("query", help="Search playbook docs by keyword relevance.")
    query.add_argument("terms", nargs="+", help="Search terms (space-separated keywords).")
    query.add_argument(
        "--max",
        type=int,
        default=8,
        dest="max_results",
        help="Maximum results to return (default: 8).",
    )
    query.add_argument("--format", choices=("markdown", "json"), default="markdown")

    subparsers.add_parser("list", help="List available commands, platforms, and concerns.")
    subparsers.add_parser("validate", help="Validate route references, markdown frontmatter, and links.")
    return parser


def print_supported_values() -> None:
    print("Commands:")
    for name in sorted(COMMANDS):
        print(f"- {name}")
    print("Platforms:")
    for name in sorted(PLATFORMS):
        print(f"- {name}")
    print("Concerns:")
    for name in sorted(set(CONCERNS) | {key[1] for key in PLATFORM_CONCERNS}):
        print(f"- {name}")


def print_query(args: argparse.Namespace) -> int:
    query_str = " ".join(args.terms)
    results = search_docs(ROOT, query_str, max_results=args.max_results)
    if args.format == "json":
        print(json.dumps({"query": query_str, "results": results}, indent=2))
    else:
        print_query_results(query_str, results)
    return 0


def print_request_classification(args: argparse.Namespace) -> int:
    result = classify_request(args.request)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_classification(result)
    return 0


def print_route(args: argparse.Namespace) -> int:
    if args.request_classified and not args.classification_evidence:
        print(
            "Route --request-classified requires --classification-evidence so request intake cannot be skipped silently.",
            file=sys.stderr,
        )
        return 2
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
                f"grill_me: {str(request_classification['grill_me']).lower()}",
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
        classification_evidence=args.classification_evidence or "",
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


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    task_type, stage = spill_label_for_args(args)
    write_spill_label(task_type, stage)

    if args.action == "list":
        print_supported_values()
        return 0
    if args.action == "validate":
        return validate()
    if args.action == "query":
        return print_query(args)
    if args.action == "classify":
        return print_request_classification(args)
    return print_route(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
