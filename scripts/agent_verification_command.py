"""Allowlisted commands and contained targets for structural verification."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


UNITTEST_SELECTOR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,200}$")
VERIFICATION_KINDS = {
    "py_compile",
    "unittest",
    "vibeguard",
    "workflow_validate",
}
Runner = Callable[[list[str], Path], dict[str, Any]]


def resolve_verification_target(
    project: Path, rules: Path, target: str
) -> tuple[Path, str, str, Path] | None:
    raw = Path(target.strip()).expanduser()
    candidates = [raw] if raw.is_absolute() else [project / raw, rules / raw]
    # Prefer rules when both names resolve to one checkout. Skill maintenance
    # is specifically allowed to change canonical Tao Agent OS files.
    roots = (("rules", rules.resolve()), ("project", project.resolve()))
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not resolved.is_file():
            continue
        for scope, root in roots:
            try:
                relative = resolved.relative_to(root)
            except ValueError:
                continue
            return resolved, scope, relative.as_posix(), root
    return None


def verification_target_is_changed(root: Path, target: Path) -> bool:
    try:
        relative = target.relative_to(root)
    except ValueError:
        return False
    result = run_verification_command(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", relative.as_posix()],
        root,
    )
    return result["returncode"] == 0 and bool(str(result.get("stdout") or "").strip())


def verification_command(
    *,
    project: Path,
    rules: Path,
    target: Path,
    verification_kind: str,
    test_selector: str,
) -> list[str]:
    if verification_kind == "workflow_validate":
        script = rules / "scripts" / "workflow.py"
        return [sys.executable, str(script), "validate"] if script.is_file() else []
    if verification_kind == "unittest":
        return (
            [sys.executable, "-m", "unittest", test_selector]
            if UNITTEST_SELECTOR_RE.fullmatch(test_selector)
            else []
        )
    if verification_kind == "py_compile":
        return [sys.executable, "-m", "py_compile", str(target)] if target.suffix == ".py" else []
    if verification_kind == "vibeguard":
        binary = shutil.which("vibeguard")
        if binary:
            return [binary, "audit", str(project), "--rules", str(rules)]
        return ["npx", "--yes", "@taehwandev/vibeguard", "audit", str(project), "--rules", str(rules)]
    return []


def run_verification_command(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
