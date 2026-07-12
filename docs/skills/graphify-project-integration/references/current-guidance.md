---
keyflow_id: sys_graphify_project_integration_guidance
status: review
type: human-reviewed-needed
---

# Graphify Project Integration Guidance

Graphify is project-local even when its CLI is installed once on the machine.
Every participating repository needs one canonical project skill, thin runtime
integration, and its own `graphify-out/graph.json`. The same operational skill
must not be maintained as separate Codex, Claude, and AGY copies.

## Single Canonical Skill

The canonical project skill is:

```text
.agentplaybook/skills/graphify/
  SKILL.md
  references/
  .graphify_version
```

AgentPlaybook setup stages the provider-neutral Graphify bundle away from the
target, converts runtime-specific delegation wording into one runtime-neutral
flow, and atomically replaces this directory. Stock Graphify project installers
must not be run directly over the final runtime links because their copy and
uninstall paths can overwrite or delete the canonical target.

The user-level fallback follows the same rule:

```text
~/.agentplaybook/skills/graphify/          # one user-level canonical source
~/.codex/skills/graphify                   # link
~/.claude/skills/graphify                  # link
~/.agents/skills/graphify                  # link
~/.gemini/config/skills/graphify           # AGY link
```

Install or check that fallback with
`setup-project-graphify.py --global`. It is local machine state and is never a
target-repository commit. A project-local canonical skill takes precedence for
that repository and remains the portable, versioned source for teammates and
CI.

Codex, Claude, and Antigravity/AGY share this content. `AGENTS.md` and
`CLAUDE.md` must not retain separate Graphify explanation sections. Runtime
locations contain only discovery links or machine configuration; AGY's required
rule/workflow files are themselves links to runtime adapters stored inside the
canonical bundle. This applies the AgentPlaybook invariant `one reusable rule =
one canonical owner`; see
`docs/skills/agentplaybook-skill-bundle-migration/references/source-of-truth-ownership.md`.

## Target Setup

For one explicit target, AgentPlaybook setup includes Graphify by default:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --target <TARGET_REPO>
```

For Graphify-only repair or a parallel migration across already-connected
repositories, use the narrower project installer:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-project-graphify.py \
  --project <TARGET_REPO_A> \
  --project <TARGET_REPO_B> \
  --jobs 4
```

Use `--check` for read-only inspection. The command exits incomplete while any
target lacks its initial `graphify-out/graph.json`, even when canonical skill
and runtime-link migration succeeded; graph generation remains a separate,
skill-directed action.

By default, an explicit target receives Codex, Claude, and AGY entrypoints even
if one of those runtimes is not installed on the setup machine. This keeps the
repository agent-agnostic. Use `--runtime codex`, `--runtime claude`, or
`--runtime agy` only when the repository intentionally supports a limited
runtime set. `--skip-graphify` is an explicit opt-out. Bulk
`--github-projects` setup does not enable Graphify unless `--graphify` is also
passed, because mass repo-local writes require explicit scope.

The setup helper installs or refreshes the canonical skill, replaces runtime
skill copies with repo-relative links, and installs runtime integration. It
must not run initial extraction. If the graph is missing, setup exits
incomplete and tells the active agent to read the canonical skill and build the
graph from the target root.

## Runtime Skill Paths

| Runtime | Project-local entrypoint | Project integration |
| --- | --- | --- |
| Canonical owner | `.agentplaybook/skills/graphify/SKILL.md` | Shared operational content and references |
| Codex | `.codex/skills/graphify -> ../../.agentplaybook/skills/graphify` | `.codex/hooks.json` machine hook only; no `AGENTS.md` Graphify copy |
| Claude | `.claude/skills/graphify -> ../../.agentplaybook/skills/graphify` | `.claude/settings.json` machine hooks only; no `CLAUDE.md` Graphify copy |
| Antigravity/AGY | `.agents/skills/graphify -> ../../.agentplaybook/skills/graphify` | `.agents/rules/graphify.md` and `.agents/workflows/graphify.md` link to canonical runtime adapters |

