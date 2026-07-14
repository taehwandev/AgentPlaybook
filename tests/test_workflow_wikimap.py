from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_search import search_docs_outcome
from workflow_wikimap import (
    WIKIMAP_COMMIT,
    WIKIMAP_SCRIPT,
    WIKIMAP_SHA256,
    WIKIMAP_VERSION,
    clear_wikimap_cache,
    search_wikimap,
)


class WorkflowWikimapTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_wikimap_cache()

    def test_vendor_source_is_pinned_with_license(self) -> None:
        digest = hashlib.sha256(WIKIMAP_SCRIPT.read_bytes()).hexdigest()
        license_text = (WIKIMAP_SCRIPT.parent / "LICENSE").read_text(encoding="utf-8")

        self.assertEqual("1.0.0", WIKIMAP_VERSION)
        self.assertEqual("9c26d7b66322741532ede0b474f0e5106643f275", WIKIMAP_COMMIT)
        self.assertEqual(WIKIMAP_SHA256, digest)
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Donghyun Ha", license_text)

    def test_adapter_invokes_only_update_and_search_commands(self) -> None:
        payload = {
            "results": [
                {
                    "path": "guide.md",
                    "line": 3,
                    "heading": "Guide",
                    "score": 1.0,
                    "matched": ["retrieval rule"],
                    "sources": "1/1",
                }
            ]
        }
        completed_update = subprocess.CompletedProcess([], 0, stdout="updated", stderr="")
        completed_search = subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "guide.md").write_text("# Guide\n\nretrieval rule\n", encoding="utf-8")
            with patch(
                "workflow_wikimap._run",
                side_effect=[(completed_update, ""), (completed_search, "")],
            ) as run:
                outcome = search_wikimap(root, ["retrieval rule"], max_results=4)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(outcome.available)
        self.assertEqual(["update", "search"], [command[4] for command in commands])
        flattened = " ".join(part for command in commands for part in command)
        for forbidden in ("install", "migrate", "--hook", "import-graphify", "note"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, flattened)

    def test_checksum_failure_uses_legacy_recovery_scorer(self) -> None:
        with patch(
            "workflow_search.search_wikimap",
            return_value=type(
                "Unavailable",
                (),
                {
                    "available": False,
                    "error": "pinned wikimap source checksum does not match",
                },
            )(),
        ):
            outcome = search_docs_outcome(ROOT, "documentation update", max_results=4)

        self.assertEqual("legacy", outcome.backend)
        self.assertIn("checksum", outcome.fallback_reason)
        self.assertTrue(outcome.results)
        self.assertTrue(all(item["search_backend"] == "legacy" for item in outcome.results))


if __name__ == "__main__":
    unittest.main()
