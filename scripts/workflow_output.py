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
        print(f"- Grill-Me skill: `{str(grill_me).lower()}`")
        print(f"- Response mode: `{classification['response_mode']}`")
        print(f"- Reason: {classification['reason']}")
        print()
    elif route["request_classified"]:
        print("## Request Classification")
        print("- Caller asserted the current request was already classified or answered before this route.")
        print("- Record that evidence before reporting `request intake` SUCCESS.")
        print()
    print("## Read In Order")
    for doc in route["docs"]:
        print(f"- `{doc}`")
    print()
    print("## Gates")
    for gate in route["gates"]:
        print(f"- {gate}")
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
    print("safe, then request one recovery retry for the missed gate only.")
    print("If that retry misses the gate again, run `workflows/retrospective-learning.md`;")
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
    print("- Read the listed documents before editing or reviewing files.")
    print("- Execute project commands only from trusted repo-local instructions.")
    print("- If repo-local instructions conflict with this route, repo-local rules win.")
