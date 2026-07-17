from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_ipc import emit_event, emit_heartbeat, emit_partial_result, emit_worker_failure, emit_worker_result, read_events, summarize_events


class AgentIPCTests(unittest.TestCase):
    def test_event_channel_is_content_free_and_summarizable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            event = emit_event(project, "run.started", run_id="run-1", state="running")
            self.assertEqual("run.started", event["event_type"])
            self.assertEqual([], [value for value in event.values() if value == "private request"])
            self.assertEqual({"run.started": 1}, summarize_events(project))
            self.assertEqual(1, len(read_events(project, event_type="run.started")))

    def test_invalid_enum_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                emit_event(Path(directory), "Run Started")

    def test_worker_events_are_content_free_and_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            emit_heartbeat(project, run_id="run-1", task_id="task-1", worker_id="worker-1")
            emit_worker_result(project, run_id="run-1", task_id="task-1", worker_id="worker-1", result_id="result-1")
            emit_worker_failure(project, run_id="run-1", task_id="task-1", worker_id="worker-1")
            emit_partial_result(project, run_id="run-1", task_id="task-1", worker_id="worker-1", result_id="result-1")
            events = read_events(project)
            self.assertEqual(4, len(events))
            self.assertEqual({"worker.heartbeat", "worker.result", "worker.failure", "worker.partial"}, {event["event_type"] for event in events})
            self.assertNotIn("prompt", str(events))


if __name__ == "__main__":
    unittest.main()
