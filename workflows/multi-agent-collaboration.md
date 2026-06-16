---
keyflow_id: sys_multi_agent_collaboration_workflow
status: review
type: human-reviewed-needed
---

# Multi-Agent Collaboration

Use when work is split across multiple agents, delegated roles, parallel tasks,
or a builder/verifier pair.

## Roles

Product owner agent:

- owns user problem, feature boundaries, user-facing behavior, success criteria,
  and non-goals
- should not prescribe low-level implementation unless product-critical

Architecture agent:

- owns module boundaries, contracts, data models, permission model, failure
  modes, dependencies, and verification strategy
- should not accept behavior that cannot be verified

Builder agent:

- implements the assigned slice only
- keeps the repo buildable
- does not broaden scope silently
- preserves user-owned changes

Verifier agent:

- reviews the patch against request, PRD, ARD, repo-local rules, and risk cards
- checks behavior, tests, failure states, and residual risk
- leads with findings

## Gates

For non-trivial feature work, use this sequence unless repo-local workflow says
otherwise:

```text
intake -> ambiguity gate -> PRD -> ARD -> task breakdown -> agent briefs -> implementation -> review -> verification -> closeout
```

Use `workflows/product-architecture-delivery.md` for the PRD, ARD, and commit
readiness gates.

## Parallel Work

Agents may edit in parallel only when write scopes are disjoint.

Rules:

- The lead agent should actively look for safe parallel slices when a task has
  independent surfaces. Do not wait for the user to request parallel agents when
  the split is obvious and low risk.
- Assign each writer explicit owned files or modules.
- Assign explicit forbidden files or modules when overlap is likely.
- Do not assign two writers to the same file.
- Serialize architecture, shared model, migration, dependency, generated-file,
  and release-config changes.
- If one task depends on an undefined model or contract from another task,
  define the contract first or serialize the work.
- Keep implementation briefs narrow enough that a worker can finish without
  changing another worker's contract, route, schema, state model, or config.
- Review and integrate parallel changes before broad verification.

Good splits:

- domain logic versus UI wiring after the model contract is stable
- docs update versus isolated source change
- provider/adapter implementation versus tests for a separate helper

Bad splits:

- two agents editing the same view, route, reducer, schema, or config file
- one agent changing shared models while another consumes the unstable shape
- broad refactors mixed with feature work across the same modules
- multiple agents adding exports to the same package barrel, public API, design
  system surface, generated client, migration chain, or release manifest

## Lead-Agent Split Decision

Before spawning or assigning parallel implementation work, the lead agent must
name:

- the stable contract that all workers can rely on
- each worker's owned files, packages, or modules
- each worker's forbidden files, packages, or modules
- the integration point and who owns it
- the focused verification for each slice and the final merged check

If any of those cannot be named, keep the work serial until the boundary is
clear. The lead agent remains responsible for integrating the result, resolving
conflicts, and ensuring the final diff still satisfies the original request.

## Agent Briefs

Each brief should include:

- task id
- role
- goal
- owned files or modules
- forbidden files or modules
- acceptance checks
- verification commands or manual scenarios
- expected final report shape

For code-edit workers, include:

- the checkout may contain user-owned changes
- do not revert changes outside assigned scope
- list changed files and verification in the final report

## Closeout

Closeout should state:

- what changed
- what was verified
- what remains risky
- which follow-up tasks exist
- whether docs, tests, or run artifacts were updated

## Stop If

- Two agents would edit the same file, schema, migration, generated artifact, or
  release config at the same time.
- The shared contract between parallel tasks is not defined.
- A worker brief lacks owned files, forbidden files, acceptance checks, or
  verification expectations.
- Integration review cannot be performed before broad verification or handoff.
