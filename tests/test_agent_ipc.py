from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_ipc import emit_event, read_events, summarize_events


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


if __name__ == "__main__":
    unittest.main()

