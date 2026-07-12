#!/usr/bin/env python3
"""Install or check one canonical Graphify skill across target repositories."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from support.graphify_setup import (
    configure_global_graphify,
    configure_target_graphify,
    graphify_platforms_for_runtimes,
    inspect_global_graphify,
    inspect_target_graphify,
    install_graphify_input_policy,
    repair_project_document_links,
)


DEFAULT_RUNTIMES = {"agy", "claude", "codex"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Install one .agentplaybook Graphify bundle and repo-relative runtime links."
        )
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Target repository path; repeat for parallel multi-project setup.",
    )
    parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Also install one user-level canonical skill under ~/.agentplaybook.",
    )
    parser.add_argument(
        "--runtime",
        action="append",
        choices=("agy", "claude", "codex"),
        default=[],
        help="Intentionally limit runtime entrypoints; default installs all three.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Maximum parallel target projects (default: 4).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Inspect only; do not modify target repositories.",
    )
    parser.add_argument(
        "--repair-input-policy",
        action="store_true",
        help=(
            "Repair the managed Graphify input boundary and narrow legacy root runtime "
            "blankets; do not reinstall skills, links, hooks, or Graphify output."
        ),
    )
    parser.add_argument(
        "--repair-document-links",
        action="store_true",
        help=(
            "Add deterministic graph references for explicit project-relative source "
            "paths cited by project documents; do not run an LLM extraction."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format (default: summary).",
    )
    args = parser.parse_args()

    if not args.project and not args.global_scope:
        parser.error("provide at least one --project or --global")
    if args.repair_input_policy and args.global_scope:
        parser.error("--repair-input-policy supports project targets only")
    if args.repair_document_links and args.global_scope:
        parser.error("--repair-document-links supports project targets only")
    if args.repair_input_policy and args.repair_document_links:
        parser.error("choose only one repair mode per invocation")

    projects = [Path(value).expanduser().resolve() for value in args.project]
    missing = [str(path) for path in projects if not path.is_dir()]
    if missing:
        parser.error("project directory not found: " + ", ".join(missing))
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    platforms = graphify_platforms_for_runtimes(set(args.runtime) or DEFAULT_RUNTIMES)

    def configure(project: Path) -> dict[str, object]:
        document_links: dict[str, object] | None = None
        if args.repair_input_policy:
            changes = [] if args.check else [install_graphify_input_policy(project)]
        elif args.repair_document_links:
            document_links = repair_project_document_links(project, dry_run=args.check)
            changes = [
                {
                    "tool": "graphify",
                    "hook": "graph.repair.document-links",
                    "status": "ok" if document_links["ready"] else "missing",
                    "path": str(document_links["graph_path"]),
                }
            ]
        else:
            changes = configure_target_graphify(project, platforms, dry_run=args.check)
        readiness = inspect_target_graphify(project, platforms)
        return {
            "scope": "project",
            "project": str(project),
            "changes": changes,
            "readiness": readiness,
            "document_links": document_links,
            "success": (
                bool(readiness["graph_input_policy_ready"])
                if args.repair_input_policy
                else (
                    bool(document_links and document_links["ready"])
                    if args.repair_document_links
                    else bool(readiness["ready"])
                )
            ),
        }

    reports: list[dict[str, object]] = []
    if args.global_scope:
        home = Path.home()
        reports.append(
            {
                "scope": "global",
                "project": str(home),
                "changes": configure_global_graphify(home, platforms, dry_run=args.check),
                "readiness": inspect_global_graphify(home, platforms),
            }
        )
    if projects:
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(projects))) as executor:
            reports.extend(executor.map(configure, projects))

    if args.format == "json":
        print(json.dumps({"projects": reports}, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            readiness = report["readiness"]
            if args.repair_input_policy:
                print(
                    f"{'SUCCESS' if report['success'] else 'FAIL'} input-policy "
                    f"{report['project']} blanket-exclusions="
                    f"{len(readiness.get('blanket_knowledge_input_exclusions', []))}"
                )
                continue
            if args.repair_document_links:
                links = report["document_links"] or {}
                print(
                    f"{'SUCCESS' if report['success'] else 'FAIL'} document-links "
                    f"{report['project']} scanned={links.get('document_files_scanned', 0)} "
                    f"paths={links.get('explicit_source_paths_found', 0)} "
                    f"edges={links.get('document_source_edges', 0)}"
                )
                continue
            install_ready = bool(
                readiness["canonical_skill_exists"]
                and not readiness["invalid_runtime_links"]
                and not readiness.get("missing_integrations", [])
                and not readiness.get("missing_tracking_policies", [])
            )
            print(
                f"{'SUCCESS' if install_ready else 'FAIL'} install "
                f"{report['project']} canonical={readiness['canonical_skill_doc']} "
                f"links={len(readiness['runtime_skill_links'])}"
            )
            if report["scope"] == "project":
                print(
                    f"{'SUCCESS' if readiness['ready'] else 'FAIL'} readiness "
                    f"graph={readiness['graph_path']}"
                )
                print(
                    "  graph-checks "
                    f"fresh={str(readiness.get('graph_fresh') is True).lower()} "
                    f"integrity={str(bool(readiness.get('graph_integrity_ready'))).lower()} "
                    f"inputs={str(bool(readiness.get('graph_input_policy_ready') and readiness.get('knowledge_manifest_ready'))).lower()} "
                    f"relationships={str(bool(readiness.get('graph_relationship_ready'))).lower()}"
                )
                print(
                    "  graph-counts "
                    f"knowledge={readiness.get('project_knowledge_file_count', 0)} "
                    f"manifest={readiness.get('knowledge_manifest_file_count', 0)} "
                    f"missing={readiness.get('knowledge_manifest_missing_count', 0)} "
                    f"stale={readiness.get('knowledge_manifest_stale_count', 0)} "
                    f"knowledge-path-nodes={readiness.get('graph_knowledge_code_path_node_count', 0)}"
                )
                if readiness.get("git_repository"):
                    print(
                        f"{'SUCCESS' if readiness['commit_ready'] else 'FAIL'} commit-boundary "
                        f"legacy-runtime-files={len(readiness['tracked_runtime_skill_copies'])} "
                        f"canonical-untracked={len(readiness['canonical_untracked_files'])} "
                        f"link-index-issues={len(readiness['runtime_link_index_issues']) + len(readiness['adapter_link_index_issues'])} "
                        f"unstaged={len(readiness['unstaged_commit_assets'])} "
                        f"ignored={len(readiness['ignored_commit_assets'])}"
                    )
            else:
                print(f"{'SUCCESS' if readiness['ready'] else 'FAIL'} global readiness")
    if any(
        not report.get("success", report["readiness"]["ready"])
        or (
            not args.repair_input_policy
            and not args.repair_document_links
            and report["readiness"].get("commit_ready") is False
        )
        for report in reports
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
