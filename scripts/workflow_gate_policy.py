"""Automatic workflow gates for work-producing routes."""

from __future__ import annotations


WORK_PRODUCING_COMMANDS = {
    "bugfix",
    "feature",
    "product",
    "refactor",
    "release",
    "task",
    "workflow-setup",
}
CODE_WORK_COMMANDS = {
    "bugfix",
    "feature",
    "product",
    "refactor",
    "task",
    "workflow-setup",
}

AMBIGUITY_GATE = "ambiguity check"
DOCUMENTATION_GATE = "documentation"
TEST_GATE = "tests"
MULTI_AGENT_GATE = "multi-agent split decision"


def automatic_gates(command: str) -> list[str]:
    gates: list[str] = []
    if command in WORK_PRODUCING_COMMANDS:
        gates.extend([AMBIGUITY_GATE, DOCUMENTATION_GATE])
    if command in CODE_WORK_COMMANDS:
        gates.extend([TEST_GATE, MULTI_AGENT_GATE])
    return gates


def automatic_docs(command: str) -> list[str]:
    docs: list[str] = []
    gates = set(automatic_gates(command))
    if AMBIGUITY_GATE in gates:
        docs.append("workflows/ambiguity-gate.md")
    if DOCUMENTATION_GATE in gates:
        docs.append("workflows/documentation-update.md")
    if TEST_GATE in gates:
        docs.extend(["common/testing.md", "common/verification-policy.md"])
    if MULTI_AGENT_GATE in gates:
        docs.append("workflows/multi-agent-collaboration.md")
    return docs


def add_automatic_gates(command: str, gates: list[str]) -> list[str]:
    result = list(gates)
    for gate in automatic_gates(command):
        if gate in result:
            continue
        if gate == AMBIGUITY_GATE:
            _insert_after_any(result, gate, anchors=("orient", "PRD/ARD applicability", "reproduce"))
        elif gate == MULTI_AGENT_GATE:
            _insert_before_any(result, gate, anchors=("act", "implementation", "code work", "fix", "small refactor", "install or repair"))
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
