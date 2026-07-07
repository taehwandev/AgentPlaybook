"""Antigravity/AGY runtime bridge and permission setup."""

from __future__ import annotations

from pathlib import Path

from support.permission_entries import agy_legacy_permission_entries, agy_permission_entries
from support.runtime_bridge import (
    RUNTIME_BRIDGE_BEGIN,
    RUNTIME_BRIDGE_END,
    merge_runtime_bridge,
    runtime_bridge_block,
    runtime_bridge_required_phrases,
)
from support.setup_config_files import merge_permissions_allow

AGY_RUNTIME_BRIDGE_PATH = Path.home() / ".antigravity" / "AGENTS.md"
AGY_RUNTIME_BRIDGE_BEGIN = RUNTIME_BRIDGE_BEGIN
AGY_RUNTIME_BRIDGE_END = RUNTIME_BRIDGE_END
AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES = runtime_bridge_required_phrases("Antigravity", "AGENTS.md")


def configure_agy(
    dry_run: bool,
    *,
    root: Path,
    scripts_dir: Path,
    spill_available: bool = True,
) -> list[dict]:
    results = []
    status = _merge_agy_runtime_bridge(AGY_RUNTIME_BRIDGE_PATH, dry_run, root=root)
    results.append({
        "tool": "agy",
        "hook": "runtime_bridge.AGENTS",
        "status": status,
        "path": str(AGY_RUNTIME_BRIDGE_PATH),
    })

    entries = agy_permission_entries(scripts_dir, spill_available=spill_available)
    cleanup_entries = agy_legacy_permission_entries(scripts_dir)
    if not spill_available:
        cleanup_entries += agy_permission_entries(scripts_dir, spill_available=True)
    targets = [
        Path.home() / ".gemini" / "antigravity-cli" / "settings.json",
        Path.home() / ".gemini" / "config" / "config.json",
    ]

    for target in targets:
        status = merge_permissions_allow(
            target,
            entries,
            dry_run,
            cleanup_entries=cleanup_entries,
        )
        results.append({
            "tool": "agy",
            "hook": "permissions.AgentPlaybookPython",
            "status": status,
            "path": str(target),
        })

    hooks_path = Path.home() / ".gemini" / "config" / "hooks.json"
    status = "ok" if hooks_path.exists() else "ok (no hooks file; permissions use config.json/settings.json)"
    results.append({
        "tool": "agy",
        "hook": "config.hooks",
        "status": status,
        "path": str(hooks_path),
    })
    return results


def _merge_agy_runtime_bridge(target: Path, dry_run: bool, *, root: Path) -> str:
    return merge_runtime_bridge(
        target,
        dry_run,
        block=_agy_runtime_bridge_block(root),
        required_phrases=AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES,
    )


def _agy_runtime_bridge_block(root: Path) -> str:
    return runtime_bridge_block(root, "Antigravity", "AGENTS.md")
