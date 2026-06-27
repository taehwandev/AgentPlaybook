from __future__ import annotations

import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_review_structure import check_file_size


class AgentReviewStructureTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
