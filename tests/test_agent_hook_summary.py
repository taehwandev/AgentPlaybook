from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentHookSummaryTests(unittest.TestCase):
    def test_invalid_command_surfaces_the_real_argparse_error(self) -> None:
        for invalid_command in ("code-review", "implement"):
            with self.subTest(invalid_command=invalid_command):
                with tempfile.TemporaryDirectory() as directory:
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts/agent-hook.py"),
                            "start",
                            "--project",
                            directory,
                            "--rules",
                            str(ROOT),
                            "--command",
                            invalid_command,
                            "--request",
                            "review everything that is not committed yet",
                        ],
                        capture_output=True,
                        text=True,
                    )

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("FAIL start", result.stdout)
                    self.assertIn(
                        f"invalid choice: '{invalid_command}'", result.stdout
                    )

    def test_rejected_invocation_does_not_demand_an_impossible_repair_cycle(self) -> None:
        # A usage error happens before any gate runs, so nothing reaches the
        # ledger. Sending the caller into the repair cycle deadlocks them:
        # repair-verify builds its receipt from a recorded failed checkpoint,
        # and this failure never recorded one.
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/agent-hook.py"),
                    "start",
                    "--project",
                    directory,
                    "--rules",
                    str(ROOT),
                    "--command",
                    "implement",
                    "--request",
                    "anything",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("invocation request:", result.stdout)
            self.assertIn("nothing to repair", result.stdout)
            self.assertNotIn("recovery request:", result.stdout)
            self.assertNotIn("--repair-cycle", result.stdout)

    def test_request_intake_rejection_does_not_demand_an_impossible_repair_cycle(self) -> None:
        # Clarification blocks happen before route creation, so there is no
        # route fingerprint or failed gate checkpoint for repair-verify to bind.
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/agent-hook.py"),
                    "start",
                    "--project",
                    directory,
                    "--rules",
                    str(ROOT),
                    "--command",
                    "build",
                    "--request",
                    "검증해줘",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("needs clarification before route `build`", result.stdout)
            self.assertIn("invocation request:", result.stdout)
            self.assertIn("nothing to repair", result.stdout)
            self.assertNotIn("recovery request:", result.stdout)
            self.assertNotIn("--repair-cycle", result.stdout)


if __name__ == "__main__":
    unittest.main()
