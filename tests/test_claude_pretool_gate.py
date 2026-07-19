from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

_GATE_SPEC = importlib.util.spec_from_file_location(
    "claude_pretool_gate_under_test", ROOT / "scripts" / "claude_pretool_gate.py"
)
assert _GATE_SPEC and _GATE_SPEC.loader
gate = importlib.util.module_from_spec(_GATE_SPEC)
_GATE_SPEC.loader.exec_module(gate)

from support.claude_setup import (
    _PRETOOL_GATE_ALIAS,
    _PRETOOL_GATE_MATCHER,
    _merge_claude_pre_tool_gate,
)
from support.setup_config_files import read_json


def _decide(payload: dict) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = gate.decide(payload)
    return code, buffer.getvalue()


def _opt_in_project(base: Path) -> Path:
    project = base / "proj"
    (project / ".agentplaybook").mkdir(parents=True)
    (project / "AGENTS.md").write_text("uses agentplaybook-hook\n", encoding="utf-8")
    return project


def _write_preflight(project: Path) -> None:
    (project / ".agentplaybook" / "preflight.json").write_text("{}", encoding="utf-8")


class ClaudePreToolGateTests(unittest.TestCase):
    def test_non_edit_tool_is_allowed(self) -> None:
        code, out = _decide({"tool_name": "Bash", "cwd": "/tmp", "session_id": "s"})
        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_edit_outside_agentplaybook_project_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, out = _decide(
                {"tool_name": "Edit", "cwd": tmp, "session_id": "s"}
            )
        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_edit_without_preflight_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            code, out = _decide(
                {"tool_name": "Edit", "cwd": str(project), "session_id": "s"}
            )
        self.assertEqual(0, code)
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("start hook", decision["permissionDecisionReason"])

    def test_edit_with_fresh_preflight_is_allowed_and_marks_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            code, out = _decide(
                {"tool_name": "Write", "cwd": str(project), "session_id": "s5"}
            )
            self.assertEqual(0, code)
            self.assertEqual("", out)
            marker = project / ".agentplaybook" / "claude-pretool-gate" / "s5"
            self.assertTrue(marker.exists())

    def test_session_marker_short_circuits_without_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            marker_dir = project / ".agentplaybook" / "claude-pretool-gate"
            marker_dir.mkdir(parents=True)
            (marker_dir / "s6").write_text("", encoding="utf-8")
            code, out = _decide(
                {"tool_name": "Edit", "cwd": str(project), "session_id": "s6"}
            )
        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_malformed_stdin_fails_open(self) -> None:
        with patch_stdin("not json{{"):
            code = gate.main()
        self.assertEqual(0, code)

    def test_nested_cwd_resolves_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            nested = project / "a" / "b"
            nested.mkdir(parents=True)
            code, out = _decide(
                {"tool_name": "Edit", "cwd": str(nested), "session_id": "s"}
            )
        self.assertEqual(0, code)
        self.assertEqual("deny", json.loads(out)["hookSpecificOutput"]["permissionDecision"])


class ClaudePreToolGateSetupTests(unittest.TestCase):
    def test_merge_installs_pre_tool_use_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            command = f"AGENTPLAYBOOK_HOOK_SOFT_FAIL=1 launcher {_PRETOOL_GATE_ALIAS}"
            status = _merge_claude_pre_tool_gate(target, command, dry_run=False)
            self.assertEqual("installed", status)
            config = read_json(target)
            groups = config["hooks"]["PreToolUse"]
            group = next(g for g in groups if g.get("matcher") == _PRETOOL_GATE_MATCHER)
            self.assertEqual(command, group["hooks"][0]["command"])

    def test_merge_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            command = f"AGENTPLAYBOOK_HOOK_SOFT_FAIL=1 launcher {_PRETOOL_GATE_ALIAS}"
            _merge_claude_pre_tool_gate(target, command, dry_run=False)
            status = _merge_claude_pre_tool_gate(target, command, dry_run=False)
            self.assertEqual("ok", status)
            config = read_json(target)
            matching = [
                g
                for g in config["hooks"]["PreToolUse"]
                if g.get("matcher") == _PRETOOL_GATE_MATCHER
            ]
            self.assertEqual(1, len(matching))


class patch_stdin:
    def __init__(self, text: str) -> None:
        self.text = text
        self._old = None

    def __enter__(self) -> None:
        self._old = sys.stdin
        sys.stdin = io.StringIO(self.text)

    def __exit__(self, *exc: object) -> None:
        sys.stdin = self._old


if __name__ == "__main__":
    unittest.main()
