"""Opaque reservation markers for isolated worker evidence directories."""

from __future__ import annotations

import hmac
import os
import uuid
from pathlib import Path

from agent_gate_evidence import gate_evidence_path_for_preflight


RESERVATION_FILENAME = ".agentplaybook-reservation"
CLAIMED_FILENAME = ".agentplaybook-reservation-claimed"


def create_worker_reservation(worker_dir: Path) -> str:
    """Create a content-free reservation token in an already reserved directory."""

    token = uuid.uuid4().hex
    directory_fd = _open_directory(worker_dir)
    try:
        marker_fd = os.open(
            RESERVATION_FILENAME,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(marker_fd, "wb") as marker:
            marker.write((token + "\n").encode("ascii"))
            marker.flush()
            os.fsync(marker.fileno())
    finally:
        os.close(directory_fd)
    return token


def worker_reservation_matches(worker_dir: Path, token: str) -> bool:
    """Validate a handoff-issued marker without following directory/file symlinks."""

    if len(token) != 32 or any(character not in "0123456789abcdef" for character in token):
        return False
    try:
        directory_fd = _open_directory(worker_dir)
        try:
            marker_fd = os.open(
                RESERVATION_FILENAME,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            with os.fdopen(marker_fd, "rb") as marker:
                recorded = marker.read(64).decode("ascii").strip()
        finally:
            os.close(directory_fd)
    except (OSError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(recorded, token)


def claim_worker_reservation(worker_dir: Path, token: str) -> bool:
    """Atomically consume a valid reservation so only one worker can claim it."""

    if not worker_reservation_matches(worker_dir, token):
        return False
    try:
        directory_fd = _open_directory(worker_dir)
        try:
            os.rename(
                RESERVATION_FILENAME,
                CLAIMED_FILENAME,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            claimed_fd = os.open(
                CLAIMED_FILENAME,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            with os.fdopen(claimed_fd, "rb") as marker:
                recorded = marker.read(64).decode("ascii").strip()
            if not hmac.compare_digest(recorded, token):
                return False
            os.unlink(CLAIMED_FILENAME, dir_fd=directory_fd)
            return True
        finally:
            os.close(directory_fd)
    except (OSError, UnicodeDecodeError):
        return False


def isolated_worker_evidence(
    project: Path,
    parent_evidence: Path,
    requested: Path | None = None,
    *,
    lexical_project: Path | None = None,
    reserve: bool,
) -> Path:
    """Select or exclusively reserve a safe worker preflight path."""

    lexical_project = (lexical_project or project).expanduser().absolute()
    project = project.resolve()
    worker_root = project / ".agentplaybook" / "workers"
    lexical_worker_root = lexical_project / ".agentplaybook" / "workers"
    if worker_root.resolve() != worker_root:
        raise ValueError(
            "Fallback worker evidence root must not resolve through a symlink."
        )
    requested_path = (
        requested.expanduser().absolute()
        if requested
        else worker_root / uuid.uuid4().hex[:16] / "preflight.json"
    )
    try:
        try:
            relative = requested_path.relative_to(worker_root)
        except ValueError:
            relative = requested_path.relative_to(lexical_worker_root)
        selected = worker_root / relative
        selected.relative_to(project)
    except ValueError as error:
        raise ValueError(
            "Fallback worker evidence must stay under <project>/.agentplaybook/workers/."
        ) from error
    if len(relative.parts) != 2 or relative.parts[-1] != "preflight.json":
        raise ValueError(
            "Fallback worker evidence must use one opaque worker directory and preflight.json."
        )
    if selected == parent_evidence or (
        gate_evidence_path_for_preflight(selected)
        == gate_evidence_path_for_preflight(parent_evidence)
    ):
        raise ValueError(
            "Fallback worker evidence must not overlap parent evidence or ledger paths."
        )
    if reserve:
        worker_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if worker_root.resolve() != worker_root:
            raise ValueError(
                "Fallback worker evidence root must not resolve through a symlink."
            )
        try:
            selected.parent.mkdir(mode=0o700, exist_ok=False)
        except FileExistsError as error:
            raise ValueError(
                "Fallback worker evidence directory must be newly and exclusively reserved."
            ) from error
        if selected.parent.resolve() != selected.parent:
            raise ValueError(
                "Fallback worker evidence directory must not resolve through a symlink."
            )
    return selected


def reserve_isolated_worker_evidence(
    project: Path,
    parent_evidence: Path,
    requested: Path | None = None,
    *,
    lexical_project: Path | None = None,
) -> tuple[Path, Path, str]:
    """Reserve one worker directory and mint its matching single-use token."""

    preflight = isolated_worker_evidence(
        project,
        parent_evidence,
        requested,
        lexical_project=lexical_project,
        reserve=True,
    )
    return (
        preflight,
        gate_evidence_path_for_preflight(preflight),
        create_worker_reservation(preflight.parent),
    )


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    return os.open(path, flags)
