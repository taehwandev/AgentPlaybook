#!/usr/bin/env python3
"""Claude Code PreToolUse gate for AgentPlaybook.

This gate enforces two things a purely advisory bridge cannot, at the only point
that actually stops the model -- the moment it calls an edit tool:

1. Workflow entry. Nothing otherwise stops a file edit when the agent skipped the
   ``start`` hook, so the workflow is easy to ignore. The gate denies a file-edit
   tool call when an AgentPlaybook project has no fresh preflight evidence, which
   forces ``start`` (route + preflight) before mutating files.
2. Structural proportionality. Skill docs and the post-hoc review gate cannot
   stop a task from ballooning into many new files/layers -- by review time the
   tokens and analysis are already spent. This gate counts new source files a
   session creates and denies the one past the budget, so sprawl has to be
   collapsed or justified per file before more files are written. A recorded
   justification (the ack file) unlocks the rest of the session; the gate never
   hard-bricks and always fails open.

Contract (Claude Code PreToolUse hook):
- Reads a JSON payload from stdin with ``tool_name``, ``cwd``, ``session_id``,
  and ``tool_input`` (``file_path`` for Write).
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
# Only Write creates a file from nothing; Edit/MultiEdit require an existing
# file, so new-file sprawl flows through Write.
NEW_FILE_TOOLS = {"Write"}
STATE_DIR = ".agentplaybook"
PREFLIGHT_NAME = "preflight.json"
SESSION_MARKER_DIR = "claude-pretool-gate"
NEW_FILE_STATE_SUFFIX = ".newfiles"
SPRAWL_ACK_SUFFIX = ".sprawl-ack"
OPT_IN_FILES = ("AGENTS.md", "CLAUDE.md", "CODEX.md")
OPT_IN_TOKEN = "agentplaybook"
DEFAULT_MAX_AGE_SECONDS = 8 * 60 * 60
MAX_ROOT_WALK = 40
# New source files past this count in one session must be collapsed or justified.
# Matches the review-time signal in
# agent_review_structure.REVIEW_NEW_SOURCE_FILE_PRESSURE_LIMIT. Only code source
# files count, so doc/content work (e.g. a writing workspace full of .md drafts)
# is never blocked.
DEFAULT_NEW_FILE_BUDGET = 5
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".cjs", ".dart", ".go", ".h", ".hpp",
    ".java", ".js", ".jsx", ".kt", ".kts", ".m", ".mjs", ".mm", ".php", ".py",
    ".rb", ".rs", ".sass", ".scss", ".svelte", ".swift", ".ts", ".tsx", ".vue",
}


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


def workflow_entry_allows(root: Path, session_id: str) -> bool:
    """Gate 1: the workflow ``start`` hook must have run this session."""
    marker = session_marker(root, session_id)
    if marker.exists():
        return True
    if evidence_is_fresh(root):
        touch_marker(marker)
        return True
    return False


def new_file_budget() -> int:
    raw = os.environ.get("AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET", "").strip()
    if not raw:
        return DEFAULT_NEW_FILE_BUDGET
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_NEW_FILE_BUDGET
    return value if value >= 0 else DEFAULT_NEW_FILE_BUDGET


def write_target_path(payload: dict, cwd: Path) -> Path | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("file_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    target = Path(raw)
    if not target.is_absolute():
        target = cwd / target
    return target


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def sprawl_state_file(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / (safe_session_id(session_id) + NEW_FILE_STATE_SUFFIX)


def sprawl_ack_file(root: Path, session_id: str) -> Path:
    return root / STATE_DIR / SESSION_MARKER_DIR / (safe_session_id(session_id) + SPRAWL_ACK_SUFFIX)


def read_new_files(state: Path) -> list[str]:
    try:
        text = state.read_text(encoding="utf-8")
    except OSError:
        return []
    return [line for line in text.splitlines() if line.strip()]


def record_new_file(state: Path, key: str) -> None:
    try:
        state.parent.mkdir(parents=True, exist_ok=True)
        with state.open("a", encoding="utf-8") as handle:
            handle.write(key + "\n")
    except OSError:
        pass


def sprawl_deny_reason(count: int, budget: int, ack: Path, target: Path, root: Path) -> str:
    return (
        f"AgentPlaybook proportionality gate: this task has already created {count} new "
        f"source file(s) in {root.name} (budget {budget}); creating {target.name} would exceed "
        "it. Turning a task into many files, layers, or abstractions burns tokens and review "
        "time. Collapse the change into fewer files, or -- if each new file protects a concrete "
        f"present risk -- record the per-file justification by writing it to {ack}, then retry. "
        "Tune with AGENTPLAYBOOK_CLAUDE_GATE_NEW_FILE_BUDGET."
    )


def sprawl_deny(tool: str, payload: dict, root: Path, cwd: Path, session_id: str) -> str | None:
    """Gate 2: deny the new source file that pushes a task past its budget."""
    if tool not in NEW_FILE_TOOLS:
        return None
    budget = new_file_budget()
    if budget <= 0:
        return None
    try:
        target = write_target_path(payload, cwd)
        if target is None or target.exists():
            # No path, or editing/overwriting an existing file -- not new-file sprawl.
            return None
        if STATE_DIR in target.parts:
            return None  # agent state (including the ack file itself) never counts
        if not is_relative_to(target, root):
            return None  # outside the project
        if target.suffix.lower() not in SOURCE_SUFFIXES:
            return None  # docs/config/content are not code sprawl

        state = sprawl_state_file(root, session_id)
        recorded = read_new_files(state)
        key = str(target)
        if sprawl_ack_file(root, session_id).exists():
            if key not in recorded:
                record_new_file(state, key)
            return None
        if key in recorded:
            return None  # idempotent retry of an already-counted file
        if len(recorded) + 1 > budget:
            return sprawl_deny_reason(len(recorded), budget, sprawl_ack_file(root, session_id), target, root)
        record_new_file(state, key)
        return None
    except Exception:
        return None


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
    if not workflow_entry_allows(root, session_id):
        return deny(deny_reason(root))
    sprawl_reason = sprawl_deny(tool, payload, root, cwd, session_id)
    if sprawl_reason:
        return deny(sprawl_reason)
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
        # Any unexpected failure must fail open.
        return allow()


if __name__ == "__main__":
    sys.exit(main())
