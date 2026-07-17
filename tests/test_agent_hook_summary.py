from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentHookSummaryTests(unittest.TestCase):
    def test_invalid_command_surfaces_the_real_argparse_error(self) -> None:
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
                    "code-review",
                    "--request",
                    "review everything that is not committed yet",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("FAIL start", result.stdout)
            self.assertIn("invalid choice: 'code-review'", result.stdout)


if __name__ == "__main__":
    unittest.main()
