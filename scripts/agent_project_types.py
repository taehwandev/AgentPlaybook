"""Types and formatting helpers for AgentPlaybook project discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from workflow_common import unique


DiscoveryStatus = Literal["selected", "ambiguous", "not_found"]

INSTRUCTION_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    ".agents/README.md",
    "CONTRIBUTING.md",
)

PROJECT_MARKERS = (
    ".git",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Package.swift",
    "settings.gradle",
    "settings.gradle.kts",
    "build.gradle",
    "build.gradle.kts",
    "pom.xml",
    "mix.exs",
)


@dataclass
class ProjectCandidate:
    path: Path
    confidence: int
    reasons: list[str] = field(default_factory=list)
    instruction_files: list[str] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

    def merge(self, other: "ProjectCandidate") -> None:
        self.confidence = max(self.confidence, other.confidence)
        self.reasons = unique([*self.reasons, *other.reasons])
        self.instruction_files = unique([*self.instruction_files, *other.instruction_files])
        self.markers = unique([*self.markers, *other.markers])
        self.sources = unique([*self.sources, *other.sources])
        self.aliases = unique([*self.aliases, *other.aliases])

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "confidence": self.confidence,
            "reasons": self.reasons,
            "instruction_files": self.instruction_files,
            "markers": self.markers,
            "sources": self.sources,
            "aliases": self.aliases,
        }


@dataclass
class DiscoveryResult:
    status: DiscoveryStatus
    candidates: list[ProjectCandidate]
    selected: ProjectCandidate | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "selected_project": self.selected.to_dict() if self.selected else None,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def format_discovery_text(result: DiscoveryResult) -> str:
    if result.status == "selected" and result.selected:
        lines = ["status: selected", f"project: {result.selected.path}"]
        if result.selected.instruction_files:
            lines.append("instruction_files:")
            lines.extend(f"- {item}" for item in result.selected.instruction_files)
        return "\n".join(lines)

    lines = [f"status: {result.status}"]
    if result.candidates:
        lines.append("candidates:")
        for candidate in result.candidates:
            lines.append(f"- {candidate.path} ({candidate.confidence})")
            if candidate.reasons:
                lines.append(f"  reason: {', '.join(candidate.reasons)}")
            if candidate.instruction_files:
                lines.append(f"  instruction_files: {', '.join(candidate.instruction_files)}")
    return "\n".join(lines)


def format_entry_text(manifest: dict[str, object]) -> str:
    lines = [f"status: {manifest['status']}", f"runtime: {manifest['runtime']}"]
    selected = manifest.get("selected_project")
    if isinstance(selected, dict):
        lines.append(f"project: {selected['path']}")
        instruction_files = selected.get("instruction_files")
        if isinstance(instruction_files, list) and instruction_files:
            lines.append("instruction_files:")
            lines.extend(f"- {item}" for item in instruction_files)
    elif manifest.get("candidates"):
        lines.append("candidates:")
        candidates = manifest["candidates"]
        if isinstance(candidates, list):
            for candidate in candidates:
                if isinstance(candidate, dict):
                    lines.append(f"- {candidate['path']} ({candidate['confidence']})")

    next_steps = manifest.get("next_steps", [])
    if isinstance(next_steps, list) and next_steps:
        lines.append("next_steps:")
        lines.extend(f"- {step}" for step in next_steps)
    workflow_command = manifest.get("workflow_command")
    if workflow_command:
        lines.append(f"workflow_command: {workflow_command}")
    return "\n".join(lines)
