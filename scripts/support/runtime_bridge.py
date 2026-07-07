"""User-level runtime bridge helpers for AgentPlaybook setup."""

from __future__ import annotations

import re
from pathlib import Path

RUNTIME_BRIDGE_BEGIN = "<!-- agentplaybook-runtime-bridge:start -->"
RUNTIME_BRIDGE_END = "<!-- agentplaybook-runtime-bridge:end -->"

RUNTIME_BRIDGE_GRAPH_PHRASES = [
    "Before project work, run AgentPlaybook workflow routing with the user's current request; route/search owns natural-language document discovery.",
    "Do not wait for the user to name document keywords; infer the work surface from the request, platform, concern, and touched files, then read the route required_docs before editing or reviewing.",
    "Use workflow-doc-surfaces.json and the local document graph as routing/search inputs; treat graph neighbors as reference_docs unless the route marks them as required_docs.",
    "If routing/search misses a clearly relevant platform, concern, or document surface, stop and report the gap instead of proceeding from memory.",
]

RUNTIME_BRIDGE_COMMON_REQUIRED_PHRASES = [
    "Start every task by identifying the current project root.",
    "If the runtime starts outside the target repo or the target repo is not explicit, run AgentPlaybook agent-entry.py or project-discover.py before project work.",
    "If project discovery returns ambiguous or not_found, ask the user for the target project before routing, editing, testing, committing, or reporting completion.",
    "Before project work, open the project-root instruction file for the active runtime.",
    *RUNTIME_BRIDGE_GRAPH_PHRASES,
    "For multi-step work, run AgentPlaybook preflight before edits and finish-check before final report, commit, release, or handoff.",
    "Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
    "Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
]


def runtime_bridge_required_phrases(runtime_name: str, instruction_file: str) -> list[str]:
    return [
        f"{runtime_name} reads {instruction_file}.",
        *RUNTIME_BRIDGE_COMMON_REQUIRED_PHRASES,
        f"If this bridge or the project-root {instruction_file} cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
    ]


def runtime_bridge_block(root: Path, runtime_name: str, instruction_file: str) -> str:
    return "\n".join([
        RUNTIME_BRIDGE_BEGIN,
        "## AgentPlaybook Runtime Bridge",
        "",
        f"Apply this bridge before project work in {runtime_name} sessions.",
        "",
        f"- Shared AgentPlaybook root: `{root}`",
        "- Start every task by identifying the current project root.",
        "- If the runtime starts outside the target repo or the target repo is not explicit, run AgentPlaybook agent-entry.py or project-discover.py before project work.",
        "- If project discovery returns ambiguous or not_found, ask the user for the target project before routing, editing, testing, committing, or reporting completion.",
        "- Before project work, open the project-root instruction file for the active runtime.",
        f"- {runtime_name} reads {instruction_file}.",
        "- Read project-root instructions before AgentPlaybook shared guidance.",
        "- Before project work, run AgentPlaybook workflow routing with the user's current request; route/search owns natural-language document discovery.",
        "- Do not wait for the user to name document keywords; infer the work surface from the request, platform, concern, and touched files, then read the route required_docs before editing or reviewing.",
        "- Use workflow-doc-surfaces.json and the local document graph as routing/search inputs; treat graph neighbors as reference_docs unless the route marks them as required_docs.",
        "- If routing/search misses a clearly relevant platform, concern, or document surface, stop and report the gap instead of proceeding from memory.",
        "- For multi-step work, run AgentPlaybook preflight before edits and finish-check before final report, commit, release, or handoff.",
        f"- If this bridge or the project-root {instruction_file} cannot be confirmed before project work, stop before routing, editing, testing, committing, or reporting completion and ask for bridge repair.",
        "- Do not mention AgentPlaybook setup, hook, permission, helper, or label commands in normal conversation.",
        "- Do not report whether background labels, hooks, or metering ran unless the user explicitly asks about that subsystem.",
        "- If a response exposed those background details, do not answer with an apology-only message; continue by repairing the action path or stopping with the specific blocker.",
        RUNTIME_BRIDGE_END,
        "",
    ])


def merge_runtime_bridge(
    target: Path,
    dry_run: bool,
    *,
    block: str,
    required_phrases: list[str],
) -> str:
    text = target.read_text() if target.exists() else ""
    pattern = re.compile(
        re.escape(RUNTIME_BRIDGE_BEGIN)
        + r"[\s\S]*?"
        + re.escape(RUNTIME_BRIDGE_END)
        + r"\n?",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match:
        if match.group(0) == block:
            return "ok"
        if dry_run:
            return "missing"
        updated = pattern.sub(block, text)
    else:
        missing = [phrase for phrase in required_phrases if phrase not in text]
        if not missing:
            return "ok"
        if dry_run:
            return "missing"
        separator = "" if not text or text.endswith("\n") else "\n"
        updated = f"{text}{separator}{block}"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated)
    return "installed"
