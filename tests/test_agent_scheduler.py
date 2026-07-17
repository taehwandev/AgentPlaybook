from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_scheduler import claim_next, claim_task, choose_capacity, enqueue_task, retry_task, transition_task


class AgentSchedulerTests(unittest.TestCase):
    def test_small_work_stays_serial_and_independent_work_is_bounded(self) -> None:
        self.assertEqual(1, choose_capacity(0, 3))
        self.assertEqual(1, choose_capacity(1, 3))
        self.assertEqual(2, choose_capacity(2, 2))
        self.assertEqual(3, choose_capacity(4, 8))

    def test_claims_highest_priority_and_respects_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            low = enqueue_task(project, "run-low", priority=1)
            high = enqueue_task(project, "run-high", priority=5)

            claimed = claim_next(project, capacity=1)
            self.assertEqual(high["task_id"], claimed["task_id"])
            self.assertIsNone(claim_next(project, capacity=1))
            self.assertEqual("completed", transition_task(project, claimed["task_id"], "completed")["state"])
            self.assertEqual(low["task_id"], claim_next(project, capacity=1)["task_id"])

    def test_unknown_task_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                transition_task(Path(directory), "missing", "unknown")

    def test_retry_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            task = enqueue_task(project, "run-1", max_retries=1)
            self.assertEqual(task["task_id"], claim_next(project)["task_id"])
            transition_task(project, task["task_id"], "failed")
            retried = retry_task(project, task["task_id"])
            self.assertEqual(2, retried["attempt"])
            self.assertEqual(task["task_id"], claim_next(project)["task_id"])
            transition_task(project, task["task_id"], "failed")
            self.assertIsNone(retry_task(project, task["task_id"]))

    def test_targeted_claim_does_not_replace_retry_with_another_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            retryable = enqueue_task(project, "run-retry", priority=1, max_retries=1)
            other = enqueue_task(project, "run-other", priority=9)
            transition_task(project, retryable["task_id"], "failed")
            retried = retry_task(project, retryable["task_id"])
            self.assertEqual("queued", retried["state"])
            self.assertEqual(retryable["task_id"], claim_task(project, retryable["task_id"], capacity=1)["task_id"])
            self.assertEqual(other["task_id"], claim_next(project, capacity=2)["task_id"])


if __name__ == "__main__":
    unittest.main()
