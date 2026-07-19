#!/usr/bin/env python3
"""Claude Code PreToolUse gate that enforces AgentPlaybook workflow entry.

Claude's runtime bridge is otherwise advisory: nothing stops a file edit when
the agent skipped the ``start`` hook, so the workflow is easy to ignore. This
gate is the Claude-native equivalent of the Codex permission prefix rule. It
denies a file-edit tool call when an AgentPlaybook project has no fresh
preflight evidence, which forces the agent to run ``start`` (route + preflight)
before mutating files. Once evidence exists the gate steps aside for the rest of
the session.

Contract (Claude Code PreToolUse hook):
- Reads a JSON payload from stdin with ``tool_name``, ``cwd``, ``session_id``.
- Prints a ``permissionDecision`` JSON object to allow or deny.
- Only file-edit tools are gated; everything else and every unexpected error
  fails open (exit 0, no output) so the gate can never brick ordinary editing.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
STATE_DIR = ".agentplaybook"
PREFLIGHT_NAME = "preflight.json"
SESSION_MARKER_DIR = "claude-pretool-gate"
OPT_IN_FILES = ("AGENTS.md", "CLAUDE.md", "CODEX.md")
OPT_IN_TOKEN = "agentplaybook"
DEFAULT_MAX_AGE_SECONDS = 8 * 60 * 60
MAX_ROOT_WALK = 40


def allow() -> int:
    """Fail-open: no output means Claude proceeds with the tool call."""
    return 0


def deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def max_age_seconds() -> int:
    raw = os.environ.get("AGENTPLAYBOOK_CLAUDE_GATE_MAX_AGE_SECONDS", "").strip()
    if not raw:
        return DEFAULT_MAX_AGE_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_AGE_SECONDS
    return value if value >= 0 else DEFAULT_MAX_AGE_SECONDS


def opts_in(path: Path) -> bool:
    """True when this directory marks a project that uses AgentPlaybook."""
    if (path / STATE_DIR).is_dir():
        return True
    for name in OPT_IN_FILES:
        candidate = path / name
        try:
            head = candidate.read_text(encoding="utf-8", errors="ignore")[:8192]
        except OSError:
            continue
        if OPT_IN_TOKEN in head.lower():
            return True
    return False


def find_project_root(cwd: Path) -> Path | None:
    """Nearest ancestor (including cwd) that opts into AgentPlaybook."""
    for candidate in (cwd, *cwd.parents):
        if opts_in(candidate):
            return candidate
        if candidate == candidate.parent:
            break
    return None


def evidence_is_fresh(root: Path) -> bool:
    preflight = root / STATE_DIR / PREFLIGHT_NAME
    try:
        mtime = preflight.stat().st_mtime
    except OSError:
        return False
    return (time.time() - mtime) <= max_age_seconds()


def safe_session_id(session_id: str) -> str:
    cleaned = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    return cleaned or "unknown-session"


def session_marker(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / safe_session_id(session_id)


def touch_marker(marker: Path) -> None:
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    except OSError:
        pass


def deny_reason(root: Path) -> str:
    return (
        "AgentPlaybook: run the workflow start hook before editing files in this "
        f"project. No fresh preflight evidence at {root / STATE_DIR / PREFLIGHT_NAME}. "
        "Run `~/.agentplaybook/bin/agentplaybook-hook start --project "
        f"{root} --rules <AGENTPLAYBOOK_ROOT> --command <route> --request \"<user "
        "request>\"`, read the route required_docs, then retry the edit. Set "
        "AGENTPLAYBOOK_CLAUDE_GATE_MAX_AGE_SECONDS to tune the freshness window."
    )


def decide(payload: dict) -> int:
    tool = payload.get("tool_name")
    if tool not in EDIT_TOOLS:
        return allow()
    cwd_raw = payload.get("cwd") or os.getcwd()
    try:
        cwd = Path(cwd_raw).resolve()
    except OSError:
        return allow()
    root = find_project_root(cwd)
    if root is None:
        # Not an AgentPlaybook project; never block ordinary editing.
        return allow()
    session_id = str(payload.get("session_id") or "")
    marker = session_marker(root, session_id)
    if marker.exists():
        return allow()
    if evidence_is_fresh(root):
        touch_marker(marker)
        return allow()
    return deny(deny_reason(root))


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return allow()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return allow()
        return decide(payload)
    except Exception:
        # Any unexpected failure must fail open.
        return allow()


if __name__ == "__main__":
    sys.exit(main())
