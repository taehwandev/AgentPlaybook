"""Purpose-based file and package checks for the AgentPlaybook review hook."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any


PathPredicate = Callable[[Path, Path], bool]
TestPredicate = Callable[[Path], bool]

PYTHON_TOP_LEVEL_TYPE_RE = re.compile(r"^class\s+([A-Za-z_]\w*)\b")
BRACE_TOP_LEVEL_TYPE_RE = re.compile(
    r"^\s*"
    r"(?:(?:export\s+default\s+|export\s+|public\s+|private\s+|protected\s+|internal\s+|"
    r"open\s+|final\s+|sealed\s+|abstract\s+|data\s+|value\s+|inline\s+|static\s+|readonly\s+|"
    r"pub\s+|pub\(crate\)\s+)*)"
    r"(?:(?:enum\s+class|annotation\s+class|sealed\s+class|sealed\s+interface|data\s+class|"
    r"value\s+class)\s+|"
    r"(?P<kind>class|interface|enum|struct|record|object|protocol|actor|typealias|type|trait)\s+)"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b"
)
GO_TOP_LEVEL_TYPE_RE = re.compile(r"^\s*type\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+(?P<kind>struct|interface)\b")
TS_TYPE_ALIAS_RE = re.compile(r"^\s*(?:export\s+)?type\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=")
BRACE_TOP_LEVEL_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:export\s+default\s+|export\s+|public\s+|private\s+|protected\s+|"
    r"internal\s+|open\s+|final\s+|static\s+|pub\s+|pub\(crate\)\s+)*)"
    r"(?:async\s+)?(?P<kind>function|func|fun|fn)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b"
)
BRACE_TOP_LEVEL_CONST_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*="
    r"\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*=>"
)
TYPE_OWNER_KINDS = {"actor", "class", "enum", "interface", "object", "protocol", "record", "struct", "trait", "type", "typealias"}
MAX_TOP_LEVEL_OWNERS = 4
MAX_PUBLIC_TOP_LEVEL_OWNERS = 1
GENERIC_PACKAGE_PARTS = {"common", "commons", "helper", "helpers", "lib", "manager", "managers", "misc", "service", "services", "shared", "util", "utils"}
MIXED_ROLE_BLOCKS = (
    ("ui", "data"),
    ("ui", "domain"),
    ("ui", "platform"),
    ("state", "data"),
    ("state", "platform"),
    ("contract", "impl"),
    ("testing", "impl"),
)
ROLE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("state", ("viewmodel", "state", "uistate", "store", "reducer", "action", "effect", "presenter", "controller")),
    ("ui", ("screen", "view", "component", "widget", "page", "fragment", "activity", "cell", "row", "panel", "dialog", "sheet")),
    ("data", ("repository", "repo", "client", "datasource", "dao", "mapper", "serializer", "parser", "dto", "response", "request")),
    ("domain", ("usecase", "interactor", "policy", "rule", "entity", "aggregate", "valueobject", "domain")),
    ("platform", ("adapter", "bridge", "provider", "driver", "launcher", "notification", "webview", "intent", "filesystem", "keychain")),
    ("contract", ("contract", "api", "port", "protocol", "interface", "event", "command", "route", "spec")),
    ("testing", ("fixture", "fake", "spy", "mock", "stub", "assertion", "assertions", "subject", "matcher")),
    ("impl", ("impl", "implementation", "service", "manager", "handler", "worker", "job")),
)


def purpose_failures(
    project: Path,
    paths: list[Path],
    path_metadata: dict[str, dict[str, Any]],
    review_source_path: PathPredicate,
    test_exempt_path: TestPredicate,
) -> list[str]:
    failures: list[str] = []
    for path in paths:
        if test_exempt_path(path):
            continue
        try:
            lines = (project / path).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        failures.extend(top_level_declaration_failures(path, top_level_type_declarations(path, lines)))
    failures.extend(package_role_failures(project, paths, path_metadata, review_source_path, test_exempt_path))
    return failures


def top_level_type_declarations(path: Path, lines: list[str]) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    brace_depth = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if path.suffix.lower() == ".py":
            if line == line.lstrip(" "):
                match = PYTHON_TOP_LEVEL_TYPE_RE.match(line)
            else:
                match = None
        elif brace_depth == 0 and stripped and not stripped.startswith(("//", "/*", "*")):
            match = (
                BRACE_TOP_LEVEL_TYPE_RE.match(line)
                or GO_TOP_LEVEL_TYPE_RE.match(line)
                or TS_TYPE_ALIAS_RE.match(line)
                or BRACE_TOP_LEVEL_FUNCTION_RE.match(line)
                or BRACE_TOP_LEVEL_CONST_FUNCTION_RE.match(line)
            )
        else:
            match = None
        if match:
            declaration = type_declaration(match_kind(match), match_name(match), line, index)
            if declaration["owner"]:
                declarations.append(declaration)
        brace_depth = max(0, brace_depth + line.count("{") - line.count("}"))
    return declarations


def match_kind(match: re.Match[str]) -> str:
    return match.groupdict().get("kind") or "type"


def match_name(match: re.Match[str]) -> str:
    return match.groupdict().get("name") or match.group(1)


def type_declaration(kind: str, name: str, line: str, index: int) -> dict[str, Any]:
    return {
        "kind": kind,
        "name": name,
        "line": index + 1,
        "private": bool(re.search(r"\bprivate\b", line)) or name.startswith("_"),
        "exported": bool(re.search(r"\b(export|public|pub)\b", line)),
        "role": role_for_name(name),
        "owner": top_level_owner(kind, name, line),
    }


def top_level_owner(kind: str, name: str, line: str) -> bool:
    return (
        kind in TYPE_OWNER_KINDS
        or bool(re.search(r"\b(export|public|pub|internal)\b", line))
        or role_for_name(name) is not None
        or component_or_hook_name(name)
    )


def component_or_hook_name(name: str) -> bool:
    return bool(name[:1].isupper() or re.match(r"^use[A-Z]", name))


def top_level_declaration_failures(path: Path, declarations: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    visible = [declaration for declaration in declarations if not declaration["private"]]
    public = [declaration for declaration in visible if declaration["exported"] or exported_by_default(path)]
    if len(public) > MAX_PUBLIC_TOP_LEVEL_OWNERS:
        failures.append(
            f"{path} declares {len(public)} public/exported top-level owners ({format_declarations(public)}); "
            f"limit is {MAX_PUBLIC_TOP_LEVEL_OWNERS}; split runtime files so one file owns one "
            "public contract, component, handler, service, or implementation"
        )
    if len(declarations) > MAX_TOP_LEVEL_OWNERS:
        failures.append(
            f"{path} declares {len(declarations)} top-level owners ({format_declarations(declarations[:8])}); "
            f"limit is {MAX_TOP_LEVEL_OWNERS}; move separate contracts, state, data, platform, and helpers "
            "into purpose-named files"
        )
    roles = sorted({declaration["role"] for declaration in visible if declaration["role"]})
    if mixed_roles_blocked(roles):
        failures.append(
            f"{path} mixes top-level owner roles {', '.join(roles)} ({format_declarations(visible)}); "
            "split by purpose before approval"
        )
    return failures


def package_role_failures(
    project: Path,
    paths: list[Path],
    path_metadata: dict[str, dict[str, Any]],
    review_source_path: PathPredicate,
    test_exempt_path: TestPredicate,
) -> list[str]:
    failures: list[str] = []
    for parent in sorted({path.parent for path in paths if not test_exempt_path(path)}):
        changed = [path for path in paths if path.parent == parent and not test_exempt_path(path)]
        entries = package_role_entries(project, parent, review_source_path, test_exempt_path)
        roles = sorted({role for _, role in entries if role})
        if mixed_roles_blocked(roles) and package_is_being_grown(changed, path_metadata):
            failures.append(
                f"{parent} package mixes runtime roles {', '.join(roles)} ({format_role_entries(entries)}); "
                "do not keep growing a catch-all package. Move changed code into purpose-named packages "
                "or document and enforce a real boundary"
            )
        generic = [part for part in parent.parts if part.lower() in GENERIC_PACKAGE_PARTS]
        if generic and any(path_metadata.get(str(path), {}).get("status") == "A" for path in changed):
            failures.append(
                f"{parent} contains grab-bag package segment(s) {', '.join(sorted(set(generic)))} for new "
                "runtime source; choose a package name that states the purpose, owner, or contract"
            )
    return failures


def package_role_entries(
    project: Path,
    parent: Path,
    review_source_path: PathPredicate,
    test_exempt_path: TestPredicate,
) -> list[tuple[str, str | None]]:
    entries: list[tuple[str, str | None]] = []
    for child in sorted((project / parent).iterdir()):
        relative = parent / child.name
        if not child.is_file() or not review_source_path(project, relative) or test_exempt_path(relative):
            continue
        role = role_for_name(child.stem)
        if role is None:
            try:
                declarations = top_level_type_declarations(relative, child.read_text(encoding="utf-8").splitlines())
            except UnicodeDecodeError:
                declarations = []
            role = next((declaration["role"] for declaration in declarations if declaration["role"]), None)
        entries.append((child.name, role))
    return entries


def package_is_being_grown(paths: list[Path], path_metadata: dict[str, dict[str, Any]]) -> bool:
    return any(path_metadata.get(str(path), {}).get("status") == "A" or path_metadata.get(str(path), {}).get("additions", 0) > 0 for path in paths)


def exported_by_default(path: Path) -> bool:
    return path.suffix.lower() in {".java", ".kt", ".kts", ".swift", ".dart", ".cs", ".go", ".rs"}


def mixed_roles_blocked(roles: list[str]) -> bool:
    return any(left in set(roles) and right in set(roles) for left, right in MIXED_ROLE_BLOCKS)


def role_for_name(name: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    tokens = set(re.findall(r"[a-z0-9]+", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ").replace("-", " ").lower()))
    return next((role for role, patterns in ROLE_PATTERNS if any(pattern in tokens or (len(pattern) > 4 and pattern in normalized) for pattern in patterns)), None)


def format_declarations(declarations: list[dict[str, Any]]) -> str:
    return ", ".join(f"{declaration['name']}@{declaration['line']}" for declaration in declarations)


def format_role_entries(entries: list[tuple[str, str | None]]) -> str:
    visible = [f"{name}:{role}" for name, role in entries if role]
    return ", ".join(visible[:8]) + ("" if len(visible) <= 8 else f" ... (+{len(visible) - 8} more)")
