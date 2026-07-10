"""Automatic workflow gates for work-producing routes."""

from __future__ import annotations


WORK_PRODUCING_COMMANDS = {
    "build",
    "bugfix",
    "code-simplify",
    "docs",
    "feature",
    "product",
    "prd",
    "refactor",
    "release",
    "ship",
    "spec",
    "task",
    "workflow-setup",
}
AGENTIC_RUN_STATE_COMMANDS = WORK_PRODUCING_COMMANDS | {
    "multi-agent",
}
ROUTE_DOCS_READ_COMMANDS = WORK_PRODUCING_COMMANDS | {
    "ambiguity",
    "commit",
    "git_commit",
    "docs",
    "docs-review",
    "multi-agent",
    "plan",
    "prd",
    "release",
    "retrospective",
    "review",
    "spec",
    "test",
    "triage",
    "webperf",
}
CODE_WORK_COMMANDS = {
    "build",
    "bugfix",
    "code-simplify",
    "feature",
    "product",
    "refactor",
    "task",
    "workflow-setup",
}
ALIGNMENT_BRIEF_COMMANDS = {
    "ambiguity",
    "build",
    "bugfix",
    "code-simplify",
    "docs",
    "feature",
    "multi-agent",
    "plan",
    "planning",
    "prd",
    "product",
    "refactor",
    "release",
    "ship",
    "spec",
    "task",
    "test",
    "triage",
    "webperf",
    "workflow-setup",
}

AMBIGUITY_GATE = "ambiguity check"
ROUTE_DOCS_READ_GATE = "route docs read"
ALIGNMENT_BRIEF_GATE = "alignment brief"
DOCUMENTATION_IMPACT_GATE = "documentation impact"
DOCUMENTATION_GATE = "documentation"
TEST_GATE = "tests"
CYCLE_CONTRACT_GATE = "cycle contract"
BOUNDARY_PLAN_GATE = "boundary plan"
MULTI_AGENT_GATE = "multi-agent split decision"
SIDE_EFFECT_AUDIT_GATE = "side-effect audit"
AGENTIC_RUN_STATE_GATE = "agentic run state"
SOURCE_DOCS_GATE = "source docs"

SOURCE_DOCS_COMMANDS = {
    "build",
    "bugfix",
    "code-simplify",
    "docs",
    "feature",
    "product",
    "prd",
    "refactor",
    "release",
    "ship",
    "spec",
    "task",
    "workflow-setup",
}


def automatic_gates(command: str) -> list[str]:
    gates: list[str] = []
    if command in ROUTE_DOCS_READ_COMMANDS:
        gates.append(ROUTE_DOCS_READ_GATE)
    if command in SOURCE_DOCS_COMMANDS:
        gates.append(SOURCE_DOCS_GATE)
    if command in WORK_PRODUCING_COMMANDS:
        gates.extend([AMBIGUITY_GATE, DOCUMENTATION_IMPACT_GATE])
    if command in ALIGNMENT_BRIEF_COMMANDS:
        gates.append(ALIGNMENT_BRIEF_GATE)
    if command in AGENTIC_RUN_STATE_COMMANDS:
        gates.append(AGENTIC_RUN_STATE_GATE)
    if command in WORK_PRODUCING_COMMANDS:
        gates.extend([CYCLE_CONTRACT_GATE, DOCUMENTATION_GATE])
    if command in CODE_WORK_COMMANDS:
        gates.extend(
            [TEST_GATE, BOUNDARY_PLAN_GATE, MULTI_AGENT_GATE, SIDE_EFFECT_AUDIT_GATE]
        )
    return gates


