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
from support.setup_agent_hooks_impl import ensure_local_claude_excluded
from support.stable_launcher import ensure_stable_launcher, stable_launcher_path, stable_root_pointer_path


class SetupAgentHooksTests(unittest.TestCase):
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
