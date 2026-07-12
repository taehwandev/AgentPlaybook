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
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format (default: summary).",
    )
    args = parser.parse_args()

    if not args.project and not args.global_scope:
        parser.error("provide at least one --project or --global")

    projects = [Path(value).expanduser().resolve() for value in args.project]
    missing = [str(path) for path in projects if not path.is_dir()]
    if missing:
        parser.error("project directory not found: " + ", ".join(missing))
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    platforms = graphify_platforms_for_runtimes(set(args.runtime) or DEFAULT_RUNTIMES)

    def configure(project: Path) -> dict[str, object]:
        changes = configure_target_graphify(project, platforms, dry_run=args.check)
        return {
            "scope": "project",
            "project": str(project),
            "changes": changes,
            "readiness": inspect_target_graphify(project, platforms),
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
        not report["readiness"]["ready"]
        or report["readiness"].get("commit_ready") is False
        for report in reports
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
