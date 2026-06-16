"""Build narrow Spill helper permission command variants."""

from __future__ import annotations

from pathlib import Path

SPILL_HELPER_NAMES = (
    "spill-token-metering-setup.mjs",
    "spill-token-metering-stats.mjs",
)
SPILL_HELPER_RELATIVE_DIR = "Library/Application Support/Spill/adapters/setup"


def spill_helper_permission_commands(tool: str, *, home: Path | None = None) -> list[str]:
    commands: list[str] = []
    for helper in SPILL_HELPER_NAMES:
        flag = "--label" if helper.endswith("setup.mjs") else "--tool"
        for path in spill_helper_path_variants(helper, home=home):
            commands.append(f"node {path} {flag} {tool}")
    return _dedupe(commands)


def spill_helper_path_variants(helper: str, *, home: Path | None = None) -> list[str]:
    home_path = home or Path.home()
    bases = (
        str(home_path),
        "~",
        "$HOME",
        "${HOME}",
    )

    variants: list[str] = []
    for base in bases:
        path = f"{base}/{SPILL_HELPER_RELATIVE_DIR}/{helper}"
        variants.extend(_shell_path_spellings(path))
    return _dedupe(variants)


def _shell_path_spellings(path: str) -> list[str]:
    escaped = path.replace("Application Support", "Application\\ Support")
    return [
        path,
        escaped,
        _quote(path),
        _double_quote(path),
    ]


def _quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _double_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
