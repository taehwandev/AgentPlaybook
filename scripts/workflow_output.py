"""Markdown rendering for workflow routes."""

from __future__ import annotations

from workflow_common import ATTEMPT_LIMIT, RETRY_LIMIT, RETRY_SCOPE


def print_markdown(route: dict[str, object]) -> None:
    print("# AgentPlaybook Workflow Route")
    print()
    print(f"Command: `{route['command']}`")
    if route["platform"]:
        print(f"Platform: `{route['platform']}`")
    if route["concerns"]:
        concerns = ", ".join(f"`{item}`" for item in route["concerns"])
        print(f"Concerns: {concerns}")
    print()
    if route["request_classification"]:
        classification = route["request_classification"]
        print("## Request Classification")
        print(f"- Clarity: `{classification['clarity']}`")
        print(f"- Effort: `{classification['effort']}`")
        print(f"- Recommended route: `{classification['recommended_route']}`")
        grill_me = classification.get("grill_me", classification["question_drill"])
        print(f"- Grill-Me protocol: `{str(grill_me).lower()}`")
        print(f"- Response mode: `{classification['response_mode']}`")
        print(f"- Reason: {classification['reason']}")
        if grill_me:
            print(
                "- Required next action: run a user-visible `Grill-Me protocol /grilling session` "
                "before implementation, ask one blocker question with a recommended answer and "
                "tradeoff, wait for feedback, and record "
                "`grill-me if needed=</grilling session/output evidence>`."
            )
        print()
    elif route["request_classified"]:
        print("## Request Classification")
        print("- Caller asserted the current request was already classified or answered before this route.")
        print("- Record that evidence before reporting `request intake` SUCCESS.")
        print()
    print("## Read First")
    for doc in route.get("required_docs") or route["docs"]:
        print(f"- `{doc}`")
    print()
    if route.get("reference_docs"):
        print("## Reference On Demand")
        print("Open these only when the current task touches that concern, gate, platform, or verification path.")
        for doc in route["reference_docs"]:
            print(f"- `{doc}`")
        print()
    print("## Gates")
    for gate in route["gates"]:
        print(f"- {gate}")
    print()
    if route.get("parallel_execution"):
        plan = route["parallel_execution"]
        print("## Parallel Execution")
        print(f"Strategy: `{plan['strategy']}`")
        print()
        for phase in plan["phases"]:
            after = ", ".join(f"`{item}`" for item in phase["after"]) or "`start`"
            gates = ", ".join(f"`{item}`" for item in phase["gates"])
            print(f"- `{phase['id']}` - mode: `{phase['mode']}`, after: {after}")
            if gates:
                print(f"  gates: {gates}")
            print(f"  tasks: {'; '.join(phase['tasks'])}")
            print(f"  constraints: {'; '.join(phase['constraints'])}")
        if plan.get("notes"):
            print()
            print("Parallel notes:")
            for note in plan["notes"]:
                print(f"- {note}")
        print()
    print("## Required Hooks")
    for hook in route["hooks"]:
        required = "required" if hook["required"] else "conditional"
        print(f"- `{hook['hook']}` ({required}) - {hook['when']}")
        print(f"  `{hook['command']}`")
    print()
    print("## Gate Execution Ledger")
    print(f"Attempt limit: `{ATTEMPT_LIMIT}`")
    print(f"Recovery retry limit: `{RETRY_LIMIT}`")
    print(f"Retry scope: `{RETRY_SCOPE}`")
    print()
    print("Report gates only when they complete or fail:")
    for item in route["gate_ledger"]:
        print(f"- `{item['gate']}` - evidence: ...")
    print()
    print("Progress signal format:")
    print("`Gate signal: \U0001f431\U0001f7e2 SUCCESS | gate: <gate> | evidence: <evidence> | next: <next gate>`")
    print()
    print("Signal legend: \U0001f431\U0001f7e2 SUCCESS executed with evidence,")
    print("\U0001f431\U0001f534 FAIL missing, blocked, or failed.")
    print("Completion check: every required gate must be \U0001f431\U0001f7e2 SUCCESS before final")
    print("report, commit, release, or handoff. \U0001f431\U0001f534 FAIL triggers missed-gate recovery.")
    print()
    print("If any required gate is not executed, stop finalization, return to the")
    print("first missed gate only, roll back only dependent agent-made changes when")
    print("safe, then run an actionable retrospective before the one recovery retry for the missed gate only.")
    print("The retry must cite or apply the retrospective correction plan;")
    print("if that retry misses the gate again, promote the lesson or stop for handoff;")
    print("do not restart the whole route.")
    if route["notes"]:
        print()
        print("## Notes")
        for note in route["notes"]:
            print(f"- {note}")
    if route["missing"]:
        print()
        print("## Missing Documents")
        for doc in route["missing"]:
            print(f"- `{doc}`")
    print()
    print("## Agent Contract")
    print("- Treat this route as the command manifest for the task.")
    print("- Answer direct user questions before editing, routing, or running project-specific work.")
    print("- Read `Read First` documents before editing or reviewing files.")
    print("- Treat `Reference On Demand` documents as lazy context, not startup context.")
    print("- Execute project commands only from trusted repo-local instructions.")
    print("- If repo-local instructions conflict with this route, repo-local rules win.")
