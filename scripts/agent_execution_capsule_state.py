"""Content-free state and persistence primitives for execution capsules."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from agent_worktree_fingerprint import git_output, worktree_fingerprint


SCHEMA_VERSION = 2
CAPSULE_FILENAME = "execution-capsule.json"
REUSE_POLICY = {
    "condition": "ready_and_valid",
    "gate_effect": "none",
    "ledger_owner": "parent",
    "worker_may_skip": ["route", "preflight"],
    "worker_may_reuse": ["required-doc-manifest"],
}


def capsule_path_for_evidence(evidence_path: Path) -> Path:
    if evidence_path.name == "preflight.json":
        return evidence_path.parent / CAPSULE_FILENAME
    return evidence_path.parent / f"{evidence_path.stem}-{CAPSULE_FILENAME}"


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        return {"invalid_json": True}
    return payload if isinstance(payload, dict) else {"invalid_json": True}


def file_hash_record(path: Path) -> dict[str, str]:
    return {"filename": path.name, "sha256": sha256_file(path)}


def doc_hash_record(relative: str, path: Path) -> dict[str, Any]:
    digest, size = _sha256_and_size(path)
    return {
        "path": relative,
        "size_bytes": size,
        "sha256": digest,
    }


def contained_doc_path(rules: Path, relative: str) -> Path:
    candidate = (rules / relative).resolve()
    try:
        candidate.relative_to(rules)
    except ValueError as error:
        raise ValueError(f"required doc escapes rules root: {relative}") from error
    return candidate


def git_state(path: Path) -> dict[str, str]:
    head = git_output(path, "rev-parse", "--verify", "HEAD").strip()
    return {
        "head": head,
        "worktree_fingerprint": worktree_fingerprint(path),
    }


def sha256_file(path: Path) -> str:
    return _sha256_and_size(path)[0]


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def execution_capsule_binding_fingerprint(capsule: dict[str, Any]) -> str | None:
    """Return the stable route/doc identity that gate evidence may reference.

    A finish check runs after implementation, so mutable worktree and ledger
    hashes cannot participate in an evidence binding.  This deliberately uses
    only the preflight, route, and required-document snapshot captured before
    work began.
    """

    required = (
        "schema_version",
        "phase",
        "route_fingerprint",
        "preflight_evidence",
        "required_docs",
        "reuse_policy",
    )
    if any(field not in capsule for field in required):
        return None
    if capsule.get("phase") != "ready":
        return None
    payload = {field: capsule[field] for field in required}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(path.parent, directory_flags)
    temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        file_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        try:
            with os.fdopen(file_fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
            raise
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
    finally:
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except OSError:
            pass
        os.close(directory_fd)


def _sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size
