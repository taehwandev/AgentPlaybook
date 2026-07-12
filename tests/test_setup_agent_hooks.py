from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from support.permission_entries import codex_prefix_rule_entries
from support.setup_config_files import merge_codex_prefix_rules, merge_permissions_allow
from support.graphify_setup import (
    CANONICAL_SKILL_PATH,
    GLOBAL_PLATFORM_SKILL_DIRS,
    PLATFORM_SKILL_DIRS,
    TRACKING_POLICY_PATHS,
    _normalize_runtime_integrations,
    configure_target_graphify,
    graphify_platforms_for_runtimes,
    inspect_global_graphify,
    inspect_target_graphify,
)
from support.graphify_git_tracking import inspect_graphify_git_tracking
from support.setup_agent_hooks_impl import ensure_local_claude_excluded
from support.stable_launcher import ensure_stable_launcher, stable_launcher_path, stable_root_pointer_path


class SetupAgentHooksTests(unittest.TestCase):
    def test_git_tracking_rejects_legacy_runtime_files_until_link_is_staged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            canonical = project / CANONICAL_SKILL_PATH
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# canonical graphify\n", encoding="utf-8")
            runtime_skill = project / PLATFORM_SKILL_DIRS["codex"]
            runtime_skill.mkdir(parents=True)
            (runtime_skill / "SKILL.md").write_text(
                "# legacy copy\n", encoding="utf-8"
            )
            (project / ".codex" / "hooks.json").write_text(
                '{"graphify": true}', encoding="utf-8"
            )
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir(parents=True)
            graph.write_text("{}", encoding="utf-8")
            for relative in TRACKING_POLICY_PATHS:
                policy = project / relative
                policy.parent.mkdir(parents=True, exist_ok=True)
                policy.write_text("# policy\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".agentplaybook", ".codex", *map(str, TRACKING_POLICY_PATHS)],
                cwd=project,
                check=True,
            )
            for child in runtime_skill.iterdir():
                child.unlink()
            runtime_skill.rmdir()
            runtime_skill.symlink_to(
                "../../.agentplaybook/skills/graphify", target_is_directory=True
            )

            before = inspect_graphify_git_tracking(project, ["codex"])
            self.assertFalse(before["commit_ready"])
            self.assertEqual(
                [".codex/skills/graphify/SKILL.md"],
                before["tracked_runtime_skill_copies"],
            )
            self.assertEqual(
                [".codex/skills/graphify"], before["runtime_link_index_issues"]
            )
            with patch(
                "support.graphify_inspection.shutil.which",
                return_value="/tmp/graphify",
            ):
                target_before = inspect_target_graphify(project, ["codex"])
                before_results = configure_target_graphify(
                    project, ["codex"], dry_run=True
                )
            self.assertTrue(target_before["runtime_ready"])
            self.assertFalse(target_before["ready"])
            self.assertTrue(
                any(
                    result["hook"] == "tracking.commit_boundary"
                    and result["status"] == "missing"
                    for result in before_results
                )
            )

            subprocess.run(
                ["git", "add", "-A", ".agentplaybook", ".codex"],
                cwd=project,
                check=True,
            )
            after = inspect_graphify_git_tracking(project, ["codex"])
            with patch(
                "support.graphify_inspection.shutil.which",
                return_value="/tmp/graphify",
            ):
                target_after = inspect_target_graphify(project, ["codex"])
                after_results = configure_target_graphify(
                    project, ["codex"], dry_run=True
                )
            index_text = subprocess.run(
                ["git", "ls-files", "--stage", "--", ".codex/skills/graphify"],
                cwd=project,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout

            canonical.write_text("# staged content changed\n", encoding="utf-8")
            dirty = inspect_graphify_git_tracking(project, ["codex"])
            self.assertFalse(dirty["commit_ready"])
            self.assertEqual(
                [".agentplaybook/skills/graphify/SKILL.md"],
                dirty["unstaged_commit_assets"],
            )
            subprocess.run(
                ["git", "add", ".agentplaybook/skills/graphify/SKILL.md"],
                cwd=project,
                check=True,
            )
            restaged = inspect_graphify_git_tracking(project, ["codex"])

        self.assertTrue(after["commit_ready"])
        self.assertTrue(target_after["ready"])
        self.assertTrue(
            any(
                result["hook"] == "tracking.commit_boundary"
                and result["status"] == "ok"
                for result in after_results
            )
        )
        self.assertEqual([], after["tracked_runtime_skill_copies"])
        self.assertEqual([], after["runtime_link_index_issues"])
        self.assertEqual([], after["policy_untracked_files"])
        self.assertEqual([], after["unstaged_commit_assets"])
        self.assertEqual([], after["ignored_commit_assets"])
        self.assertTrue(index_text.startswith("120000 "))
        self.assertTrue(index_text.endswith("\t.codex/skills/graphify\n"))
        self.assertNotIn(".codex/skills/graphify/SKILL.md", index_text)
        self.assertTrue(restaged["commit_ready"])

    def test_global_graphify_readiness_requires_one_canonical_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            canonical = home / CANONICAL_SKILL_PATH
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# canonical graphify\n")
            for platform in ("agents", "antigravity", "claude", "codex"):
                link = home / GLOBAL_PLATFORM_SKILL_DIRS[platform]
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(
                    os.path.relpath(canonical.parent, start=link.parent),
                    target_is_directory=True,
                )

            with patch("support.graphify_inspection.shutil.which", return_value="/tmp/graphify"):
                readiness = inspect_global_graphify(
                    home, ["antigravity", "claude", "codex"]
                )

        self.assertTrue(readiness["ready"])
        self.assertEqual(4, len(readiness["runtime_skill_links"]))

    def test_project_graphify_setup_cli_defaults_to_agent_agnostic_install(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "setup-project-graphify.py"), "--help"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("installs all three", result.stdout)
        self.assertIn("--jobs", result.stdout)

    def test_target_graphify_readiness_requires_canonical_skill_links_integration_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            canonical = project / CANONICAL_SKILL_PATH
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# graphify\n", encoding="utf-8")
            skill_link = project / PLATFORM_SKILL_DIRS["codex"]
            skill_link.parent.mkdir(parents=True)
            skill_link.symlink_to("../../.agentplaybook/skills/graphify", target_is_directory=True)
            hooks = project / ".codex" / "hooks.json"
            hooks.write_text('{"graphify": true}', encoding="utf-8")
            agents = project / "AGENTS.md"
            agents.write_text("## graphify\n", encoding="utf-8")
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text("{}", encoding="utf-8")
            for relative in TRACKING_POLICY_PATHS:
                policy = project / relative
                policy.parent.mkdir(parents=True, exist_ok=True)
                policy.write_text("# policy\n", encoding="utf-8")

            with patch("support.graphify_inspection.shutil.which", return_value="/tmp/graphify"):
                result = inspect_target_graphify(project, ["codex"])

        self.assertTrue(result["ready"])
        self.assertEqual(str(graph), result["graph_path"])
        self.assertEqual(str(canonical), result["canonical_skill_doc"])

    def test_target_graphify_readiness_rejects_duplicated_runtime_skill_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            canonical = project / CANONICAL_SKILL_PATH
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# canonical graphify\n", encoding="utf-8")
            copied = project / PLATFORM_SKILL_DIRS["codex"] / "SKILL.md"
            copied.parent.mkdir(parents=True)
            copied.write_text("# copied graphify\n", encoding="utf-8")
            (project / ".codex" / "hooks.json").write_text('{"graphify": true}')
            (project / "AGENTS.md").write_text("## graphify\n")
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text("{}")
            for relative in TRACKING_POLICY_PATHS:
                policy = project / relative
                policy.parent.mkdir(parents=True, exist_ok=True)
                policy.write_text("# policy\n")

            with patch("support.graphify_inspection.shutil.which", return_value="/tmp/graphify"):
                result = inspect_target_graphify(project, ["codex"])

        self.assertFalse(result["ready"])
        self.assertEqual([str(project / PLATFORM_SKILL_DIRS["codex"])], result["invalid_runtime_links"])

    def test_runtime_integration_removes_prose_copies_and_links_agy_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            canonical = project / CANONICAL_SKILL_PATH
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# canonical graphify\n")
            (project / "AGENTS.md").write_text(
                "# Project\n\n## graphify\n\nCopied rules.\n\n"
                "## Project Scope and Ownership\n\nGraphify-out copied policy.\n\n"
                "## Local\n\nKeep me.\n"
            )
            (project / "CLAUDE.md").write_text(
                "# Claude\n\n"
                "This file only adds the project-scoped Graphify routing note for Claude.\n\n"
                "## graphify\n\nCopied rules.\n"
            )
            nested = project / ".claude" / "CLAUDE.md"
            nested.parent.mkdir(parents=True)
            nested.write_text(
                "---\nkeyflow_id: generated\nstatus: review\ntype: ai-generated\n---\n\n"
                "# graphify\nCopied registration.\n"
            )

            _normalize_runtime_integrations(project, ["antigravity", "claude", "codex"])

            self.assertNotIn("graphify", (project / "AGENTS.md").read_text().lower())
            self.assertIn("## Local", (project / "AGENTS.md").read_text())
            self.assertNotIn("graphify", (project / "CLAUDE.md").read_text().lower())
            self.assertFalse(nested.exists())
            for relative in (
                Path(".agents/rules/graphify.md"),
                Path(".agents/workflows/graphify.md"),
            ):
                link = project / relative
                self.assertTrue(link.is_symlink())
                self.assertTrue(link.resolve().is_file())
                self.assertIn(
                    str((project / ".agentplaybook/skills/graphify/runtime/antigravity").resolve()),
                    str(link.resolve()),
                )

    def test_target_graphify_dry_run_reports_missing_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)

            with patch("support.graphify_configuration.shutil.which", return_value="/tmp/graphify"):
                results = configure_target_graphify(project, ["codex"], dry_run=True)

            self.assertTrue(any(result["status"] == "missing" for result in results))
            self.assertFalse((project / "graphify-out").exists())

    def test_target_graphify_install_never_runs_initial_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)

            with patch("support.graphify_configuration.shutil.which", return_value="/tmp/graphify"), patch(
                "support.graphify_configuration.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0),
            ) as run, patch(
                "support.graphify_configuration.install_canonical_skill",
                return_value=True,
            ), patch("support.graphify_configuration.replace_runtime_skill_with_link"):
                configure_target_graphify(project, ["codex"], dry_run=False)

        commands = [call.args[0] for call in run.call_args_list]
        install_command = [
            "/tmp/graphify",
            "install",
            "--project",
            "--platform",
            "codex",
        ]
        self.assertIn(install_command, commands)
        self.assertNotIn("extract", install_command)

    def test_graphify_runtime_mapping_uses_project_platforms(self) -> None:
        self.assertEqual(
            ["antigravity", "claude", "codex"],
            graphify_platforms_for_runtimes({"agy", "claude", "codex"}),
        )

    def test_stable_launcher_records_current_root_under_user_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            with patch.dict(os.environ, {"HOME": temp_home}):
                results = ensure_stable_launcher(ROOT, dry_run=False)
                launcher = stable_launcher_path()
                pointer = stable_root_pointer_path()

                self.assertTrue(launcher.exists())
                self.assertTrue(os.access(launcher, os.X_OK))
                self.assertEqual(f"{ROOT.resolve()}\n", pointer.read_text())
                self.assertIn("scripts/workflow.py", launcher.read_text())
                self.assertTrue(all(result["status"] == "installed" for result in results))

                check = ensure_stable_launcher(ROOT, dry_run=True)

        self.assertTrue(all(result["status"] == "ok" for result in check))

    def test_stable_launcher_soft_fails_when_root_pointer_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            with patch.dict(os.environ, {"HOME": temp_home}):
                ensure_stable_launcher(ROOT, dry_run=False)
                stable_root_pointer_path().write_text("/missing/AgentPlaybook\n")
                launcher = stable_launcher_path()
                env = os.environ.copy()
                env["AGENTPLAYBOOK_HOOK_SOFT_FAIL"] = "1"

                result = subprocess.run(
                    [str(launcher), "workflow", "validate"],
                    cwd=temp_home,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

        self.assertEqual(0, result.returncode)
        self.assertIn("AgentPlaybook hook skipped", result.stderr)

    def test_stable_launcher_supports_agent_hook_subcommand_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            with patch.dict(os.environ, {"HOME": temp_home}):
                ensure_stable_launcher(ROOT, dry_run=False)
                launcher = stable_launcher_path()

                result = subprocess.run(
                    [str(launcher), "start", "--help"],
                    cwd=str(ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

        self.assertEqual(0, result.returncode)
        self.assertNotIn("unsupported AgentPlaybook script alias: start", result.stderr)
        self.assertIn("--request-classified", result.stdout)

    def test_external_project_claude_settings_are_excluded_locally(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            self._git(project, "init")

            status = ensure_local_claude_excluded(project, dry_run=False)

            self.assertEqual("installed", status)
            self.assertIn(".claude/", (project / ".git" / "info" / "exclude").read_text())

    def test_dry_run_reports_missing_without_writing_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            self._git(project, "init")

            status = ensure_local_claude_excluded(project, dry_run=True)

            self.assertEqual("missing", status)
            self.assertNotIn(".claude/", (project / ".git" / "info" / "exclude").read_text())

    def test_tracked_claude_settings_are_not_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            self._git(project, "init")
            settings = project / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text("{}\n")
            self._git(project, "add", ".claude/settings.json")

            status = ensure_local_claude_excluded(project, dry_run=False)

            self.assertEqual("ok", status)
            self.assertNotIn(".claude/", (project / ".git" / "info" / "exclude").read_text())

    def test_codex_merge_removes_argument_specific_agentplaybook_prefix_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "default.rules"
            target.write_text(
                "\n".join(
                    [
                        'prefix_rule(pattern=["python3", "$HOME/Documents/KeyFlowVault/AgentPlaybook/scripts/agent-preflight.py", "--project", "$(pwd)"], decision="allow")',
                        'prefix_rule(pattern=["python3", "scripts/agent-hook.py", "docs-read", "--project", "$(pwd)"], decision="allow")',
                        'prefix_rule(pattern=["/bin/zsh", "-lc", "python3 \\"$HOME/Documents/KeyFlowVault/AgentPlaybook/scripts/agent-hook.py\\" finish --project \\"$(pwd)\\" --gate \\"verify=done\\""], decision="allow")',
                        "",
                    ]
                )
            )

            status = merge_codex_prefix_rules(
                target,
                codex_prefix_rule_entries(ROOT / "scripts"),
                dry_run=False,
            )

            text = target.read_text()
            self.assertEqual("installed", status)
            self.assertIn("# agentplaybook-hooks:begin", text)
            self.assertIn(str(ROOT / "scripts" / "agent-preflight.py"), text)
            self.assertNotIn("$HOME", text)
            self.assertNotIn("$(pwd)", text)
            self.assertNotIn("--project", text)
            self.assertNotIn("--gate", text)

    def test_permission_merge_removes_argument_specific_agentplaybook_allow_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "settings.json"
            target.write_text(
                """{
  "permissions": {
    "allow": [
      "command(python3 ~/Documents/KeyFlowVault/AgentPlaybook/scripts/agent-hook.py finish --project \\"$(pwd)\\" --gate \\"verify=done\\")",
      "command(python3 ~/Documents/KeyFlowVault/AgentPlaybook/scripts/agent-hook\\\\.py review --project \\"$(pwd)\\")",
      "command(python3 /Users/example/Other/scripts/custom.py --project keep)"
    ]
  }
}
"""
            )
            entries = [
                f"command(python3 {ROOT / 'scripts' / 'agent-hook.py'})",
                f"command(python3 {ROOT / 'scripts' / 'agent-hook.py'} *)",
            ]
            cleanup_entries = [
                "command(python3 ~/Documents/KeyFlowVault/AgentPlaybook/scripts/agent-hook.py)",
            ]

            status = merge_permissions_allow(
                target,
                entries,
                dry_run=False,
                cleanup_entries=cleanup_entries,
            )

            text = target.read_text()
            self.assertEqual("installed", status)
            self.assertIn(str(ROOT / "scripts" / "agent-hook.py"), text)
            self.assertIn("Other/scripts/custom.py", text)
            self.assertNotIn("$(pwd)", text)
            self.assertNotIn("--gate", text)
            self.assertNotIn("agent-hook\\.py", text)

    def _git(self, project: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(project), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
