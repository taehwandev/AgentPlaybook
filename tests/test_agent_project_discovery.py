from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_project_discovery import build_entry_manifest, discover_projects, find_project_root


class AgentProjectDiscoveryTests(unittest.TestCase):
    def test_find_project_root_uses_nearest_agent_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            nested = project / "src" / "feature"
            nested.mkdir(parents=True)
            (project / "AGENTS.md").write_text("# instructions\n", encoding="utf-8")

            self.assertEqual(project.resolve(), find_project_root(nested))

    def test_cwd_project_is_selected_with_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "app"
            (project / ".agents").mkdir(parents=True)
            (project / "AGENTS.md").write_text("# agent\n", encoding="utf-8")
            (project / ".agents" / "README.md").write_text("# shared\n", encoding="utf-8")
            cwd = project / "src"
            cwd.mkdir()

            result = discover_projects("fix this app", cwd, search_roots=[], max_depth=0, include_default_search_roots=False)

            self.assertEqual("selected", result.status)
            self.assertEqual(project.resolve(), result.selected.path)
            self.assertIn("AGENTS.md", result.selected.instruction_files)
            self.assertIn(".agents/README.md", result.selected.instruction_files)

    def test_explicit_request_path_beats_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            current = base / "current"
            target = base / "target"
            current.mkdir()
            target.mkdir()
            (current / "AGENTS.md").write_text("# current\n", encoding="utf-8")
            (current / ".git").mkdir()
            (target / "CLAUDE.md").write_text("# target\n", encoding="utf-8")

            result = discover_projects(
                f"apply this to {target}",
                current,
                search_roots=[],
                max_depth=0,
                include_default_search_roots=False,
            )

            self.assertEqual("selected", result.status)
            self.assertEqual(target.resolve(), result.selected.path)
            self.assertIn("explicit path in request", result.selected.reasons)

    def test_registry_alias_beats_current_git_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            current = base / "current"
            target = base / "target"
            current.mkdir()
            target.mkdir()
            (current / "AGENTS.md").write_text("# current\n", encoding="utf-8")
            (current / ".git").mkdir()
            (target / "AGENTS.md").write_text("# target\n", encoding="utf-8")
            registry = base / "projects.json"
            registry.write_text(
                json.dumps({"projects": [{"root": str(target), "aliases": ["target-app"]}]}),
                encoding="utf-8",
            )

            result = discover_projects(
                "work on target-app",
                current,
                registry_path=registry,
                search_roots=[],
                max_depth=0,
                include_default_search_roots=False,
            )

            self.assertEqual("selected", result.status)
            self.assertEqual(target.resolve(), result.selected.path)

    def test_registry_alias_selects_project_from_home_like_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            project = base / "nunu-os-main"
            project.mkdir()
            (project / "AGENTS.md").write_text("# agent\n", encoding="utf-8")
            registry = base / "projects.json"
            registry.write_text(
                json.dumps({"projects": [{"root": str(project), "aliases": ["nunu"]}]}),
                encoding="utf-8",
            )

            result = discover_projects(
                "work on nunu",
                base,
                registry_path=registry,
                search_roots=[],
                max_depth=0,
                include_default_search_roots=False,
            )

            self.assertEqual("selected", result.status)
            self.assertEqual(project.resolve(), result.selected.path)
            self.assertIn("nunu", result.selected.aliases)

    def test_search_roots_report_ambiguous_when_projects_tie(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            one = base / "one"
            two = base / "two"
            one.mkdir()
            two.mkdir()
            (one / "AGENTS.md").write_text("# one\n", encoding="utf-8")
            (two / "AGENTS.md").write_text("# two\n", encoding="utf-8")
            outside = base / "outside"
            outside.mkdir()

            result = discover_projects(
                "update the app",
                outside,
                search_roots=[base],
                max_depth=1,
                include_default_search_roots=False,
            )

            self.assertEqual("ambiguous", result.status)
            self.assertEqual([one.resolve(), two.resolve()], [candidate.path for candidate in result.candidates[:2]])

    def test_directory_scanning_requires_explicit_search_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            project = base / "app"
            outside = base / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "AGENTS.md").write_text("# app\n", encoding="utf-8")

            result = discover_projects("update app", outside, max_depth=1)

            self.assertEqual("not_found", result.status)

    def test_entry_manifest_tells_runtime_to_read_project_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "app"
            project.mkdir()
            (project / "AGENTS.md").write_text("# agent\n", encoding="utf-8")

            manifest = build_entry_manifest(
                "update app",
                project,
                runtime="codex",
                command="feature",
                include_default_search_roots=False,
            )

            self.assertEqual("selected", manifest["status"])
            self.assertEqual("codex", manifest["runtime"])
            self.assertIn("workflow.py", manifest["workflow_command"])
            self.assertIn("AGENTS.md", manifest["selected_project"]["instruction_files"])
            self.assertIn("Open the selected project's runtime instruction files before project work.", manifest["next_steps"])


if __name__ == "__main__":
    unittest.main()
