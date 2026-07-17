from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentOsWatchdogTests(unittest.TestCase):
    def test_default_watchdog_is_one_bounded_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/agent-os-watchdog.py"), "--project", directory],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(1, len(payload["cycles"]))
            self.assertEqual(0, payload["cycles"][0]["recovered_runs"])


if __name__ == "__main__":
    unittest.main()
