"""Streaming Git worktree fingerprints for execution-capsule bindings."""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from pathlib import Path
from typing import Any, Iterator


def git_output(path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=path,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"cannot capture git state for execution capsule: git {args[0]} failed"
        )
    return completed.stdout.decode("utf-8")


def worktree_fingerprint(path: Path) -> str:
    """Hash tracked and untracked state without persisting paths or contents."""

    digest = hashlib.sha256()
    components = (
        (b"status", ("status", "--porcelain=v2", "-z", "--untracked-files=all")),
        (b"staged", ("diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv")),
        (b"unstaged", ("diff", "--binary", "--no-ext-diff", "--no-textconv")),
    )
    for label, command in components:
        _hash_git_component(digest, label, path, *command)

    for relative_bytes in _git_null_records(
        path, "ls-files", "--others", "--exclude-standard", "-z"
    ):
        candidate = path / Path(os.fsdecode(relative_bytes))
        _hash_component(digest, b"untracked-path", relative_bytes)
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            # A file can vanish after `git ls-files` emitted its snapshot.
            # Hash the race instead of crashing or reusing stale state.
            _hash_component(digest, b"untracked-raced", relative_bytes)
            continue
        _hash_component(
            digest,
            b"untracked-mode",
            str(stat.S_IMODE(metadata.st_mode)).encode("ascii"),
        )
        if stat.S_ISLNK(metadata.st_mode):
            _hash_component(
                digest,
                b"untracked-content",
                os.fsencode(os.readlink(candidate)),
            )
        elif stat.S_ISREG(metadata.st_mode):
            _hash_file_component(digest, b"untracked-content", candidate)
        else:
            _hash_component(
                digest,
                b"untracked-content",
                str(metadata.st_mode).encode("ascii"),
            )
    return digest.hexdigest()


def _hash_git_component(
    digest: Any,
    label: bytes,
    path: Path,
    *args: str,
) -> None:
    with subprocess.Popen(
        ["git", *args],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ) as process:
        assert process.stdout is not None
        nested = hashlib.sha256()
        size = 0
        while chunk := process.stdout.read(1024 * 1024):
            nested.update(chunk)
            size += len(chunk)
        if process.wait() != 0:
            raise RuntimeError(
                f"cannot capture git state for execution capsule: git {args[0]} failed"
            )
    _hash_stream_digest(digest, label, size, nested.digest())


def _git_null_records(path: Path, *args: str) -> Iterator[bytes]:
    with subprocess.Popen(
        ["git", *args],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ) as process:
        assert process.stdout is not None
        buffer = b""
        while chunk := process.stdout.read(64 * 1024):
            buffer += chunk
            records = buffer.split(b"\0")
            buffer = records.pop()
            yield from (record for record in records if record)
        if buffer:
            yield buffer
        if process.wait() != 0:
            raise RuntimeError(
                f"cannot capture git state for execution capsule: git {args[0]} failed"
            )


def _hash_file_component(digest: Any, label: bytes, path: Path) -> None:
    nested = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            nested.update(chunk)
            size += len(chunk)
    _hash_stream_digest(digest, label, size, nested.digest())


def _hash_stream_digest(
    digest: Any,
    label: bytes,
    size: int,
    content_digest: bytes,
) -> None:
    _hash_component(digest, label + b"-size", str(size).encode("ascii"))
    _hash_component(digest, label + b"-sha256", content_digest)


def _hash_component(digest: Any, label: bytes, payload: bytes) -> None:
    digest.update(len(label).to_bytes(4, "big"))
    digest.update(label)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
