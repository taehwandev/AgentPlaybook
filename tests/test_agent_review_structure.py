from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_review_structure import changed_source_paths, check_file_size, review_source_path
from agent_structure_rules import structure_rule_review


class AgentReviewStructureTests(unittest.TestCase):
    def test_pinned_third_party_source_is_outside_human_authored_size_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "scripts" / "third_party" / "engine" / "engine.py"
            source.parent.mkdir(parents=True)
            source.write_text("value = 1\n", encoding="utf-8")
            (source.parent / "LICENSE").write_text("license\n", encoding="utf-8")
            (source.parent / "README.md").write_text(
                "Upstream: example\nCommit: abc\nSHA-256: 123\nLicense: MIT\n",
                encoding="utf-8",
            )

            self.assertFalse(review_source_path(project, source.relative_to(project)))

    def test_unprovenanced_third_party_source_stays_in_structure_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "scripts" / "third_party" / "engine" / "engine.py"
            source.parent.mkdir(parents=True)
            source.write_text("value = 1\n", encoding="utf-8")

            self.assertTrue(review_source_path(project, source.relative_to(project)))

    def test_changed_source_paths_can_be_limited_to_review_pathspec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "src").mkdir()
            (project / "src" / "a.py").write_text("value = 1\n", encoding="utf-8")
            (project / "src" / "b.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "add", "."], cwd=project, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=AgentPlaybook Tests",
                    "-c",
                    "user.email=agentplaybook@example.invalid",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=project,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (project / "src" / "a.py").write_text("value = 2\n", encoding="utf-8")
            (project / "src" / "b.py").write_text("value = 2\n", encoding="utf-8")

            def run_command(command: list[str], cwd: Path) -> dict[str, object]:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            _discovery, paths = changed_source_paths(project, run_command, ["src/a.py"])

        self.assertEqual([Path("src/a.py")], paths)

    def test_existing_oversized_file_growth_requires_evidence_without_hard_failure(self) -> None:
        result = {"failures": [], "warnings": []}

        check_file_size(
            Path("src/messages.ts"),
            ["export const messages = {};"] * 501,
            500,
            {"status": "M", "additions": 33},
            result,
        )

        self.assertEqual([], result["failures"])
        self.assertTrue(any("already over 500 lines" in warning for warning in result["warnings"]))

    def test_changed_file_over_review_pressure_limit_requires_evidence(self) -> None:
        result = {"failures": [], "warnings": []}

        check_file_size(
            Path("src/workflow.ts"),
            ["export const value = 1;"] * 301,
            500,
            {"status": "M", "additions": 4},
            result,
        )

        self.assertEqual([], result["failures"])
        self.assertTrue(any("review-pressure limit is 300" in warning for warning in result["warnings"]))

    def test_new_oversized_file_still_fails(self) -> None:
        result = {"failures": [], "warnings": []}

        check_file_size(
            Path("src/newFeature.ts"),
            ["export const value = 1;"] * 501,
            500,
            {"status": "A", "additions": 501},
            result,
        )

        self.assertTrue(any("new development source/style file" in failure for failure in result["failures"]))

    def test_structure_rules_fail_for_forbidden_new_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / ".agents").mkdir()
            (project / ".agents" / "structure-rules.json").write_text(
                json.dumps({"forbidden_new_paths": ["**/utils/**"]}),
                encoding="utf-8",
            )
            source = project / "src" / "utils" / "userClient.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const userClient = {};\n", encoding="utf-8")

            result = structure_rule_review(
                project,
                [Path("src/utils/userClient.ts")],
                {"src/utils/userClient.ts": {"status": "A"}},
                lambda root, path: (root / path).suffix == ".ts" and (root / path).exists(),
                lambda path: False,
            )

        self.assertTrue(
            any(
                "forbidden" in failure and "src/utils/userClient.ts" in failure
                for failure in result["failures"]
            )
        )

    def test_structure_rules_fail_for_forbidden_import(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / ".agents").mkdir()
            (project / ".agents" / "structure-rules.json").write_text(
                json.dumps(
                    {
                        "rules": [
                            {
                                "name": "domain_stays_out_of_ui",
                                "paths": ["src/domain/**"],
                                "forbidden_imports": ["src/ui/**"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = project / "src" / "domain" / "userPolicy.ts"
            source.parent.mkdir(parents=True)
            source.write_text("import { Button } from '../ui/button';\n", encoding="utf-8")

            result = structure_rule_review(
                project,
                [Path("src/domain/userPolicy.ts")],
                {"src/domain/userPolicy.ts": {"status": "M"}},
                lambda root, path: (root / path).suffix == ".ts" and (root / path).exists(),
                lambda path: False,
            )

        self.assertTrue(
            any(
                "forbidden by" in failure and "src/ui" in failure
                for failure in result["failures"]
            )
        )

    def test_structure_rules_fail_when_new_path_misses_allowed_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / ".agents").mkdir()
            (project / ".agents" / "structure-rules.json").write_text(
                json.dumps({"allowed_new_paths": ["src/features/**", "src/domain/**"]}),
                encoding="utf-8",
            )
            source = project / "src" / "platform" / "bridge.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const bridge = {};\n", encoding="utf-8")

            result = structure_rule_review(
                project,
                [Path("src/platform/bridge.ts")],
                {"src/platform/bridge.ts": {"status": "A"}},
                lambda root, path: (root / path).suffix == ".ts" and (root / path).exists(),
                lambda path: False,
            )

        self.assertTrue(any("allowed_new_paths" in failure for failure in result["failures"]))


if __name__ == "__main__":
    unittest.main()
