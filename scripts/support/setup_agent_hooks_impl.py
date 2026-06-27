"""Runtime hook setup entry flow for AgentPlaybook."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from support.agy_setup import configure_agy
from support.claude_setup import configure_claude
from support.permission_entries import claude_project_permission_entries, codex_prefix_rule_entries
from support.project_type_detection import detect_project_permissions
from support.setup_config_files import merge_codex_prefix_rules, merge_permissions_allow, print_results

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
WORKFLOW_SCRIPT = SCRIPTS_DIR / "workflow.py"
DEFAULT_SPILL_SETUP_HELPER = (
    Path.home()
    / "Library/Application Support/Spill/adapters/setup/spill-token-metering-setup.mjs"
)
DEFAULT_GITHUB_DIR = Path.home() / "GitHub"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure AI runtime hooks and permissions for AgentPlaybook."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any required hook is missing.",
    )
    parser.add_argument(
        "--target",
        metavar="PATH",
        help="Also install project-level permissions for this external project directory.",
    )
    parser.add_argument(
        "--github-projects",
        action="store_true",
        help="Also install project-level permissions for all ~/GitHub/* projects.",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or args.check
    spill_available = _has_spill_setup_helper()
    results: list[dict] = []

    if _has_claude():
        results += configure_claude(
            dry_run,
            root=ROOT,
            scripts_dir=SCRIPTS_DIR,
            workflow_script=WORKFLOW_SCRIPT,
            spill_available=spill_available,
        )

    if _has_codex():
        results += configure_codex(dry_run)

    if _has_agy():
        results += configure_agy(
            dry_run,
            root=ROOT,
            scripts_dir=SCRIPTS_DIR,
            spill_available=spill_available,
        )

    # External project installs
    target_paths: list[Path] = []
    if args.target:
        target_paths.append(Path(args.target).expanduser().resolve())
    if args.github_projects:
        target_paths += _find_github_projects()

    for project_path in target_paths:
        results += configure_external_project(
            project_path, SCRIPTS_DIR, dry_run, spill_available=spill_available
        )

    print_results(results, dry_run)

    if args.check:
        missing = [r for r in results if r["status"] == "missing"]
        if missing:
            print(
                "\nRun `python3 scripts/setup-agent-hooks.py` to install missing hooks or permissions.",
                file=sys.stderr,
            )
            sys.exit(1)


def _has_claude() -> bool:
    return (Path.home() / ".claude").is_dir() or bool(shutil.which("claude"))


def _has_codex() -> bool:
    return (Path.home() / ".codex").is_dir() or bool(shutil.which("codex"))


def _has_agy() -> bool:
    gemini_home = Path.home() / ".gemini"
    return (
        gemini_home.is_dir()
        or bool(shutil.which("agy"))
        or bool(shutil.which("antigravity"))
        or bool(shutil.which("gemini"))
    )


def _spill_setup_helper_path() -> Path:
    override = os.environ.get("AGENTPLAYBOOK_SPILL_HELPER_PATH", "")
    return Path(override) if override else DEFAULT_SPILL_SETUP_HELPER


def _has_spill_setup_helper() -> bool:
    return _spill_setup_helper_path().is_file()


def configure_codex(dry_run: bool) -> list[dict]:
    target = Path.home() / ".codex" / "rules" / "default.rules"
    status = merge_codex_prefix_rules(target, codex_prefix_rule_entries(SCRIPTS_DIR), dry_run)
    return [{"tool": "codex", "hook": "rules.AgentPlaybookPython", "status": status, "path": str(target)}]


def configure_external_project(
    project_path: Path,
    scripts_dir: Path,
    dry_run: bool,
    *,
    spill_available: bool = True,
) -> list[dict]:
    """Install AgentPlaybook + project-type-specific permissions for an external project.

    Combines the standard project-level entries (AgentPlaybook scripts, git -C
    wildcards) with entries detected from the project's build toolchain (Swift,
    Node.js, Gradle, Rust, Go, Python) so that any parameter combination is
    covered after a single install run.
    """
    target = project_path / ".claude" / "settings.json"
    entries = claude_project_permission_entries(scripts_dir, spill_available=spill_available)
    entries += detect_project_permissions(project_path)
    status = merge_permissions_allow(target, entries, dry_run)
    hook_label = f"permissions.project.{project_path.name}"
    exclude_status = ensure_local_claude_excluded(project_path, dry_run)
    return [
        {"tool": "claude", "hook": hook_label, "status": status, "path": str(target)},
        {
            "tool": "git",
            "hook": f"exclude.claude.{project_path.name}",
            "status": exclude_status,
            "path": str(project_path / ".git" / "info" / "exclude"),
        },
    ]


def ensure_local_claude_excluded(project_path: Path, dry_run: bool) -> str:
    """Keep generated project Claude permissions local unless already tracked."""
    git_dir = project_path / ".git"
    if not git_dir.is_dir():
        return "ok"
    if _git_path_matches(project_path, ["ls-files", "--error-unmatch", ".claude/settings.json"]):
        return "ok"
    if _git_path_matches(project_path, ["check-ignore", "-q", ".claude/settings.json"]):
        return "ok"

    exclude = git_dir / "info" / "exclude"
    text = exclude.read_text() if exclude.exists() else ""
    lines = text.splitlines()
    if ".claude/" in lines or ".claude/settings.json" in lines:
        return "ok"
    if dry_run:
        return "missing"

    exclude.parent.mkdir(parents=True, exist_ok=True)
    if text and not text.endswith("\n"):
        text += "\n"
    exclude.write_text(text + ".claude/\n")
    return "installed"


def _git_path_matches(project_path: Path, args: list[str]) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project_path), *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _find_github_projects() -> list[Path]:
    if not DEFAULT_GITHUB_DIR.exists():
        return []
    return sorted(
        p for p in DEFAULT_GITHUB_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )
