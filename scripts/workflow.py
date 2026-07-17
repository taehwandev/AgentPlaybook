#!/usr/bin/env python3
"""Resolve shared AgentPlaybook workflow routes.

This CLI does not run project commands. It produces the document route and
gates an agent should use before it executes work in a target repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_execution_capsule_bindings import preflight_identity_failures
from workflow_catalog import COMMANDS, CONCERNS, PLATFORM_CONCERNS, PLATFORMS
from workflow_common import ROOT, unique
from workflow_dispatch import (
    WORK_KINDS,
    build_dispatch_manifest,
    execute_dispatch_manifest,
    print_dispatch_manifest,
)
from workflow_request import (
    classified_route_block_reason,
    classify_request,
    infer_concerns_from_request,
    print_classification,
    route_block_reason,
)
from workflow_output import print_markdown
from workflow_route import resolve_docs
from workflow_search import print_query_results, search_docs_outcome
from workflow_spill import spill_label_for_args, write_spill_label
from workflow_validate import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve AgentPlaybook workflow routes.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    route = subparsers.add_parser("route", help="Print a workflow route manifest.")
    route.add_argument("command", choices=sorted(COMMANDS), help="Task command profile.")
    route.add_argument(
        "--project",
        help="Target project root used for target-project readiness checks.",
    )
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
        "--surface-path",
        action="append",
        default=[],
        help="Path already known to be in scope; can be repeated. Used to promote required docs from workflow-doc-surfaces.json.",
    )
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

    _add_dispatch_parser(subparsers)

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


def _add_dispatch_parser(subparsers: argparse._SubParsersAction) -> None:
    dispatch = subparsers.add_parser(
        "dispatch", help="Build a Codex task handoff from a workflow profile."
    )
    dispatch.add_argument("command", choices=sorted(COMMANDS), help="Task command profile.")
    dispatch.add_argument("--request", required=True, help="Current user request text.")
    dispatch.add_argument("--request-classified", action="store_true")
    dispatch.add_argument("--classification-evidence", default="")
    dispatch.add_argument("--project", default=".", help="Target project root for the delegated Codex task.")
    dispatch.add_argument("--rules", type=Path, default=ROOT)
    dispatch.add_argument("--evidence", type=Path)
    dispatch.add_argument("--worker-evidence", type=Path)
    dispatch.add_argument("--worker-reservation-token", default="")
    dispatch.add_argument("--work-kind", choices=WORK_KINDS, default="auto")
    dispatch.add_argument("--complexity-evidence", default="")
    dispatch.add_argument("--platform", choices=sorted(PLATFORMS), help="Affected platform.")
    dispatch.add_argument(
        "--concern",
        action="append",
        default=[],
        choices=sorted(set(CONCERNS) | {key[1] for key in PLATFORM_CONCERNS}),
        help="Affected concern. Can be repeated.",
    )
    dispatch.add_argument("--format", choices=("markdown", "json"), default="markdown")
    dispatch.add_argument("--parent-model", default="")
    dispatch.add_argument("--parent-reasoning-effort", default="")
    dispatch.add_argument("--parent-sandbox-mode", default="")
    dispatch.add_argument("--require-isolation", action="store_true")
    dispatch.add_argument("--heartbeat-interval-seconds", type=float, default=0)
    dispatch.add_argument("--execute", action="store_true")


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
    outcome = search_docs_outcome(ROOT, query_str, max_results=args.max_results)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "query": query_str,
                    "backend": outcome.backend,
                    "backend_version": outcome.backend_version,
                    "fallback_reason": outcome.fallback_reason,
                    "weak": outcome.weak,
                    "partial": outcome.partial,
                    "fused": outcome.fused,
                    "results": outcome.results,
                },
                indent=2,
            )
        )
    else:
        print_query_results(query_str, outcome.results)
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
    # A classified handoff deliberately keeps the original request for identity
    # binding, even when that text is a short confirmation such as "yes".  Its
    # classification evidence, not a second classification of that reply, is
    # the authority for opening the selected work route.
    request_classification = (
        None
        if args.request_classified
        else (classify_request(args.request) if args.request else None)
    )
    if not request_classification and not args.request_classified:
        print(
            "Route requires request intake evidence. Pass --request \"<USER_REQUEST>\" "
            "or --request-classified after answering/classifying the current request.",
            file=sys.stderr,
        )
        return 2

    block_reason = route_block_reason(args.command, request_classification)
    if not block_reason and args.request_classified:
        block_reason = classified_route_block_reason(args.command, args.classification_evidence or "")
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

    intent_text = args.request or args.classification_evidence or ""
    inferred_concerns = infer_concerns_from_request(intent_text)
    concerns = unique([*args.concern, *inferred_concerns])
    newly_inferred = [concern for concern in inferred_concerns if concern not in args.concern]

    route = resolve_docs(
        args.command,
        args.platform,
        concerns,
        request_classification=request_classification,
        request_classified=args.request_classified,
        classification_evidence=args.classification_evidence or "",
        request_text=intent_text,
        surface_paths=args.surface_path,
        project_root=Path(args.project).resolve() if args.project else None,
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
    return 1 if route["missing"] or route.get("blocking") else 0


def print_dispatch(args: argparse.Namespace) -> int:
    if args.request_classified and not args.classification_evidence:
        print(
            "Dispatch --request-classified requires --classification-evidence so request intake cannot be skipped silently.",
            file=sys.stderr,
        )
        return 2
    request_classification = (
        None if args.request_classified else classify_request(args.request)
    )
    block_reason = (
        classified_route_block_reason(args.command, args.classification_evidence)
        if args.request_classified
        else route_block_reason(args.command, request_classification)
    )
    if block_reason:
        print(block_reason, file=sys.stderr)
        return 2

    project = Path(args.project).resolve()
    rules = args.rules.expanduser().resolve()
    evidence_path = (
        args.evidence.expanduser().resolve()
        if args.evidence
        else project / ".agentplaybook" / "preflight.json"
    )
    parent_identity_matches = _preflight_identity_matches(
        evidence_path,
        project=project,
        rules=rules,
    )
    parent_route = _parent_dispatch_route(
        evidence_path,
        command=args.command,
        request=args.request,
        request_classified=args.request_classified,
        classification_evidence=args.classification_evidence,
        platform=args.platform,
        concerns=args.concern,
        project=project,
        rules=rules,
    )
    if not parent_identity_matches:
        evidence_path = project / ".agentplaybook" / "preflight.json"
    route = parent_route
    if route is None:
        inferred_concerns = infer_concerns_from_request(args.request)
        route = resolve_docs(
            args.command,
            args.platform,
            unique([*args.concern, *inferred_concerns]),
            request_classification=request_classification,
            request_classified=args.request_classified,
            classification_evidence=args.classification_evidence,
            request_text=args.request,
            project_root=project,
        )
    if route["missing"] or route.get("blocking"):
        print("Dispatch route is blocked:", file=sys.stderr)
        for item in [*route["missing"], *(route.get("blocking") or [])]:
            print(f"- {item}", file=sys.stderr)
        return 1
    try:
        manifest = build_dispatch_manifest(
            args.command,
            args.request,
            Path(args.project),
            work_kind=args.work_kind,
            complexity_evidence=args.complexity_evidence,
            route=route,
            request_classified=args.request_classified,
            classification_evidence=args.classification_evidence,
            request_classification=request_classification,
            parent_model=args.parent_model,
            parent_reasoning_effort=args.parent_reasoning_effort,
            parent_sandbox_mode=args.parent_sandbox_mode,
            isolation_required=args.require_isolation,
            heartbeat_interval_seconds=args.heartbeat_interval_seconds,
            rules=rules,
            evidence_path=evidence_path,
            worker_evidence_path=args.worker_evidence,
            reserve_worker_evidence=args.execute,
            worker_reservation_token=args.worker_reservation_token,
            parent_context_reusable=parent_route is not None,
            defer_capsule_validation=args.execute,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    if args.execute:
        try:
            return execute_dispatch_manifest(manifest)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        except (OSError, RuntimeError) as error:
            print(error, file=sys.stderr)
            return 1
    print_dispatch_manifest(manifest, args.format)
    return 0


def _parent_dispatch_route(
    evidence_path: Path,
    *,
    command: str,
    request: str,
    request_classified: bool,
    classification_evidence: str,
    platform: str | None,
    concerns: list[str],
    project: Path,
    rules: Path,
) -> dict[str, object] | None:
    """Reuse the parent start route without mutating its handoff capsule."""

    if not _preflight_identity_matches(evidence_path, project=project, rules=rules):
        return None
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    route = payload.get("route") if isinstance(payload, dict) else None
    if not isinstance(route, dict) or route.get("command") != command:
        return None
    if platform and route.get("platform") != platform:
        return None
    routed_concerns = {
        str(item) for item in (route.get("concerns") or []) if str(item).strip()
    }
    if any(concern not in routed_concerns for concern in concerns):
        return None
    intake = payload.get("request_intake")
    if not isinstance(intake, dict):
        return None
    if request_classified:
        if not intake.get("request_classified"):
            return None
        if intake.get("classification_evidence") != classification_evidence:
            return None
        # A classification description is reusable policy evidence, not a
        # request identity.  Reuse a classified parent route only when start
        # also captured the exact current request; otherwise resolve a fresh
        # route and keep the old capsule invalid for this dispatch.
        if not intake.get("request") or intake.get("request") != request:
            return None
    elif intake.get("request") != request:
        return None
    return dict(route)


def _preflight_identity_matches(
    evidence_path: Path,
    *,
    project: Path,
    rules: Path,
) -> bool:
    return not preflight_identity_failures(evidence_path, project, rules)


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
    if args.action == "dispatch":
        return print_dispatch(args)
    return print_route(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
