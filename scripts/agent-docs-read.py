#!/usr/bin/env python3
"""Read routed AgentPlaybook docs and write an auditable receipt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_finish_check_steps import read_preflight, resolve_paths
from agent_finish_common import write_json
from agent_route_docs import build_route_doc_receipt, receipt_path_for_evidence


def build_parser(playbook_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a receipt for routed document reads.")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--rules", type=Path, default=playbook_root)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument(
        "--receipt-output",
        type=Path,
        help="where to write the route-docs-read receipt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="legacy alias for --receipt-output",
    )
    return parser


def main() -> int:
    playbook_root = Path(__file__).resolve().parents[1]
    args = build_parser(playbook_root).parse_args()
    project, _rules, evidence_path, _finish_output = resolve_paths(args)
    failures: list[str] = []
    preflight = read_preflight(evidence_path, failures)
    route = preflight.get("route") or {}
    docs = route.get("docs") or []
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    if not docs:
        print("FAIL: preflight route has no docs to read", file=sys.stderr)
        return 1

    output_arg = args.receipt_output or args.output
    output_path = output_arg.resolve() if output_arg else receipt_path_for_evidence(evidence_path)
    try:
        receipt = build_route_doc_receipt(
            playbook_root=playbook_root,
            project=project,
            evidence_path=evidence_path,
            route=route,
        )
    except OSError as error:
        print(f"FAIL: unable to read routed docs: {error}", file=sys.stderr)
        return 1

    write_json(output_path, receipt)
    print(f"SUCCESS docs-read")
    print(f"- receipt: {output_path}")
    print(f"- routed docs read: {receipt['doc_count']}")
    print(f"- route fingerprint: {receipt['route_fingerprint']}")
    for doc in receipt["docs"][:8]:
        print(f"- {doc['path']} ({doc['size_bytes']} bytes)")
    if len(receipt["docs"]) > 8:
        print(f"- ... {len(receipt['docs']) - 8} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
