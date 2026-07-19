from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

_SPEC = importlib.util.spec_from_file_location(
    "claude_stop_gate_under_test", ROOT / "scripts" / "claude_stop_gate.py"
)
assert _SPEC and _SPEC.loader
gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gate)

from support.claude_setup import _merge_claude_stop_gate
from support.setup_config_files import read_json


def _decide(payload: dict) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = gate.decide(payload)
    return code, buffer.getvalue()


def _blocked(out: str) -> bool:
    return bool(out) and json.loads(out).get("decision") == "block"


def _opt_in_project(base: Path) -> Path:
    project = base / "proj"
    (project / ".agentplaybook" / gate.SESSION_MARKER_DIR).mkdir(parents=True)
    (project / "AGENTS.md").write_text("uses agentplaybook\n", encoding="utf-8")
    return project


def _record_edit(project: Path, session_id: str, *, newer_than: Path | None = None) -> None:
    marker = gate.edit_activity_marker(project, session_id)
    marker.write_text("", encoding="utf-8")
    if newer_than is not None:
        # Filesystem timestamp granularity can tie these two writes; the gate
        # compares them, so make the ordering explicit rather than racy.
        stamp = newer_than.stat().st_mtime + 1
        os.utime(marker, (stamp, stamp))


def _write_finish(project: Path, session_id: str | None = None) -> None:
    payload: dict = {}
    if session_id is not None:
        payload["runtime_session"] = {"runtime": "claude", "session_id": session_id}
    (project / ".agentplaybook" / "finish.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _payload(project: Path, session_id: str, **extra) -> dict:
    return {"session_id": session_id, "cwd": str(project), **extra}


class ClaudeStopGateTests(unittest.TestCase):
    def test_read_only_session_may_stop(self) -> None:
        # Nothing was mutated, so there is nothing to finish.
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))

            code, out = _decide(_payload(project, "s1"))

        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_editing_session_without_finish_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")

            code, out = _decide(_payload(project, "s1"))

        self.assertEqual(0, code)
        self.assertTrue(_blocked(out))
        self.assertIn("finish", json.loads(out)["reason"])

    def test_finish_from_another_session_does_not_release_the_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")
            _write_finish(project, "some-other-session")

            _, out = _decide(_payload(project, "s1"))

        self.assertTrue(_blocked(out))

    def test_failed_finish_does_not_release_the_stop(self) -> None:
        # `finish` stamps its session only when it records no failures, so a
        # failed run leaves no stamp and the gate stays closed.
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")
            _write_finish(project)

            _, out = _decide(_payload(project, "s1"))

        self.assertTrue(_blocked(out))

    def test_passing_finish_this_session_allows_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")
            _write_finish(project, "s1")

            code, out = _decide(_payload(project, "s1"))

        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_second_stop_without_new_edits_is_not_blocked_again(self) -> None:
        # A stop is not always a completion report: a session also stops to ask
        # the user a question. Blocking that a second time costs a round trip
        # and adds no enforcement, since the gate already reported the work.
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")

            _, first = _decide(_payload(project, "s1"))
            _, second = _decide(_payload(project, "s1"))

            self.assertTrue(_blocked(first))
            self.assertEqual("", second)

    def test_further_edits_rearm_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")
            _decide(_payload(project, "s1"))

            _, quiet = _decide(_payload(project, "s1"))
            _record_edit(project, "s1", newer_than=gate.blocked_marker(project, "s1"))
            _, rearmed = _decide(_payload(project, "s1"))

            self.assertEqual("", quiet)
            self.assertTrue(_blocked(rearmed))

    def test_stop_hook_active_never_blocks_again(self) -> None:
        # The gate already blocked once and the model continued; blocking a
        # second time would trap the session in a loop.
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")

            code, out = _decide(_payload(project, "s1", stop_hook_active=True))

        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_env_kill_switch_disables_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")

            with patch.dict("os.environ", {"AGENTPLAYBOOK_CLAUDE_STOP_GATE": "0"}):
                code, out = _decide(_payload(project, "s1"))

        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_non_agentplaybook_project_is_never_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, out = _decide({"session_id": "s1", "cwd": tmp})

        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_malformed_stdin_fails_open(self) -> None:
        with patch.object(sys, "stdin", io.StringIO("not json{{")):
            code = gate.main()

        self.assertEqual(0, code)

    def test_block_reason_uses_resolved_absolute_launcher_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _record_edit(project, "s1")

            _, out = _decide(_payload(project, "s1"))

        reason = json.loads(out)["reason"]
        self.assertIn(str(gate.stable_launcher_path()), reason)
        self.assertNotIn("~/.agentplaybook", reason)

    def test_setup_installs_stop_gate_without_removing_user_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            user_hook = {"type": "command", "command": "my-own-stop-notifier"}
            target.write_text(json.dumps({
                "hooks": {"Stop": [{"matcher": "", "hooks": [user_hook]}]}
            }))
            command = "AGENTPLAYBOOK_HOOK_SOFT_FAIL=1 /abs/agentplaybook-hook claude-stop-gate"

            status = _merge_claude_stop_gate(target, command, dry_run=False)
            commands = [
                hook["command"]
                for group in read_json(target)["hooks"]["Stop"]
                for hook in group["hooks"]
            ]

        self.assertEqual("installed", status)
        self.assertIn(command, commands)
        self.assertIn("my-own-stop-notifier", commands)

    def test_setup_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            target.write_text(json.dumps({"hooks": {}}))
            command = "AGENTPLAYBOOK_HOOK_SOFT_FAIL=1 /abs/agentplaybook-hook claude-stop-gate"

            first = _merge_claude_stop_gate(target, command, dry_run=False)
            after_first = target.read_text()
            second = _merge_claude_stop_gate(target, command, dry_run=False)

            self.assertEqual("installed", first)
            self.assertEqual("ok", second)
            self.assertEqual(after_first, target.read_text())


if __name__ == "__main__":
    unittest.main()