def automatic_docs(command: str) -> list[str]:
    docs: list[str] = []
    gates = set(automatic_gates(command))
    if command in {"commit", "git_commit"}:
        return docs
    if AMBIGUITY_GATE in gates:
        docs.append("workflows/skills/ambiguity-gate/SKILL.md")
    if ALIGNMENT_BRIEF_GATE in gates:
        docs.extend(
            [
                "common/skills/task-intake-effort-routing/SKILL.md",
                "common/skills/product-spec-to-implementation/SKILL.md",
            ]
        )
        if command in {"prd", "product", "spec"}:
            docs.append("workflows/skills/prd-creation/SKILL.md")
    if DOCUMENTATION_GATE in gates or DOCUMENTATION_IMPACT_GATE in gates:
        docs.append("workflows/skills/documentation-update/SKILL.md")
    if CYCLE_CONTRACT_GATE in gates:
        docs.append("workflows/skills/cycle-contract/SKILL.md")
    if SOURCE_DOCS_GATE in gates:
        docs.extend(
            [
                "common/skills/product-spec-to-implementation/SKILL.md",
                "common/skills/source-driven-development/SKILL.md",
            ]
        )
    if TEST_GATE in gates:
        docs.extend(
            [
                "common/skills/testing/SKILL.md",
                "common/skills/scenario-driven-testing/SKILL.md",
                "common/skills/verification-policy/SKILL.md",
            ]
        )
    if BOUNDARY_PLAN_GATE in gates:
        docs.append("common/skills/code-structure-ownership/SKILL.md")
    if MULTI_AGENT_GATE in gates:
        docs.append("workflows/skills/multi-agent-collaboration/SKILL.md")
    if SIDE_EFFECT_AUDIT_GATE in gates:
        docs.append("workflows/skills/development-cycle/SKILL.md")
    if AGENTIC_RUN_STATE_GATE in gates:
        docs.extend(
            [
                "workflows/skills/agent-task-lifecycle/SKILL.md",
                "workflows/skills/scripted-agent-workflow/SKILL.md",
            ]
        )
    return docs


def add_automatic_gates(command: str, gates: list[str]) -> list[str]:
    result = list(gates)
    before_implementation = (
        "act",
        "implementation",
        "code work",
        "fix",
        "small refactor",
        "install or repair",
    )
    for gate in automatic_gates(command):
        if gate in result:
            continue
        if gate == ROUTE_DOCS_READ_GATE:
            if "orient" in result:
                _insert_after_any(result, gate, anchors=("orient",))
            else:
                result.insert(0, gate)
        elif gate == SOURCE_DOCS_GATE:
            _insert_after_any(
                result,
                gate,
                anchors=(ROUTE_DOCS_READ_GATE, "orient"),
            )
        elif gate == AMBIGUITY_GATE:
            _insert_after_any(
                result,
                gate,
                anchors=(SOURCE_DOCS_GATE, ROUTE_DOCS_READ_GATE, "orient", "PRD/ARD applicability", "reproduce"),
            )
        elif gate == DOCUMENTATION_IMPACT_GATE:
            _insert_after_any(
                result,
                gate,
                anchors=(SOURCE_DOCS_GATE, ROUTE_DOCS_READ_GATE, "orient"),
            )
        elif gate == ALIGNMENT_BRIEF_GATE:
            _insert_before_any(
                result,
                gate,
                anchors=(
                    "PRD/ARD applicability",
                    "PRD",
                    "PRD draft",
                    "ARD",
                    "acceptance criteria",
                    "scope",
                    "act",
                    "implementation",
                    "code work",
                    "fix",
                    "baseline",
                    "measure",
                    "test scope",
                    "run checks",
                    "simplification plan",
                    "small refactor",
                    "edit",
                    "install or repair",
                    "sources",
                    "options",
                    "recommendation",
                    "roles",
                    "write scopes",
                    "agent briefs",
                    "package",
                    "config",
                    "grill-me if needed",
                    "question drill if needed",
                    "route recommendation",
                    "ask blockers",
                    "record assumptions",
                ),
            )
        elif gate == AGENTIC_RUN_STATE_GATE:
            _insert_after_any(
                result,
                gate,
                anchors=(ALIGNMENT_BRIEF_GATE, AMBIGUITY_GATE, ROUTE_DOCS_READ_GATE, "orient"),
            )
        elif gate == CYCLE_CONTRACT_GATE:
            _insert_before_any(result, gate, anchors=before_implementation)
        elif gate == BOUNDARY_PLAN_GATE:
            _insert_before_any(result, gate, anchors=before_implementation)
        elif gate == MULTI_AGENT_GATE:
            _insert_before_any(result, gate, anchors=before_implementation)
        elif gate == SIDE_EFFECT_AUDIT_GATE:
            _insert_before_any(result, gate, anchors=("verify", "verification", "handoff", "commit readiness"))
        elif gate in {DOCUMENTATION_GATE, TEST_GATE}:
            _insert_before_any(result, gate, anchors=("verify", "verification", "handoff", "commit readiness"))
        else:
            result.append(gate)
    return result


def _insert_after_any(gates: list[str], gate: str, anchors: tuple[str, ...]) -> None:
    for anchor in anchors:
        if anchor in gates:
            gates.insert(gates.index(anchor) + 1, gate)
            return
    gates.insert(0, gate)


def _insert_before_any(gates: list[str], gate: str, anchors: tuple[str, ...]) -> None:
    for anchor in anchors:
        if anchor in gates:
            gates.insert(gates.index(anchor), gate)
            return
    gates.append(gate)