Read the canonical `SKILL.md` once for the task. Confirm that every enabled
runtime directory is a symlink whose resolved target is the canonical directory
inside the same repository. Do not treat an AgentPlaybook card,
AGENTS/CLAUDE section, rule, workflow, hook, or the Graphify report as a
substitute. Do not accept copied runtime bundles even when their hashes match;
matching copies can drift on the next update.

Opening a runtime directory link in an editor or file browser displays the
canonical directory's files under that runtime path. That view is not evidence
of a second physical copy. Verify the entry itself with `ls -ld` or `readlink`,
and verify the repository form with `git ls-files -s`: a committed runtime
directory link has mode `120000`, while entries such as
`.claude/skills/graphify/SKILL.md` or
`.agents/skills/graphify/references/...` are legacy tracked copies that must be
removed by the same migration commit.

## Version-Control Policy

AgentPlaybook setup creates an allowlist boundary for `.agentplaybook`.

Commit these project assets:

- the root `.gitignore` change that allowlists the canonical skill while
  keeping `.agentplaybook` runtime evidence local
- `.agentplaybook/.gitignore`
- `.agentplaybook/skills/graphify/**`
- `.graphifyignore`, because it defines the repository's graph input boundary
- `graphify-out/.gitignore`, because it records the default local-only output
  policy
- repo-relative runtime directory links under `.codex/skills`,
  `.claude/skills`, and `.agents/skills`, so every supported agent discovers
  the same canonical skill after clone
- AGY rule/workflow links when AGY is an enabled runtime; their adapter content
  remains inside the canonical bundle

Commit these only after an explicit repository policy and privacy/reproducibility
review:

- runtime integration files such as `.codex/hooks.json` and
  `.claude/settings.json`; commit only the machine configuration the repository
  intentionally shares rather than user-local runtime configuration
- `graphify-out/graph.json`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/manifest.json`
- `graphify-out/graph.html` or `graphify-out/wiki/**`

Do not commit:

- `.agentplaybook` preflight, docs-read, review, finish, gate-evidence, or cache
  JSON files
- Graphify `.graphify_*` sidecars, cache directories, chunk files,
  transcripts, cost/token trackers, dated backups, interpreter/root markers,
  or temporary extraction files
- absolute or repository-external symlinks

Before calling the migration commit-ready, confirm that the Git index contains
the canonical files and no descendants below any runtime Graphify link. A
working-tree symlink is insufficient when the index still contains the old
runtime-specific files. The check also fails for unstaged canonical, policy, or
link changes and for required assets still blocked by ignore rules. Stage the
canonical directory, repo-relative runtime links, AGY adapter links, mandatory
policies, and deletion of all legacy runtime descendants as one atomic
migration unit.

`graphify-out/.gitignore` defaults generated output to local-only. A repository
that intentionally publishes reviewed graph artifacts may replace that default
with a narrow allowlist. Existing tracked outputs stay tracked until the
repository explicitly changes that policy; setup must not silently untrack
them.

## Initial Graph And Recheck

After reading the canonical skill, invoke its initial graph flow from the target
root (`$graphify .` for Codex or `/graphify .` where supported). The skill owns
provider/model selection, source scoping, and any cost-sensitive decisions.

Then verify:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check --target <TARGET_REPO>
graphify query "What are the main project modules and their relationships?"
```

For a project that already has a graph, follow the installed skill's update
rules. The AST-only `graphify update .` fast path is suitable after code-only
changes; semantic inputs require the skill-directed update/extraction path.

## Workflow Gate Evidence

Graphify routes include a `graphify readiness` gate. Record these fields:

- `cli`: resolved Graphify executable or verified CLI availability.
- `skill_doc`: canonical `.agentplaybook/skills/graphify/SKILL.md` path and
  confirmation it was read.
- `runtime_links`: every enabled runtime link and its resolved canonical target.
- `project_integration`: runtime-specific instruction/hook/rule/workflow evidence.
- `graph`: target-root `graphify-out/graph.json` evidence.
- `query_smoke`: the scoped query command and successful result.

Presence of a graph alone is insufficient. Likewise, installation output alone
does not prove that the graph was built or queryable.
