#!/usr/bin/env python3
"""Claude Code Stop gate for Tao Agent OS.

The PreToolUse gate forces `start` before the first edit, but nothing forced the
other end of the lifecycle. `review` and `finish` were enforced only by the model
remembering to run them, which is exactly the kind of rule a model skips under
load: a session could edit files all the way to a final report with no review
evidence and no gate ledger, and the work would look finished.

This gate closes that end. When a session edited files in an Tao Agent OS
project and has no passing `finish` from that same session, stopping is blocked
once, with the commands needed to resolve it.

Contract (Claude Code Stop hook):
- Reads a JSON payload from stdin with ``session_id``, ``cwd``, and
  ``stop_hook_active``.
- Prints ``{"decision": "block", "reason": ...}`` to keep the session going, or
  nothing to let it stop.
- ``stop_hook_active`` means this gate already blocked once and the model
  continued; blocking again would loop, so that case always allows.
- Blocking is once per batch of edits, not once per stop. A session that stops
  again to ask the user something is not blocked twice for the same work, and
  any further edit re-arms the gate.
- Every unexpected error allows the stop. A gate that can trap a session is
  worse than one that misses a finish.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:  # Never fail to load; used for the message and the session lookup.
    from agent_runtime_session import recorded_session_id
    from support.stable_launcher import stable_launcher_path
except ImportError:  # pragma: no cover - exercised only on a broken install
    def stable_launcher_path() -> Path:
        return Path.home() / ".agentplaybook" / "bin" / "agentplaybook-hook"

    def recorded_session_id(payload: object) -> str:
        if not isinstance(payload, dict):
            return ""
        session = payload.get("runtime_session")
        if not isinstance(session, dict):
            return ""
        recorded = session.get("session_id")
        return recorded if isinstance(recorded, str) else ""

STATE_DIR = ".agentplaybook"
FINISH_NAME = "finish.json"
SESSION_MARKER_DIR = "claude-pretool-gate"
EDIT_ACTIVITY_SUFFIX = ".edited"
BLOCKED_SUFFIX = ".stop-blocked"
# Written by the PreToolUse gate; see session_projects().
SESSION_PROJECT_DIR = "claude-session-projects"
# Written by `finish`; see session_finished() for why finish.json alone is not enough.
FINISHED_SUFFIX = ".finished"
OPT_IN_FILES = ("AGENTS.md", "CLAUDE.md", "CODEX.md")
OPT_IN_TOKEN = "agentplaybook"


def allow() -> int:
    """No output means Claude is free to stop."""
    return 0


def block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def safe_session_id(session_id: str) -> str:
    cleaned = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    return cleaned or "unknown-session"


def opts_in(path: Path) -> bool:
    if (path / STATE_DIR).is_dir():
        return True
    for name in OPT_IN_FILES:
        try:
            head = (path / name).read_text(encoding="utf-8", errors="ignore")[:8192]
        except OSError:
            continue
        if OPT_IN_TOKEN in head.lower():
            return True
    return False


def find_project_root(cwd: Path) -> Path | None:
    for candidate in (cwd, *cwd.parents):
        if opts_in(candidate):
            return candidate
        if candidate == candidate.parent:
            break
    return None


def edit_activity_marker(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / (safe_session_id(session_id) + EDIT_ACTIVITY_SUFFIX)


def blocked_marker(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / (safe_session_id(session_id) + BLOCKED_SUFFIX)


def marker_mtime(marker: Path) -> float | None:
    try:
        return marker.stat().st_mtime
    except OSError:
        return None


def has_unreported_edits(root: Path, session_id: str) -> bool:
    """True when this session edited files the gate has not blocked on yet.

    A stop is not always a completion report -- a session also stops to ask the
    user a question, and blocking that just costs a round trip without adding
    enforcement. The gate cannot read intent, but it can avoid repeating itself:
    it blocks once per batch of edits, and any further edit re-arms it.

    Recording that the gate blocked is safe in a way recording workflow entry
    was not. This marker can only ever make the gate quieter about work it has
    already reported; it can never stand in for a finish.
    """
    edited = marker_mtime(edit_activity_marker(root, session_id))
    if edited is None:
        return False
    blocked = marker_mtime(blocked_marker(root, session_id))
    return blocked is None or edited > blocked


def record_block(root: Path, session_id: str) -> None:
    marker = blocked_marker(root, session_id)
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    except OSError:
        pass


def finished_marker(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / (safe_session_id(session_id) + FINISHED_SUFFIX)


def session_finished(root: Path, session_id: str) -> bool:
    """True when a passing `finish` ran in this session.

    `finish` writes a per-session record, and only when it found no failures, so
    a failed finish leaves this gate closed instead of counting as completion.

    The per-session record exists because `finish.json` is a single shared file:
    any later finish -- another runtime, another session, a re-verification run
    -- overwrites it and erases the proof that this session completed. Stamping
    the session inside that file was not enough; observed live when a Codex
    re-verification run replaced a passing Claude finish and this gate then
    blocked completed work. The shared file is still accepted as a fallback for
    a finish written before the per-session record existed.
    """
    if finished_marker(root, session_id).exists():
        return True
    try:
        payload = json.loads((root / STATE_DIR / FINISH_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return recorded_session_id(payload) == session_id


def session_projects(session_id: str, cwd_root: Path | None) -> list[Path]:
    """Every project this session edited, not just the one it happens to sit in.

    A stop happens once, with one cwd, but a session can edit files across
    several projects. Checking only the cwd project let an edited project stop
    unverified: the cwd project had a finish, so the gate allowed the stop while
    another project's work had never been reviewed.
    """
    roots: list[Path] = []
    if cwd_root is not None:
        roots.append(cwd_root)
    index = Path.home() / STATE_DIR / SESSION_PROJECT_DIR / safe_session_id(session_id)
    try:
        recorded = index.read_text(encoding="utf-8").splitlines()
    except OSError:
        recorded = []
    for line in recorded:
        candidate = Path(line.strip())
        if line.strip() and candidate not in roots:
            roots.append(candidate)
    return roots


def block_reason(root: Path) -> str:
    launcher = stable_launcher_path()
    return (
        "Tao Agent OS: this session edited files but has no passing finish check. "
        "Record the remaining route gates with `gate` or `gate-batch`, then run "
        f"`{launcher} review --project {root} --rules <AGENTPLAYBOOK_ROOT> "
        "--review-scope working-tree --review-outcome <pass|findings> ...` and "
        f"`{launcher} finish --project {root} --rules <AGENTPLAYBOOK_ROOT>`. "
        "If finish reports failures, repair them instead of reporting completion. "
        "Set AGENTPLAYBOOK_CLAUDE_STOP_GATE=0 to disable this gate."
    )


def gate_enabled() -> bool:
    return os.environ.get("AGENTPLAYBOOK_CLAUDE_STOP_GATE", "").strip() != "0"


def decide(payload: dict) -> int:
    if not gate_enabled():
        return allow()
    # Already blocked once for this stop; blocking again would loop forever.
    if payload.get("stop_hook_active"):
        return allow()
    try:
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    except OSError:
        return allow()
    session_id = str(payload.get("session_id") or "")
    if not session_id:
        return allow()
    for root in session_projects(session_id, find_project_root(cwd)):
        if session_finished(root, session_id):
            continue
        if not has_unreported_edits(root, session_id):
            continue
        record_block(root, session_id)
        return block(block_reason(root))
    return allow()


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
        # Any unexpected failure must let the session stop.
        return allow()


if __name__ == "__main__":
    sys.exit(main())
