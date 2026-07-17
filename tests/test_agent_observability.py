from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_observability import status_snapshot
from agent_run_registry import register_run
from agent_scheduler import enqueue_task


class AgentObservabilityTests(unittest.TestCase):
    def test_snapshot_exposes_only_aggregated_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run = register_run(project, project / "preflight.json", {"command": "task"}, {})
            enqueue_task(project, run["run_id"])
            snapshot = status_snapshot(project)
            self.assertEqual(2, snapshot["api_version"])
            self.assertTrue(snapshot["snapshot_id"])
            self.assertTrue(snapshot["captured_at"])
            self.assertEqual("project-state-lock", snapshot["consistency"])
            self.assertEqual(1, snapshot["api_contract"]["contract_version"])
            self.assertEqual(1, snapshot["active_runs"])
            self.assertEqual({"queued": 1}, snapshot["task_counts"])
            self.assertTrue(snapshot["events"]["run.started"])
            self.assertNotIn("request", str(snapshot))


if __name__ == "__main__":
    unittest.main()
