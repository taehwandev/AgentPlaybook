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

    def _write_new_source(self, project: Path, session: str, relative: str) -> tuple[int, str]:
        return _decide(
            {
                "tool_name": "Write",
                "cwd": str(project),
                "session_id": session,
                "tool_input": {"file_path": relative},
            }
        )

    def test_new_source_files_up_to_budget_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            for index in range(5):
                code, out = self._write_new_source(project, "sp", f"src/file{index}.py")
                self.assertEqual(0, code)
                self.assertEqual("", out, f"file{index} should be allowed")

    def test_new_source_file_past_budget_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            for index in range(5):
                self._write_new_source(project, "sp", f"src/file{index}.py")
            code, out = self._write_new_source(project, "sp", "src/file5.py")
        self.assertEqual(0, code)
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("proportionality gate", decision["permissionDecisionReason"])

    def test_ack_file_unlocks_further_new_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            for index in range(5):
                self._write_new_source(project, "sp", f"src/file{index}.py")
            ack = project / ".agentplaybook" / "claude-pretool-gate" / "sp.sprawl-ack"
            ack.parent.mkdir(parents=True, exist_ok=True)
            ack.write_text("each file owns a distinct platform adapter\n", encoding="utf-8")
            code, out = self._write_new_source(project, "sp", "src/file5.py")
        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_non_source_new_files_are_never_counted(self) -> None:
        # Doc/content sprawl (e.g. a writing workspace) must not be blocked.
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            for index in range(12):
                code, out = self._write_new_source(project, "sp", f"drafts/post{index}.md")
                self.assertEqual("", out, f"markdown draft {index} must be allowed")

    def test_overwriting_existing_source_file_is_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = _opt_in_project(Path(tmp))
            _write_preflight(project)
            existing = project / "src" / "existing.py"
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.write_text("value = 1\n", encoding="utf-8")
            # Fill the budget with new files, then overwrite the existing one.
            for index in range(5):
                self._write_new_source(project, "sp", f"src/new{index}.py")
            code, out = self._write_new_source(project, "sp", "src/existing.py")
        self.assertEqual(0, code)
        self.assertEqual("", out)

    def test_new_file_budget_can_be_disabled_with_zero(self) -> None:
        import os as _os

        previous = _os.environ.get("AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET")
        _os.environ["AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET"] = "0"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project = _opt_in_project(Path(tmp))
                _write_preflight(project)
                for index in range(20):
                    code, out = self._write_new_source(project, "sp", f"src/file{index}.py")
                    self.assertEqual("", out)
        finally:
            if previous is None:
                _os.environ.pop("AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET", None)
            else:
                _os.environ["AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET"] = previous


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
