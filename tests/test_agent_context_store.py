from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_context_store import refresh_context_snapshot, validate_context_snapshot


class AgentContextStoreTests(unittest.TestCase):
    def test_snapshot_refresh_and_validation_follow_route_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            rules = ROOT
            route = {"required_docs": ["AGENTS.md"], "gates": []}
            intake = {"request_classified": True, "request_fingerprint": "opaque"}
            snapshot = refresh_context_snapshot(project, rules, route, intake)
            self.assertEqual("AGENTS.md", snapshot["required_docs"][0]["path"])
            self.assertEqual([], validate_context_snapshot(project, rules, route, intake))

    def test_route_change_invalidates_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            refresh_context_snapshot(project, ROOT, {"required_docs": ["AGENTS.md"], "gates": []})
            failures = validate_context_snapshot(project, ROOT, {"required_docs": [], "gates": []})
            self.assertTrue(failures)

    def test_request_change_invalidates_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            route = {"required_docs": ["AGENTS.md"], "gates": []}
            refresh_context_snapshot(project, ROOT, route, {"request_classified": True, "request": "one"})
            failures = validate_context_snapshot(project, ROOT, route, {"request_classified": True, "request": "two"})
            self.assertIn("request fingerprint", failures[0])


if __name__ == "__main__":
    unittest.main()
