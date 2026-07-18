"""Filesystem discovery, cleanup, and indexing for lesson records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_execution_capsule_state import atomic_write_json
from agent_state_lock import state_lock


SCHEMA_VERSION = 1


def existing_candidates(
    root: Path, lesson_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Path]]:
    """Return inbox records, promoted records, and removable inbox paths."""

    inbox_records, inbox_paths = _read_lesson_records(root / "lessons" / "inbox", lesson_id)
    promoted_records, _ = _read_lesson_records(root / "lessons" / "promoted", lesson_id)
    return inbox_records, promoted_records, inbox_paths


def remove_duplicate_candidates(keep: Path | None, paths: list[Path]) -> None:
    for path in paths:
        if keep is not None and path == keep:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue


def update_index(root: Path, relative_path: Path, lesson: dict[str, Any]) -> None:
    path = root / "index.json"
    with state_lock(path):
        try:
            index = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = {"schema_version": SCHEMA_VERSION, "lessons": []}
        entry = {
            "lesson_id": lesson["lesson_id"],
            "status": lesson["status"],
            "failure_type": lesson["failure_type"],
            "root_cause": lesson["root_cause"],
            "promotion_status": lesson["promotion_status"],
            "relative_path": str(relative_path),
        }
        lessons = [
            item
            for item in index.get("lessons", [])
            if item.get("lesson_id") != lesson["lesson_id"]
        ]
        lessons.append(entry)
        atomic_write_json(
            path,
            {
                "schema_version": SCHEMA_VERSION,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "lessons": lessons[-100:],
            },
        )


def _read_lesson_records(
    directory: Path, lesson_id: str
) -> tuple[list[dict[str, Any]], list[Path]]:
    paths = sorted({*directory.glob(f"*-{lesson_id}.json"), directory / f"{lesson_id}.json"})
    records: list[dict[str, Any]] = []
    existing_paths: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("lesson_id") == lesson_id:
            records.append(payload)
            existing_paths.append(path)
    return records, existing_paths
