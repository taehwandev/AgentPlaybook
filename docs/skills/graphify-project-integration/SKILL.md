---
keyflow_id: sys_docs_graphify_project_integration_skill
status: review
type: human-reviewed-needed
agentplaybook_card_contract: strict
requires_docs:
  - docs/skills/agent-bootstrap/SKILL.md
  - common/skills/llm-wiki-documentation/SKILL.md
  - common/skills/verification-policy/SKILL.md
---

# Graphify Project Integration

Use when AgentPlaybook is installed in a target repository, when Graphify is
missing or incomplete there, or when a workflow must prove that the target
project's graph, canonical skill, and runtime links are ready.

## Use When

- Applying AgentPlaybook to a repository that should use Graphify.
- Installing or repairing project-local Graphify skills, rules, workflows, or hooks.
- A route mentions Graphify, a project graph, or a missing `graphify-out/graph.json`.
- An agent appears to skip Graphify because the CLI, skill document, integration, or graph is absent.

## Read

- `references/current-guidance.md` for the install/readiness procedure.
- The target project's canonical
  `.agentplaybook/skills/graphify/SKILL.md` before building, updating, or
  querying that project's graph. Runtime skill paths are links to this one
  source, not separate documents to maintain or read independently.

## Decision Rule

Treat Graphify readiness as seven separate conditions: CLI available, one
canonical project-local `SKILL.md` installed and read, every enabled runtime
path resolving to that canonical directory, portable Git ownership verified,
project integration installed, a fresh and input-complete
`graphify-out/graph.json` present, and a scoped query smoke check successful.
Document-to-source relationships are a query-quality signal: when semantic
inputs or explicit path citations produce them, include a representative
doc-to-source path in the smoke check. Their absence does not fail a current,
input-complete AST-only graph. Missing any of the seven conditions is a failed
readiness gate, not permission to skip Graphify silently. A copied runtime
bundle fails the canonical-source condition even when its content currently
matches.

Files visible while an editor follows a runtime directory link are views of
the canonical target, not additional physical copies. Git ownership is ready
only when canonical files and mandatory policies are tracked, every previously
tracked runtime skill path is one repo-relative mode `120000` entry, and no
tracked `SKILL.md` or `references/` descendants remain below runtime paths.
Preserving legacy project knowledge as graph input is only a migration safety
measure; equivalent shared content across runtime directories must still be
collapsed into one `.agentplaybook` owner.

## Process

1. Identify the target repository. Explicit target setup wires Codex, Claude,
   and Antigravity/AGY by default so the repository does not depend on which
   runtime happens to be installed on the setup machine.
2. Run the target setup flow; Graphify integration is included by default for
   an explicit `--target`.
3. Open and read the one canonical
   `.agentplaybook/skills/graphify/SKILL.md`. Verify that `.codex`, `.claude`,
   and `.agents` runtime skill paths are repo-relative links to it. Remove
   duplicate Graphify explanation sections from `AGENTS.md` and `CLAUDE.md`;
   rules or hook files do not substitute for the canonical skill document.
4. Build the initial graph from the target root using the installed skill flow.
5. If project docs explicitly cite source paths but the graph omitted those
   edges, run the AgentPlaybook deterministic document-link repair; it must not
   invent semantic relationships or replace extraction.
6. Run a small `graphify query` smoke check against the target graph.
7. Record all seven readiness fields in the workflow gate evidence.

## Common Rationalizations

| Rationalization | Required response |
| --- | --- |
| "The shared AgentPlaybook graph is enough." | Build and verify the target repository's own graph. |
| "The rule file mentions Graphify." | Read the canonical `.agentplaybook` `SKILL.md`; a rule or hook is only integration wiring. |
| "Each runtime needs its own copy." | Keep runtime mechanics in wiring and resolve all shared skill content to the one canonical bundle. |
| "There is no graph, so I will use grep." | Install/repair Graphify or report the readiness gate failure; do not silently bypass it. |
| "Setup can generate the graph automatically." | Keep installation deterministic; graph generation runs through the skill because it may require model/provider and cost decisions. |

## Red Flags

- `graphify-out/graph.json` comes from another repository.
- A setup command reports success while the runtime skill or graph is missing.
- Codex, Claude, or AGY contains a copied Graphify bundle instead of a
  repo-relative link to `.agentplaybook/skills/graphify`.
- `AGENTS.md` or `CLAUDE.md` restates Graphify operational guidance already
  owned by the canonical skill.
- A codebase answer proceeds without Graphify even though the project opted in.
- A hook, rule, or command registration is claimed as proof that `SKILL.md` was read.
- Initial extraction runs silently during permission or hook installation.

## Do Not

- Do not copy a graph between projects.
- Do not install a Graphify package from the network without approval.
- Do not run paid/model-backed extraction silently from the setup helper.
- Do not mark readiness from file presence alone; include a query smoke check.
- Do not commit generated graph outputs without the target repo's tracking policy review.
- Do not edit runtime links as if they were independent skills; update the
  canonical bundle through AgentPlaybook setup.

## Stop If

- The target project or active runtime is ambiguous.
- The Graphify CLI is missing and installing it would require new network or package authority.
- The installed skill requires a provider, model, or paid action that the user has not approved.
- The graph input scope crosses repositories without an explicit merge scope.

## Verification

- CLI: `graphify` resolves locally.
- Skill doc: `.agentplaybook/skills/graphify/SKILL.md` exists and was read.
- Runtime links: every enabled runtime skill directory is a repo-relative link
  that resolves to the canonical Graphify directory.
- Git ownership: `git ls-files -s` shows no runtime skill descendants and mode
  `120000` for every runtime skill path the repository intentionally tracks.
- Integration: the runtime's rule/workflow/hook or instruction registration exists.
- Graph: `graphify-out/graph.json` is valid, non-empty, anchored to the current
  source revision with a manifest matching current graph inputs, includes the
  repo-local knowledge inventory, and has
  no missing/dangling/self-loop endpoints.
- Query smoke: `graphify query "<scoped target-project question>"` succeeds.
  When semantic inputs expose a project-doc-to-source relation, also exercise a
  representative `graphify path` or equivalent query across it; AST-only graphs
  remain ready when that relation is absent.

## Report

Report all seven fields explicitly: CLI state; canonical skill path and read
evidence; runtime link paths and resolved targets; portable Git ownership;
project integration; graph path plus freshness, integrity, local-knowledge
input coverage, and document-to-code path coverage; and the scoped
query/path smoke result. Name every missing readiness condition. State
separately whether integration was installed and whether the initial graph was
actually built.
