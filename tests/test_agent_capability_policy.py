from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_capability_policy import capability_profile, validate_capability_profile


class AgentCapabilityPolicyTests(unittest.TestCase):
    def test_analysis_is_read_only_and_non_authoring(self) -> None:
        profile = capability_profile("analysis")
        self.assertEqual("read-only", profile["sandbox_mode"])
        self.assertEqual("deny", profile["child_process"])
        self.assertEqual([], validate_capability_profile(profile))

    def test_isolated_authoring_keeps_runtime_mode_and_isolates_filesystem(self) -> None:
        profile = capability_profile("feature", isolation_required=True)
        self.assertEqual("workspace-write", profile["sandbox_mode"])
        self.assertEqual("isolated-write", profile["isolation_mode"])
        self.assertEqual("isolated-write", profile["filesystem"])
        self.assertEqual([], validate_capability_profile(profile))

    def test_invalid_read_only_authoring_profile_is_rejected(self) -> None:
        self.assertTrue(validate_capability_profile({"sandbox_mode": "read-only", "authoring_policy": "code authoring allowed"}))


if __name__ == "__main__":
    unittest.main()
