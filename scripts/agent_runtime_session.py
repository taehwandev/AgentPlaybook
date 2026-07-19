"""Identify the runtime session that produced a piece of lifecycle evidence.

Lifecycle evidence files live in the project and are shared by every runtime, so
their presence alone never proves what happened in the session reading them. The
Claude gates need that distinction: `start` must have run in *this* session
before edits, and `finish` must have run in *this* session before it ends.
Stamping the session into the evidence keeps the hooks that write it the only
producers of that proof, and leaves the gates read-only.

A runtime that exposes no session id records nothing. Gates treat that as "not
this session", which fails closed rather than silently accepting foreign
evidence.
"""

from __future__ import annotations

import os

SESSION_ENV_VARS = (("claude", "CLAUDE_CODE_SESSION_ID"),)


def runtime_session() -> dict[str, str]:
    for runtime, variable in SESSION_ENV_VARS:
        value = os.environ.get(variable, "").strip()
        if value:
            return {"runtime": runtime, "session_id": value}
    return {}


def recorded_session_id(payload: object) -> str:
    """Read back a session id stamped by `runtime_session()`."""
    if not isinstance(payload, dict):
        return ""
    session = payload.get("runtime_session")
    if not isinstance(session, dict):
        return ""
    recorded = session.get("session_id")
    return recorded if isinstance(recorded, str) else ""
