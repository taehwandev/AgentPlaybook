"""Parallel execution hints for workflow route manifests."""

from __future__ import annotations

from typing import Any

from workflow_gate_policy import (
    AGENTIC_RUN_STATE_GATE,
    ALIGNMENT_BRIEF_GATE,
    AMBIGUITY_GATE,
    BOUNDARY_PLAN_GATE,
    CODE_WORK_COMMANDS,
    CYCLE_CONTRACT_GATE,
    DOCUMENTATION_IMPACT_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    ROUTE_DOCS_READ_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    SOURCE_DOCS_GATE,
    TEST_GATE,
)


def parallel_execution_plan(command: str, gates: list[str]) -> dict[str, Any]:
    """Return safe, content-free parallelization guidance for a route."""

    phases: list[dict[str, Any]] = []
    _append_phase(
        phases,
        phase_id="intake",
        mode="serial",
        gates=_existing(gates, ("request intake", "classify request", "select effort", "grill-me if needed")),
        tasks=("classify request clarity", "answer direct questions before work", "settle blocker questions"),
        constraints=("do not start project mutations before intake is clear",),
    )
    _append_phase(
        phases,
        phase_id="orientation",
        mode="parallel",
        gates=_existing(gates, (ROUTE_DOCS_READ_GATE, SOURCE_DOCS_GATE)),
        tasks=("read independent required docs", "run read-only searches", "inspect stack and git status"),
        constraints=("read-only commands only", "preflight must succeed before edits"),
    )
    _append_phase(
        phases,
        phase_id="scoping",
        mode="serial",
        gates=_existing(
            gates,
            (
                ALIGNMENT_BRIEF_GATE,
                AGENTIC_RUN_STATE_GATE,
                AMBIGUITY_GATE,
                DOCUMENTATION_IMPACT_GATE,
                CYCLE_CONTRACT_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
            ),
        ),
        tasks=("define assumptions and acceptance source", "record run state", "stabilize contracts"),
        constraints=("shared contracts and write scopes must be settled before parallel writers",),
    )
    _append_worker_phase(phases, command, gates)
    _append_phase(
        phases,
        phase_id="integration_review",
        mode="serial",
        gates=_existing(gates, ("integration review", SIDE_EFFECT_AUDIT_GATE, "review hook")),
        tasks=("merge worker results", "check contract drift and side effects", "run review hook"),
        constraints=("must run after any parallel writers before broad verification",),
    )
    _append_phase(
        phases,
        phase_id="verification",
        mode="parallel",
        gates=_existing(
            gates,
            (
                TEST_GATE,
                DOCUMENTATION_GATE,
                "verify",
                "verification",
                "run checks",
                "evidence",
                "regression check",
                "equivalence check",
                "smoke",
                "measure",
                "link/path check",
            ),
        ),
        tasks=("run independent tests, audits, link checks, and smoke checks", "keep dependent checks ordered"),
        constraints=("parallelize only when checks do not mutate shared state",),
    )
    _append_phase(
        phases,
        phase_id="closeout",
        mode="serial",
        gates=_existing(gates, ("commit readiness", "handoff", "report", "recommendation", "open decisions")),
        tasks=("check required gate evidence", "report verification and residual risk"),
        constraints=("do not finalize until every required gate has evidence",),
    )
    return {
        "schema_version": 1,
        "strategy": "parallelize_read_only_then_disjoint_workers_then_serial_integration",
        "phases": phases,
        "notes": [
            "Use these phases to find safe parallel work; do not treat route gates as one fully serial chain.",
            "Batch independent read-only commands and selected document reads instead of running them one at a time.",
            "Parallelize read-only orientation and independent verification when the runtime supports it.",
            "Use Review Hook --review-path for task-owned files when unrelated working-tree changes are present.",
            "Run writers in parallel only after owned scopes, forbidden scopes, contracts, and checks are explicit.",
            "Keep shared contracts, generated files, migrations, dependency changes, release config, and same-file edits serial.",
        ],
    }


def _append_worker_phase(phases: list[dict[str, Any]], command: str, gates: list[str]) -> None:
    if command == "multi-agent":
        _append_phase(
            phases,
            phase_id="worker_execution",
            mode="conditional_parallel",
            gates=_existing(gates, ("roles", "write scopes", "agent briefs")),
            tasks=("run workers on disjoint owned scopes", "collect worker acceptance and verification"),
            constraints=("only parallelize after briefs are complete", "lead owns integration"),
        )
        return

    implementation_gates = _existing(
        gates,
        (
            MULTI_AGENT_GATE,
            "implementation",
            "code work",
            "fix",
            "small refactor",
            "install or repair",
            "act",
            "edit",
        ),
    )
    _append_phase(
        phases,
        phase_id="implementation" if command in CODE_WORK_COMMANDS else "action",
        mode="conditional_parallel" if command in CODE_WORK_COMMANDS else "serial",
        gates=implementation_gates,
        tasks=("split work only across disjoint files or modules", "keep shared contracts serial"),
        constraints=("requires explicit owned scope, forbidden scope, contract, and verification",),
    )


def _append_phase(
    phases: list[dict[str, Any]],
    *,
    phase_id: str,
    mode: str,
    gates: list[str],
    tasks: tuple[str, ...],
    constraints: tuple[str, ...],
) -> None:
    if not gates:
        return
    phases.append(
        {
            "id": phase_id,
            "mode": mode,
            "after": _after(phases),
            "gates": gates,
            "tasks": list(tasks),
            "constraints": list(constraints),
        }
    )


def _existing(gates: list[str], candidates: tuple[str, ...]) -> list[str]:
    return [gate for gate in candidates if gate in gates]


def _after(phases: list[dict[str, Any]]) -> list[str]:
    if not phases:
        return []
    return [str(phases[-1]["id"])]
