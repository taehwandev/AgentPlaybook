from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_ipc import read_events
from agent_scheduler import claim_next, enqueue_task
from workflow_dispatch_launch import _run_scheduled_worker
from workflow_dispatch import build_dispatch_manifest


class DispatchHeartbeatTests(unittest.TestCase):
    def test_manifest_defaults_heartbeat_to_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_dispatch_manifest(
                "task",
                "Inspect the scheduler",
                Path(directory),
                work_kind="analysis",
                request_classified=True,
                classification_evidence="clear-scoped analysis blockers resolved",
                request_classification={
                    "clarity": "clear-scoped",
                    "question_drill": False,
                    "recommended_route": "task",
                },
                route={"required_docs": ["AGENTS.md"], "gates": []},
            )
            self.assertEqual(0, manifest["heartbeat_interval_seconds"])

    def test_default_dispatch_does_not_start_heartbeat_loop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = enqueue_task(project, "run-1")
            claim_next(project)
            self.assertEqual(0, _run_scheduled_worker([], lambda _argv: 0, project, task))
            self.assertEqual([], read_events(project, event_type="worker.heartbeat"))
            self.assertEqual([], read_events(project, event_type="worker.result"))

    def test_opt_in_dispatch_emits_heartbeat_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = enqueue_task(project, "run-1")
            claim_next(project)

            def runner(_argv: list[str]) -> int:
                time.sleep(0.08)
                return 0

            self.assertEqual(
                0,
                _run_scheduled_worker(
                    [], runner, project, task, heartbeat_interval_seconds=0.02
                ),
            )
            self.assertGreaterEqual(len(read_events(project, event_type="worker.heartbeat")), 1)
            self.assertEqual(1, len(read_events(project, event_type="worker.result")))


if __name__ == "__main__":
    unittest.main()
