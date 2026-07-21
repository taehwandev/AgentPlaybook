"""Tell the global Tao Agent OS install apart from per-project runtime state.

``.tao`` names two unrelated things:

- per-project runtime state -- ``<repo>/.tao/preflight.json``, gate evidence,
  session markers;
- the global install -- ``~/.tao/bin/tao-hook``, ``~/.tao/tao-root``,
  ``~/.tao/projects.json``, ``~/.tao/claude-session-projects/``.

Every "is this a Tao project?" check used to be ``(path / ".tao").is_dir()``,
so the home directory that hosts the global install always answered yes. That
made ``$HOME`` classify as a project, which let a harness path such as
``~/.claude/plans/x.md`` register ``$HOME`` as a session project and left the
Stop gate demanding a finish for ``$HOME`` -- a finish that cannot pass, because
auditing ``~`` dies on unreadable directories like ``~/.Trash``. An
unsatisfiable gate pushes the agent toward switching the gate off, so the
discriminator belongs here rather than in each gate.

The rule is the one the layout already implies: what is global stays global,
what is per-project stays per-project. A ``.tao`` directory is per-project state
exactly when it is not the global install directory.
"""

from __future__ import annotations

import os
from pathlib import Path


STATE_DIR_NAME = ".tao"
# Set by tests and by anyone relocating the global install; the same variable
# agent_global_lessons has always used to find lessons/skills state.
STATE_HOME_ENV = "TAO_STATE_HOME"
# Files the installer writes into the global directory and that no project's
# .tao ever contains. Identity is checked first; these are the fallback for a
# global install reached through a different HOME, a symlink, or a relocation
# that happened after this process read the environment.
GLOBAL_ONLY_MARKERS = ("tao-root", "projects.json", "bin/tao-hook")


def global_state_dir() -> Path:
    """The one directory that holds global install state."""
    override = os.environ.get(STATE_HOME_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / STATE_DIR_NAME


def _resolved(path: Path) -> Path | None:
    try:
        return path.resolve()
    except OSError:  # pragma: no cover - unreadable path
        return None


def is_global_state_dir(path: Path) -> bool:
    """True when this ``.tao`` directory is the global install, not project state."""
    resolved = _resolved(path)
    if resolved is None:
        return False
    global_resolved = _resolved(global_state_dir())
    if global_resolved is not None and resolved == global_resolved:
        return True
    return any((resolved / marker).exists() for marker in GLOBAL_ONLY_MARKERS)


def is_project_state_dir(path: Path) -> bool:
    """True when ``path`` is an existing ``.tao`` holding per-project state.

    Used by the opt-in checks in both Claude gates. Keeping it here stops the
    two gates from drifting into disagreeing about what a project is.
    """
    if not path.is_dir():
        return False
    return not is_global_state_dir(path)


def project_state_dir_target(project: Path) -> Path:
    """Where per-project state for ``project`` belongs."""
    return project / STATE_DIR_NAME


def project_scoped_state_error(project: Path) -> str:
    """Why ``project`` may not receive project-scoped state, or "" when it may.

    The distinction that matters is "new project, no state yet" versus "not a
    project at all". A fresh repo whose ``.tao`` does not exist must still be
    able to start, so absence of state is never the failure -- this only refuses
    a target whose ``.tao`` *is* the global install directory. That is the case
    that produced ``~/.tao/preflight.json``: project-scoped route state written
    into global state, which later gates then demanded a finish for.
    """
    state_dir = project_state_dir_target(project)
    if not is_global_state_dir(state_dir):
        return ""
    return (
        f"refusing to write project-scoped state to {state_dir}: that is the "
        "global Tao Agent OS install directory, not a project. Re-run with "
        "--project pointing at the repository you are working in."
    )
