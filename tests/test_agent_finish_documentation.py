from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_documentation import required_doc_target_failures


class RequiredDocTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = {"required_docs": ["AGENTS.md"]}

    def test_exact_required_doc_target_is_allowed(self) -> None:
        self.assertEqual(
            [],
            required_doc_target_failures(target="AGENTS.md", route=self.route),
        )

    def test_combined_target_is_rejected_early(self) -> None:
        self.assertEqual(
            [
                "documentation target embeds route required_docs but is not one exact "
                "route-relative path: AGENTS.md; record one documentation SUCCESS "
                "entry per required doc"
            ],
            required_doc_target_failures(
                target="AGENTS.md; workflows/README.md",
                route=self.route,
            ),
        )

    def test_distinct_nested_path_with_same_basename_is_allowed(self) -> None:
        self.assertEqual(
            [],
            required_doc_target_failures(
                target="docs/AGENTS.md",
                route=self.route,
            ),
        )

    def test_path_with_required_doc_prefix_is_allowed(self) -> None:
        self.assertEqual(
            [],
            required_doc_target_failures(
                target="AGENTS.md.backup",
                route=self.route,
            ),
        )


if __name__ == "__main__":
    unittest.main()
