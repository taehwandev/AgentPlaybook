---
keyflow_id: sys_e2d59ab64adc
status: draft
type: ai-generated
---

# Agent Playbook

Shared agent guidance for work across repos, apps, platforms, and AI tools.

Base path:

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent
```

Start here:

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/AGENTS.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/index.md
```

## Structure

```text
common/           Shared engineering rules and workflows
platforms/        android, ios, web, server, application tracks
product-patterns/ Reusable product patterns such as auth, invite, billing
workflows/        Repeatable agent work paths
docs/             Static site for GitHub Pages
templates/        Repo-local routing snippets
```

## Rules

- Repo-local instructions always win.
- `AGENTS.md` is the shared entrypoint for agent runtimes.
- Use `index.md` to choose only the needed documents.
- Start most coding work from `common/agent-operating-skill.md`.
- A typical coding task should load `common/llm-coding-discipline.md`,
  `common/code-conventions.md`, one platform architecture card, and only
  relevant detail or concern cards.
- Security, background work, release, permission, and OS integration concerns should load their detail cards explicitly.
- Keep repo paths, commands, components, role matrices, domain terms, and product-specific policy out of this library.
- Keep shared documents short, action-oriented, and reusable.
- Move repeated platform-neutral rules into `common/`.
- Move reusable SaaS or product mechanics into `product-patterns/`.
- Use `workflows/` to compose common and platform cards into repeatable work paths.

## Folder Roles

- `.agent/`: hidden KeyFlow Desktop workspace context
- `agent/`: explicit shared library for multiple repos and agents
