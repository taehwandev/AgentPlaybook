from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from support.permission_entries import (
    claude_legacy_permission_entries,
    codex_legacy_prefix_rule_entries,
    codex_prefix_rule_entries,
)
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
from support.graphify_contract import PLATFORM_INTEGRATION_PATHS
from support.graphify_inspection import (
    inspect_project_graph_inputs,
    inspect_project_graph_state,
)
from support.graphify_document_links import repair_project_document_links
from support.graphify_tracking import install_tracking_policies
from support import setup_agent_hooks_impl
from support.setup_agent_hooks_impl import (
    _should_configure_global_graphify,
    configure_external_project,
    ensure_local_claude_excluded,
)
from support.stable_launcher import ensure_stable_launcher, stable_launcher_path, stable_root_pointer_path


class SetupAgentHooksTests(unittest.TestCase):
    def test_codex_only_setup_skips_unrelated_global_graphify(self) -> None:
        with (
            patch.object(
                sys,
                "argv",
                ["setup-agent-hooks.py", "--check", "--runtime", "codex"],
            ),
            patch.object(setup_agent_hooks_impl, "_has_codex", return_value=True),
            patch.object(
                setup_agent_hooks_impl,
                "ensure_stable_launcher",
                return_value=[],
            ) as ensure_launcher,
            patch.object(setup_agent_hooks_impl, "configure_codex", return_value=[]),
            patch.object(
                setup_agent_hooks_impl.shutil,
                "which",
                return_value="/tmp/graphify",
            ),
            patch.object(
                setup_agent_hooks_impl,
                "configure_global_graphify",
            ) as configure_global,
            patch.object(setup_agent_hooks_impl, "configure_target_projects", return_value=[]),
        ):
            setup_agent_hooks_impl.main()

        configure_global.assert_not_called()
        ensure_launcher.assert_called_once_with(ROOT, True)

    def test_agy_only_setup_installs_stable_launcher(self) -> None:
        with (
            patch.object(
                sys,
                "argv",
                ["setup-agent-hooks.py", "--runtime", "agy"],
            ),
            patch.object(setup_agent_hooks_impl, "_has_agy", return_value=True),
            patch.object(
                setup_agent_hooks_impl,
                "ensure_stable_launcher",
                return_value=[],
            ) as ensure_launcher,
            patch.object(setup_agent_hooks_impl, "configure_agy", return_value=[]),
            patch.object(setup_agent_hooks_impl, "configure_global_graphify", return_value=[]),
            patch.object(setup_agent_hooks_impl, "configure_target_projects", return_value=[]),
        ):
            setup_agent_hooks_impl.main()

        ensure_launcher.assert_called_once_with(ROOT, False)

    def test_global_graphify_stays_enabled_outside_codex_only_setup(self) -> None:
        self.assertFalse(_should_configure_global_graphify({"codex"}))
        self.assertTrue(_should_configure_global_graphify(set()))
        self.assertTrue(_should_configure_global_graphify({"claude"}))
        self.assertTrue(_should_configure_global_graphify({"codex", "claude"}))

    def test_graphify_readiness_rejects_unregistered_json_integration_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            hooks = project / ".codex" / "hooks.json"
            hooks.parent.mkdir(parents=True)
            hooks.write_text('{"graphify": true}', encoding="utf-8")
            integration_paths = {
                **PLATFORM_INTEGRATION_PATHS,
                "codex": (Path(".codex/hooks.json"),),
            }

            with patch(
                "support.graphify_inspection.PLATFORM_INTEGRATION_PATHS",
                integration_paths,
            ):
                readiness = inspect_target_graphify(project, ["codex"])

        self.assertIn(str(hooks), readiness["missing_integrations"])
        self.assertNotIn(str(hooks), readiness["invalid_runtime_integration_links"])

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
            graph.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "id": "src_main",
                                "file_type": "code",
                                "source_file": "src/main.py",
                            }
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
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
        self.assertFalse(target_after["ready"])
        self.assertFalse(target_after["graph_fresh"])
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
        self.assertIn("--repair-input-policy", result.stdout)
        self.assertIn("--repair-document-links", result.stdout)

    def test_target_graphify_readiness_accepts_ast_graph_without_document_code_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            source = project / "src" / "main.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/main.py"], cwd=project, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=AgentPlaybook", "-c",
                    "user.email=agentplaybook@example.invalid", "commit", "-qm", "source",
                ],
                cwd=project,
                check=True,
            )
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
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
            guide = project / ".agents" / "wiki" / "guide.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Guide\n", encoding="utf-8")
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text(
                json.dumps(
                    {
                        "built_at_commit": head,
                        "nodes": [
                            {
                                "id": "src_main",
                                "file_type": "code",
                                "source_file": "src/main.py",
                            },
                            {
                                "id": "guide",
                                "file_type": "document",
                                "source_file": ".agents/wiki/guide.md",
                            },
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            (project / "graphify-out" / "manifest.json").write_text(
                json.dumps(
                    {"src/main.py": {"mtime": source.stat().st_mtime}}
                ),
                encoding="utf-8",
            )
            for relative in TRACKING_POLICY_PATHS:
                policy = project / relative
                policy.parent.mkdir(parents=True, exist_ok=True)
                policy.write_text("# policy\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=project, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=AgentPlaybook", "-c",
                    "user.email=agentplaybook@example.invalid", "commit", "-qm", "integration",
                ],
                cwd=project,
                check=True,
            )
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            graph_payload = json.loads(graph.read_text(encoding="utf-8"))
            graph_payload["built_at_commit"] = head
            graph.write_text(json.dumps(graph_payload), encoding="utf-8")
            (project / "graphify-out" / "manifest.json").write_text(
                json.dumps(
                    {
                        "src/main.py": {"mtime": source.stat().st_mtime},
                        "AGENTS.md": {"mtime": agents.stat().st_mtime},
                        ".agents/wiki/guide.md": {"mtime": guide.stat().st_mtime},
                    }
                ),
                encoding="utf-8",
            )

            with patch("support.graphify_inspection.shutil.which", return_value="/tmp/graphify"):
                result = inspect_target_graphify(project, ["codex"])

        self.assertTrue(result["ready"], result)
        self.assertEqual(str(graph), result["graph_path"])
        self.assertEqual(str(canonical), result["canonical_skill_doc"])
        self.assertTrue(result["graph_integrity_ready"])
        self.assertFalse(result["graph_relationship_ready"])

    def test_graphify_skill_matches_ast_only_readiness_policy(self) -> None:
        skill = (
            ROOT / "docs" / "skills" / "graphify-project-integration" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("AST-only graph", skill)
        self.assertIn("does not fail a current", skill)
        self.assertNotIn(
            "When project docs and code both exist, the graph must contain",
            skill,
        )

    def test_graphify_input_policy_preserves_project_agent_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            guides = [
                project / ".agents" / "llm-wiki" / "guide.md",
                project / ".claude" / "skills" / "review" / "SKILL.md",
                project / ".codex" / "skills" / "testing" / "SKILL.md",
            ]
            for guide in guides:
                guide.parent.mkdir(parents=True)
                guide.write_text("# Project guide\n", encoding="utf-8")
            managed = (
                "# agentplaybook-graphify-inputs:start\n"
                ".agentplaybook/\n.agents/\n.claude/\n.codex/\ngraphify-out/\n"
                "# agentplaybook-graphify-inputs:end\n"
            )
            (project / ".graphifyignore").write_text(managed, encoding="utf-8")
            manifest = project / "graphify-out" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        guide.relative_to(project).as_posix(): {
                            "mtime": guide.stat().st_mtime
                        }
                        for guide in guides
                    }
                ),
                encoding="utf-8",
            )

            before = inspect_project_graph_inputs(project)
            guides[0].write_text("# Changed project guide\n", encoding="utf-8")
            stale = inspect_project_graph_inputs(project)
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_payload[guides[0].relative_to(project).as_posix()]["mtime"] = (
                guides[0].stat().st_mtime
            )
            manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
            install_tracking_policies(project)
            after = inspect_project_graph_inputs(project)
            policy = (project / ".graphifyignore").read_text(encoding="utf-8")

        self.assertFalse(before["graph_input_policy_ready"])
        self.assertTrue(before["knowledge_manifest_ready"])
        self.assertEqual(3, before["project_knowledge_file_count"])
        self.assertFalse(stale["knowledge_manifest_ready"])
        self.assertEqual(1, stale["knowledge_manifest_stale_count"])
        self.assertTrue(after["graph_input_policy_ready"])
        self.assertTrue(after["knowledge_manifest_ready"])
        self.assertNotIn("\n.agents/\n", policy)
        self.assertIn(".agents/skills/graphify", policy)
        self.assertIn(".agents/rules/graphify.md", policy)
        self.assertIn(".agents/workflows/graphify.md", policy)
        self.assertIn(".claude/settings.local.json", policy)

    def test_graphify_input_policy_rejects_blanket_runtime_exclusion_before_knowledge_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / ".graphifyignore").write_text(
                ".claude/\n",
                encoding="utf-8",
            )

            state = inspect_project_graph_inputs(project)

        self.assertFalse(state["graph_input_policy_ready"])
        self.assertEqual(
            [".graphifyignore:.claude/"],
            state["blanket_knowledge_input_exclusions"],
        )

    def test_graphify_manifest_uses_content_hash_before_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            guide = project / ".agents" / "wiki" / "guide.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Guide\n", encoding="utf-8")
            manifest = project / "graphify-out" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        ".agents/wiki/guide.md": {
                            "mtime": 1,
                            "semantic_hash": hashlib.md5(guide.read_bytes()).hexdigest(),
                        }
                    }
                ),
                encoding="utf-8",
            )

            state = inspect_project_graph_inputs(project)

        self.assertTrue(state["knowledge_manifest_ready"])
        self.assertEqual(0, state["knowledge_manifest_stale_count"])

    def test_graphify_input_policy_detects_root_gitignore_wildcard_blanket(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / ".gitignore").write_text(
                "**/.agents/**/*\n",
                encoding="utf-8",
            )

            state = inspect_project_graph_inputs(project)

        self.assertFalse(state["graph_input_policy_ready"])
        self.assertEqual(
            [".gitignore:**/.agents/**/*"],
            state["blanket_knowledge_input_exclusions"],
        )

    def test_graphify_managed_input_policy_collapses_duplicate_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            policy = project / ".graphifyignore"
            policy.write_text(
                "# keep\n.claude/\n.codex/**\n"
                "# agentplaybook-graphify-inputs:start\n.agents/\n"
                "# agentplaybook-graphify-inputs:end\n"
                "# agentplaybook-graphify-inputs:start\n.codex/\n"
                "# agentplaybook-graphify-inputs:end\n",
                encoding="utf-8",
            )
            root_ignore = project / ".gitignore"
            root_ignore.write_text(
                ".agents/\n.claude/\n.codex/**\n",
                encoding="utf-8",
            )

            install_tracking_policies(project)
            content = policy.read_text(encoding="utf-8")
            root_content = root_ignore.read_text(encoding="utf-8")

        self.assertEqual(1, content.count("# agentplaybook-graphify-inputs:start"))
        self.assertEqual(1, content.count("# agentplaybook-graphify-inputs:end"))
        self.assertIn("# keep", content)
        self.assertNotIn("\n.agents/\n", content)
        self.assertNotIn("\n.codex/\n", content)
        self.assertNotIn("\n.claude/\n", content)
        self.assertNotIn("\n.codex/**\n", content)
        self.assertNotIn(".agents/", root_content)
        self.assertNotIn(".claude/\n", root_content)
        self.assertNotIn(".codex/**", root_content)
        self.assertIn(".claude/settings.json", root_content)
        self.assertIn(".claude/settings.local.json", root_content)
        self.assertIn(".codex/hooks.json", root_content)

    def test_graph_freshness_ignores_managed_runtime_adapter_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            source = project / "src" / "main.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            deleted = project / "src" / "deleted.py"
            deleted.write_text("VALUE = 0\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "src/main.py", "src/deleted.py"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                [
                    "git", "-c", "user.name=AgentPlaybook", "-c",
                    "user.email=agentplaybook@example.invalid", "commit", "-qm", "initial",
                ],
                cwd=project,
                check=True,
            )
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text(
                json.dumps(
                    {
                        "built_at_commit": head,
                        "nodes": [
                            {
                                "id": "main",
                                "file_type": "code",
                                "source_file": "src/main.py",
                            }
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            (project / "graphify-out" / "manifest.json").write_text(
                json.dumps({"src/main.py": {"mtime": source.stat().st_mtime}}),
                encoding="utf-8",
            )
            adapter = project / ".codex" / "hooks.json"
            adapter.parent.mkdir()
            adapter.write_text('{"graphify": true}', encoding="utf-8")
            nested_evidence = project / "scripts" / ".agentplaybook" / "preflight.json"
            nested_evidence.parent.mkdir(parents=True)
            nested_evidence.write_text('{"runtime": true}', encoding="utf-8")

            adapter_only = inspect_project_graph_state(project, graph)
            extra_source = project / "src" / "extra.py"
            extra_source.write_text("VALUE = 2\n", encoding="utf-8")
            uncovered_source = inspect_project_graph_state(project, graph)
            extra_source.unlink()
            deleted.unlink()
            deleted_source = inspect_project_graph_state(project, graph)

        self.assertTrue(adapter_only["graph_fresh"])
        self.assertEqual(0, adapter_only["graph_source_dirty_count"])
        self.assertFalse(uncovered_source["graph_fresh"])
        self.assertEqual(1, uncovered_source["graph_source_dirty_count"])
        self.assertTrue(deleted_source["graph_fresh"])
        self.assertEqual(0, deleted_source["graph_source_dirty_count"])

    def test_project_graph_state_uses_current_manifest_and_reports_relationship_quality(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            source = project / "src" / "main.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            guide = project / ".agents" / "wiki" / "guide.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Guide\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "src/main.py", ".agents/wiki/guide.md"],
                cwd=project,
                check=True,
            )
            subprocess.run(
                [
                    "git", "-c", "user.name=AgentPlaybook", "-c",
                    "user.email=agentplaybook@example.invalid", "commit", "-qm", "initial",
                ],
                cwd=project,
                check=True,
            )
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text(
                json.dumps(
                    {
                        "built_at_commit": head,
                        "nodes": [
                            {"id": "guide", "file_type": "document", "source_file": ".agents/wiki/guide.md"},
                            {"id": "concept", "file_type": "rationale", "source_file": ".agents/wiki/guide.md"},
                            {"id": "script_mention", "file_type": "code", "source_file": ".agents/wiki/guide.md"},
                            {"id": "main", "file_type": "code", "source_file": "src/main.py"},
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            (project / "graphify-out" / "manifest.json").write_text(
                json.dumps(
                    {
                        "src/main.py": {"mtime": source.stat().st_mtime},
                        ".agents/wiki/guide.md": {"mtime": guide.stat().st_mtime},
                    }
                ),
                encoding="utf-8",
            )

            disconnected = inspect_project_graph_state(project, graph)
            payload = json.loads(graph.read_text(encoding="utf-8"))
            payload["links"] = [
                {"source": "guide", "target": "concept"},
                {"source": "concept", "target": "main"},
            ]
            graph.write_text(json.dumps(payload), encoding="utf-8")
            connected = inspect_project_graph_state(project, graph)
            source.write_text("VALUE = 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/main.py"], cwd=project, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=AgentPlaybook", "-c",
                    "user.email=agentplaybook@example.invalid", "commit", "-qm", "change",
                ],
                cwd=project,
                check=True,
            )
            stale = inspect_project_graph_state(project, graph)
            (project / "graphify-out" / "manifest.json").write_text(
                json.dumps(
                    {
                        "src/main.py": {"mtime": source.stat().st_mtime},
                        ".agents/wiki/guide.md": {"mtime": guide.stat().st_mtime},
                    }
                ),
                encoding="utf-8",
            )
            rebuilt_from_dirty_worktree = inspect_project_graph_state(project, graph)

        self.assertTrue(disconnected["graph_fresh"])
        self.assertFalse(disconnected["graph_relationship_ready"])
        self.assertEqual(1, disconnected["graph_code_node_count"])
        self.assertEqual(0, disconnected["graph_document_code_edge_count"])
        self.assertTrue(connected["graph_relationship_ready"])
        self.assertEqual(0, connected["graph_document_code_edge_count"])
        self.assertEqual(1, connected["graph_document_code_path_node_count"])
        self.assertEqual(2, connected["graph_knowledge_code_path_node_count"])
        self.assertFalse(stale["graph_fresh"])
        self.assertTrue(rebuilt_from_dirty_worktree["graph_fresh"])

    def test_project_graph_integrity_rejects_malformed_and_duplicate_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir(parents=True)
            graph.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "main", "file_type": "code"},
                            {"id": "main", "file_type": "code"},
                            {"label": "missing id", "file_type": "document"},
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )

            state = inspect_project_graph_state(project, graph)

        self.assertFalse(state["graph_integrity_ready"])
        self.assertEqual(1, state["graph_duplicate_node_id_count"])
        self.assertEqual(1, state["graph_malformed_node_count"])

    def test_graphify_document_link_repair_connects_explicit_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            guide = project / ".agents" / "README.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("Use `../src/main.py` for startup.\n", encoding="utf-8")
            source = project / "src" / "main.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir()
            graph.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "id": "agents_readme_guide",
                                "label": "Guide",
                                "file_type": "document",
                                "source_file": ".agents/README.md",
                                "source_location": "L1",
                            },
                            {
                                "id": "src_main",
                                "label": "main.py",
                                "file_type": "code",
                                "source_file": "src/main.py",
                                "source_location": "L1",
                            },
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )

            first = repair_project_document_links(project)
            second = repair_project_document_links(project)
            payload = json.loads(graph.read_text(encoding="utf-8"))

        self.assertTrue(first["ready"])
        self.assertEqual(1, first["document_source_edges"])
        self.assertFalse(second["changed"])
        self.assertEqual(1, len(payload["links"]))
        self.assertEqual("src_main", payload["links"][0]["target"])

    def test_target_graphify_readiness_fails_closed_without_git_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            graph = project / "graphify-out" / "graph.json"
            graph.parent.mkdir(parents=True)
            graph.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "main", "file_type": "code", "source_file": "main.py"}
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )

            state = inspect_project_graph_state(project, graph)

        self.assertFalse(state["graph_fresh"])

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
            settings = project / ".claude" / "settings.json"
            settings.write_text(
                json.dumps(
                    {
                        "permissions": {"allow": ["keep-this-permission"]},
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Read|Glob",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "SPILL_AI_TOOL=claude graphify hook-guard read",
                                        }
                                    ],
                                }
                            ],
                            "PostToolUse": [
                                {
                                    "matcher": "Bash",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": 'bash -lc "graphify hook-guard read"',
                                        }
                                    ],
                                }
                            ],
                            "UserPromptSubmit": [
                                {
                                    "hooks": [
                                        {"type": "command", "command": "keep-this-hook"}
                                    ]
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            _normalize_runtime_integrations(project, ["antigravity", "claude", "codex"])

            self.assertNotIn("graphify", (project / "AGENTS.md").read_text().lower())
            self.assertIn("## Local", (project / "AGENTS.md").read_text())
            self.assertNotIn("graphify", (project / "CLAUDE.md").read_text().lower())
            self.assertFalse(nested.exists())
            self.assertNotIn("hook-guard", settings.read_text(encoding="utf-8"))
            normalized_settings = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(["keep-this-permission"], normalized_settings["permissions"]["allow"])
            self.assertEqual(
                "keep-this-hook",
                normalized_settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"],
            )
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

    def test_gemini_binary_selects_existing_agy_adapter(self) -> None:
        from support.setup_agent_hooks_impl import _has_agy

        with tempfile.TemporaryDirectory() as temp_home:
            def which(command: str) -> str | None:
                return "/tmp/gemini" if command == "gemini" else None

            with (
                patch("support.setup_agent_hooks_impl.Path.home", return_value=Path(temp_home)),
                patch("support.setup_agent_hooks_impl.shutil.which", side_effect=which),
            ):
                self.assertTrue(_has_agy())

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
                self.assertIn('Path.home() / "git" / "AgentPlaybook"', launcher.read_text())
                self.assertIn('"execution-capsule": "agent_execution_capsule.py"', launcher.read_text())
                self.assertIn('"agent-os-status": "agent-os-status.py"', launcher.read_text())
                self.assertIn('"agent-os-watchdog": "agent-os-watchdog.py"', launcher.read_text())
                self.assertIn('"agent-os-maintenance": "agent-os-maintenance.py"', launcher.read_text())
                self.assertIn('"workflow-dispatch": "workflow_dispatch.py"', launcher.read_text())
                self.assertIn('"handoff"', launcher.read_text())
                self.assertTrue(all(result["status"] == "installed" for result in results))

                check = ensure_stable_launcher(ROOT, dry_run=True)

        self.assertTrue(all(result["status"] == "ok" for result in check))

    def test_codex_setup_is_idempotent_in_a_clean_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            with patch.dict(os.environ, {"HOME": temp_home}):
                first = ensure_stable_launcher(ROOT, dry_run=False)
                first += setup_agent_hooks_impl.configure_codex(False, root=ROOT)
                first_snapshot = {
                    path.relative_to(home): path.read_bytes()
                    for path in home.rglob("*")
                    if path.is_file()
                }

                second = ensure_stable_launcher(ROOT, dry_run=False)
                second += setup_agent_hooks_impl.configure_codex(False, root=ROOT)
                second_snapshot = {
                    path.relative_to(home): path.read_bytes()
                    for path in home.rglob("*")
                    if path.is_file()
                }

        self.assertTrue(all(result["status"] in {"installed", "ok"} for result in first))
        self.assertTrue(all(result["status"] == "ok" for result in second))
        self.assertEqual(first_snapshot, second_snapshot)

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
        self.assertIn("Tao Agent OS hook skipped", result.stderr)

    def test_stable_launcher_blocks_by_default_when_alias_is_unsupported(self) -> None:
        # Without the opt-in flag, a misconfigured or misspelled hook alias
        # must not silently exit 0 - required hooks are gated on exit code,
        # so a quiet success here would let callers skip the entire gate
        # system without noticing.
        with tempfile.TemporaryDirectory() as temp_home:
            with patch.dict(os.environ, {"HOME": temp_home}):
                ensure_stable_launcher(ROOT, dry_run=False)
                launcher = stable_launcher_path()
                env = os.environ.copy()
                env.pop("AGENTPLAYBOOK_HOOK_SOFT_FAIL", None)

                result = subprocess.run(
                    [str(launcher), "totally-bogus-alias"],
                    cwd=temp_home,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("unsupported Tao Agent OS script alias", result.stderr)

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
        self.assertNotIn("unsupported Tao Agent OS script alias: start", result.stderr)
        self.assertIn("--request-classified", result.stdout)

    def test_stable_launcher_supports_gate_batch_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            with patch.dict(os.environ, {"HOME": temp_home}):
                ensure_stable_launcher(ROOT, dry_run=False)
                launcher = stable_launcher_path()

                result = subprocess.run(
                    [str(launcher), "gate-batch", "--help"],
                    cwd=str(ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

        self.assertEqual(0, result.returncode)
        self.assertNotIn("unsupported Tao Agent OS script alias: gate-batch", result.stderr)
        self.assertIn("--gate-record", result.stdout)

    def test_stable_launcher_supports_optional_skill_feedback_alias(self) -> None:
        expected = {
            "skill-feedback": "--skill-feedback-outcome",
            "skill-curate": "--skill-feedback-outcome",
            "skill-review": "--skill-review-outcome",
            "skill-maintenance": "--skill-maintenance-outcome",
        }
        for alias, option in expected.items():
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as temp_home:
                with patch.dict(os.environ, {"HOME": temp_home}):
                    ensure_stable_launcher(ROOT, dry_run=False)
                    launcher = stable_launcher_path()

                    result = subprocess.run(
                        [str(launcher), alias, "--help"],
                        cwd=str(ROOT),
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                    )

            self.assertEqual(0, result.returncode)
            self.assertNotIn(f"unsupported Tao Agent OS script alias: {alias}", result.stderr)
            self.assertIn(option, result.stdout)

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

    def test_tracked_claude_settings_remain_machine_portable_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            self._git(project, "init")
            settings = project / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({
                "permissions": {"allow": ["Bash(user-owned-command *)"]}
            }) + "\n")
            self._git(project, "add", ".claude/settings.json")

            first = configure_external_project(
                project,
                ROOT / "scripts",
                dry_run=False,
                spill_available=False,
            )
            first_text = settings.read_text()
            second = configure_external_project(
                project,
                ROOT / "scripts",
                dry_run=False,
                spill_available=False,
            )

            self.assertTrue(all(result["status"] in {"installed", "ok"} for result in first))
            self.assertTrue(all(result["status"] == "ok" for result in second))
            self.assertEqual(first_text, settings.read_text())
            self.assertIn("Bash(user-owned-command *)", first_text)
            self.assertNotIn(str(Path.home()), first_text)
            self.assertNotIn(str(stable_launcher_path()), first_text)

    def test_codex_merge_removes_only_exact_generated_rules_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "default.rules"
            scripts_dir = ROOT / "scripts"
            generated_legacy = next(
                entry
                for entry in codex_legacy_prefix_rule_entries(scripts_dir)
                if "workflow_gate_policy.py" in entry and '"python3"' in entry
            )
            custom_same_script = (
                'prefix_rule(pattern=["python3", "scripts/agent-hook.py", '
                '"custom-action"], decision="allow")'
            )
            custom_shell_rule = (
                'prefix_rule(pattern=["/bin/zsh", "-lc", '
                '"python3 scripts/agent-hook.py custom-action"], decision="allow")'
            )
            target.write_text(
                "\n".join(
                    [
                        generated_legacy,
                        custom_same_script,
                        custom_shell_rule,
                        'prefix_rule(pattern=["custom-tool"], decision="allow")',
                        "",
                    ]
                )
            )

            entries = codex_prefix_rule_entries(scripts_dir)
            cleanup_entries = codex_legacy_prefix_rule_entries(scripts_dir)
            status = merge_codex_prefix_rules(
                target,
                entries,
                dry_run=False,
                cleanup_entries=cleanup_entries,
            )

            text = target.read_text()
            second_status = merge_codex_prefix_rules(
                target,
                entries,
                dry_run=False,
                cleanup_entries=cleanup_entries,
            )
            self.assertEqual("installed", status)
            self.assertEqual("ok", second_status)
            self.assertIn("# agentplaybook-hooks:begin", text)
            self.assertIn(str(ROOT / "scripts" / "agent-preflight.py"), text)
            self.assertNotIn(generated_legacy, text)
            self.assertIn(custom_same_script, text)
            self.assertIn(custom_shell_rule, text)
            self.assertIn('prefix_rule(pattern=["custom-tool"], decision="allow")', text)
            self.assertEqual(text, target.read_text())

    def test_permission_merge_removes_only_exact_generated_entries_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "settings.json"
            generated_legacy = "command(python3 ~/AgentPlaybook/scripts/agent-hook.py)"
            custom_same_script = (
                "command(python3 ~/AgentPlaybook/scripts/agent-hook.py custom-action)"
            )
            spill_custom = (
                "command(node ~/Library/Application\\ Support/Spill/adapters/setup/"
                "spill-token-metering-setup.mjs --label antigravity --stage custom)"
            )
            target.write_text(json.dumps({
                "permissions": {
                    "allow": [
                        "$defaults",
                        generated_legacy,
                        custom_same_script,
                        spill_custom,
                        "command(custom-tool)",
                    ]
                }
            }) + "\n")
            entries = [
                f"command(python3 {ROOT / 'scripts' / 'agent-hook.py'})",
                f"command(python3 {ROOT / 'scripts' / 'agent-hook.py'} *)",
            ]
            cleanup_entries = [
                "$defaults",
                generated_legacy,
            ]

            status = merge_permissions_allow(
                target,
                entries,
                dry_run=False,
                cleanup_entries=cleanup_entries,
            )

            text = target.read_text()
            allow = json.loads(text)["permissions"]["allow"]
            second_status = merge_permissions_allow(
                target,
                entries,
                dry_run=False,
                cleanup_entries=cleanup_entries,
            )
            self.assertEqual("installed", status)
            self.assertEqual("ok", second_status)
            self.assertIn(str(ROOT / "scripts" / "agent-hook.py"), text)
            self.assertNotIn(generated_legacy, text)
            self.assertNotIn("$defaults", text)
            self.assertIn(custom_same_script, allow)
            self.assertIn(spill_custom, allow)
            self.assertIn("command(custom-tool)", allow)
            self.assertEqual(text, target.read_text())

    def _git(self, project: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(project), *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
