from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from support.setup_agent_hooks_impl import ensure_local_claude_excluded


class SetupAgentHooksTests(unittest.TestCase):
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

    def _git(self, project: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(project), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
