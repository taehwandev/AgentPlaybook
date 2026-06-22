"""Spill label helpers for AgentPlaybook preflight."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from workflow_spill import spill_tool_label


DEFAULT_SPILL_SETUP_HELPER = (
    Path.home()
    / "Library/Application Support/Spill/adapters/setup/spill-token-metering-setup.mjs"
)


def write_spill_label(task_type: str, stage: str) -> None:
    if not has_spill_setup_helper():
        return
    try:
        subprocess.run(
            [
                "node",
                str(spill_setup_helper_path()),
                "--label",
                spill_tool_label(),
                "--task-type",
                task_type,
                "--stage",
                stage,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def spill_setup_helper_path() -> Path:
    override = os.environ.get("AGENTPLAYBOOK_SPILL_HELPER_PATH", "")
    return Path(override) if override else DEFAULT_SPILL_SETUP_HELPER


def has_spill_setup_helper() -> bool:
    return spill_setup_helper_path().is_file()
