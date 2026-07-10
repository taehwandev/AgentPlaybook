---
keyflow_id: sys_agentplaybook_source_of_truth_ownership
status: review
type: human-reviewed-needed
---

# Source-Of-Truth Ownership

Use this when restructuring AgentPlaybook guidance, moving flat docs into skill
bundles, cleaning duplicated rules, or deciding where a topic belongs.

The goal is to prevent agents from reading several stale versions of the same
rule. A reusable rule should have one canonical owner. Other files may route to
that owner or link to it, but they should not restate the operational rule in
different words.

## Ownership Rule

Use this invariant:

```text
one reusable rule = one canonical owner
```

The canonical owner is the most specific document that can own the rule after
removing repo names, service names, product policy, local paths, commands,
accounts, vendors, and one-off examples.

Preferred ownership order:

1. Repo-local instructions own repo paths, commands, product policy, domain
   vocabulary, and service setup.
2. Product-pattern skills own reusable product invariants such as billing,
   invitations, permissions, or credentials patterns.
3. Platform skills own platform-specific implementation rules and verification.
4. Workflow skills own agent process, gates, evidence, review, release, and
   handoff behavior.
5. Common skills own reusable engineering rules that cross platforms.
6. `docs/skills/...` owns AgentPlaybook maintenance, runtime integration, and
   documentation-system rules.
7. `index.md`, README summaries, and router metadata own
   discovery only; they should not own detailed operational rules.

## Placement Decision

Before moving or editing duplicated guidance, write a short ownership decision:

```text
rule/question:
canonical owner:
reason this owner is most specific:
files to link or remove:
route/index updates:
verification:
```

Use `SKILL.md` for the default entrypoint only. It may name the rule and point
to the exact reference, but the detailed rule belongs in `references/` unless it
is short enough to be required for every use of the skill.

Use a focused reference file when the guidance includes examples, checklists,
source maps, version-sensitive details, audit drills, migration steps, or
special cases. Name the file by the decision it supports, such as
`source-of-truth-ownership.md`, `route-boundaries.md`, or
`release-measurement.md`.

## Duplicate Audit

Run this drill before creating a new card or splitting an existing one:

1. Search for the rule's nouns, gate names, stop signals, and verification
   phrases across `common/`, `workflows/`, `platforms/`, `product-patterns/`,
   `docs/`, `AGENTS.md`, `index.md`, and `workflow-doc-surfaces.json`.
2. Group matches by the question they answer, not by exact wording.
3. Pick the canonical owner using the ownership order above.
4. Preserve the strongest decision rule, stop condition, and verification
   requirement in the canonical owner.
5. Replace duplicate operational prose with one of:
   - a short `Read` bullet that names the canonical owner,
   - an index or routing summary that describes discovery only,
   - deletion after routes and links target the canonical owner.
6. Update route surfaces, concern mappings, and tests so agents load the owner,
   not a stale compatibility path.
7. Run route smoke and validation before reporting completion.

## Compatibility Stubs

Flat `.md` compatibility stubs are temporary exceptions, not the normal
AgentPlaybook layout. Prefer deleting them after internal routes, links, tests,
and docs-read paths target the canonical bundle.

Keep a flat stub only when a named downstream repo instruction, runtime bridge,
or external published link still requires the exact legacy path. A retained stub
must stay short and may include:

- frontmatter that marks it as a compatibility entrypoint,
- the canonical `SKILL.md` path,
- the detailed reference path,
- a verification note saying routes should load the canonical bundle.

A stub must not include copied checklists, stop conditions, examples, or source
coverage. If the stub needs those details to be useful, the canonical bundle is
not wired clearly enough. If no named compatibility dependency remains, remove
the stub instead of keeping a second retrieval target.

## Router And Index Summaries

`index.md`, workflow concern maps, and `workflow-doc-surfaces.json` may describe
why a document is discoverable. They should not become alternate sources of the
rule. Keep their wording short enough that changing the canonical owner does not
require updating several narrative copies.

When a request names folder structure, `SKILL.md`, `references/`, skill bundles,
source-of-truth cleanup, duplicated guidance, or misplaced docs, routing should
load `docs/skills/agentplaybook-skill-bundle-migration/SKILL.md` before edits.

## Stop If

- Two canonical docs would still answer the same rule after the cleanup.
- A compatibility stub is retained without a named compatibility dependency.
- A compatibility stub contains the full rule instead of a pointer.
- A routing or index summary restates a rule in enough detail to drift.
- A moved rule loses a stronger stop condition, verification requirement, or
  source constraint.
- A third-party skill or vendor workflow is copied instead of distilled into a
  reusable AgentPlaybook rule.
- The cleanup would delete a compatibility path still referenced by runtime
  bridges, downstream repos, or tests before those references are updated or
  explicitly accepted as broken external compatibility.

## Verification

For each cleanup slice:

1. Run `python3 scripts/workflow.py validate`.
2. Run a route smoke using the user language that triggered the cleanup and
   confirm the canonical owner appears in `required_docs`.
3. Check that duplicate files now link to the canonical owner or have been
   removed rather than restating the rule.
4. Run the relevant tests for workflow routing when route surfaces changed.
5. Run `vibeguard audit . --rules .`.
6. If graphify output is maintained for the repo, run `graphify update .` after
   modifying docs or scripts.
