"""Constants for canonical Graphify installation."""

from pathlib import Path


RUNTIME_TO_PLATFORM = {
    "agy": "antigravity",
    "antigravity": "antigravity",
    "claude": "claude",
    "codex": "codex",
}

CANONICAL_SKILL_DIR = Path(".agentplaybook/skills/graphify")
CANONICAL_SKILL_PATH = CANONICAL_SKILL_DIR / "SKILL.md"

PLATFORM_SKILL_DIRS = {
    "agents": Path(".agents/skills/graphify"),
    "antigravity": Path(".agents/skills/graphify"),
    "claude": Path(".claude/skills/graphify"),
    "codex": Path(".codex/skills/graphify"),
}

GLOBAL_PLATFORM_SKILL_DIRS = {
    "agents": Path(".agents/skills/graphify"),
    "antigravity": Path(".gemini/config/skills/graphify"),
    "claude": Path(".claude/skills/graphify"),
    "codex": Path(".codex/skills/graphify"),
}

PLATFORM_INTEGRATION_PATHS = {
    "agents": (),
    "antigravity": (
        Path(".agents/rules/graphify.md"),
        Path(".agents/workflows/graphify.md"),
    ),
    # Claude and Codex discover Graphify through their canonical skill links.
    # Their user-owned settings/hooks files may contain unrelated configuration
    # and must not be treated as a required Graphify registration.
    "claude": (),
    "codex": (),
}

PLATFORM_CANONICAL_INTEGRATION_TARGETS = {
    Path(".agents/rules/graphify.md"): CANONICAL_SKILL_DIR
    / "runtime"
    / "antigravity"
    / "rule.md",
    Path(".agents/workflows/graphify.md"): CANONICAL_SKILL_DIR
    / "runtime"
    / "antigravity"
    / "workflow.md",
}

TRACKING_POLICY_PATHS = (
    Path(".gitignore"),
    Path(".agentplaybook/.gitignore"),
    Path(".graphifyignore"),
    Path("graphify-out/.gitignore"),
)

GRAPHIFY_RUNTIME_ADAPTER_INPUTS = (
    Path(".agents/skills/graphify"),
    Path(".agents/rules/graphify.md"),
    Path(".agents/workflows/graphify.md"),
    Path(".claude/skills/graphify"),
    Path(".claude/settings.json"),
    Path(".claude/settings.local.json"),
    Path(".codex/skills/graphify"),
    Path(".codex/hooks.json"),
)

ROOT_GITIGNORE_BLOCK = """# agentplaybook-project-assets:start
# Runtime evidence is local, but canonical project skills are repository assets.
!.agentplaybook/
.agentplaybook/*
!.agentplaybook/.gitignore
!.agentplaybook/skills/
.agentplaybook/skills/*
!.agentplaybook/skills/graphify/
!.agentplaybook/skills/graphify/**
# agentplaybook-project-assets:end"""

AGENTPLAYBOOK_GITIGNORE_BLOCK = """# agentplaybook-project-assets:start
/*
!/.gitignore
!/skills/
/skills/*
!/skills/graphify/
!/skills/graphify/**
# agentplaybook-project-assets:end"""

GRAPHIFY_INPUT_BLOCK = "\n".join(
    (
        "# agentplaybook-graphify-inputs:start",
        ".agentplaybook/",
        *(path.as_posix() for path in GRAPHIFY_RUNTIME_ADAPTER_INPUTS),
        "graphify-out/",
        "# agentplaybook-graphify-inputs:end",
    )
)

GRAPHIFY_OUTPUT_GITIGNORE = """# Generated Graphify output is local by default.
# A repository may explicitly allowlist reviewed, reproducible, public-safe
# graph.json/report/HTML/wiki artifacts when they are intentional products.
/*
!/.gitignore
"""

AGY_GRAPHIFY_RULE = """---
keyflow_id: sys_graphify_antigravity_rule_adapter
status: stable
type: ai-generated
---

# Graphify project rule

The single project Graphify source is
`.agentplaybook/skills/graphify/SKILL.md`. Read it before Graphify work and use
`.agents/skills/graphify` only as the Antigravity/AGY discovery link. Do not
copy shared Graphify guidance into this runtime rule.
"""

AGY_GRAPHIFY_WORKFLOW = """---
keyflow_id: sys_graphify_antigravity_workflow_adapter
status: stable
type: ai-generated
description: Run the project's canonical Graphify skill
---

1. Read `.agentplaybook/skills/graphify/SKILL.md` completely.
2. Apply that canonical workflow from the project root with the user's current
   Graphify arguments.
3. Keep this file limited to AGY invocation; update shared behavior only in the
   canonical skill through Tao Agent OS setup.
"""

CANONICAL_SKILL_REPLACEMENTS = (
    (
        "**MANDATORY: You MUST use the Agent tool here. Reading files yourself one-by-one is forbidden - it is 5-10x slower. If you do not use the Agent tool you are doing this wrong.**",
        "**MANDATORY: Use the active runtime's parallel subagent or delegation feature here. Reading files yourself one-by-one is forbidden because it is substantially slower.**",
    ),
    (
        """> Uses the `Task` tool for parallel subagent dispatch.
> Call `Task` once per chunk — ALL in the same response so they run in parallel.

Pass the extraction prompt as the task description:

```
Task(description="Your task is to perform the following. Follow the instructions below exactly.\\n\\n<agent-instructions>\\n[extraction prompt, with FILE_LIST, CHUNK_NUM, TOTAL_CHUNKS, DEEP_MODE substituted]\\n</agent-instructions>\\n\\nExecute this now. Output ONLY the structured JSON response.")
```

Each subagent writes its result to its own `graphify-out/.graphify_chunk_NN.json`. Collect results as each `Task` completes and parse each as JSON.""",
        """> Use the active runtime's parallel worker primitive for every chunk. Codex maps this to `spawn_agent` plus `wait_agent`; Claude maps it to parallel Agent/Task calls; Antigravity/AGY maps it to its available parallel agent runner. Dispatch all chunks before waiting.

Pass the extraction prompt as the worker task, with `FILE_LIST`, `CHUNK_NUM`, `TOTAL_CHUNKS`, `DEEP_MODE`, and `CHUNK_PATH` substituted. Require each worker to follow the prompt exactly, write only its assigned `graphify-out/.graphify_chunk_NN.json`, and return only a short completion result. Workers must not edit any other project file.

Each worker writes its result to its own `graphify-out/.graphify_chunk_NN.json`. Collect and validate those files after all workers complete.""",
    ),
    (
        "If the file is missing, the subagent was likely dispatched as read-only (Explore type) — print a warning: \"chunk N missing from disk — subagent may have been read-only. Re-run with general-purpose agent.\" Do not silently skip.",
        "If the file is missing, the worker may have been read-only — print a warning: \"chunk N missing from disk — re-run with a write-capable general worker.\" Do not silently skip.",
    ),
    (
        "If more than half the chunks failed or are missing, stop and tell the user to re-run and ensure `subagent_type=\"general-purpose\"` is used.",
        "If more than half the chunks failed or are missing, stop and tell the user to re-run with the active runtime's write-capable general worker type.",
    ),
    (
        "Merge all chunk files into `.graphify_semantic_new.json`. **After each Agent call completes, read the real token counts from the Agent tool result's `usage` field and write them back into the chunk JSON before merging** — the chunk JSON itself always has placeholder zeros. Then run:",
        "Merge all chunk files into `.graphify_semantic_new.json`. **When the active runtime exposes exact worker token counts, copy those exact counts into the chunk JSON before merging; otherwise keep the placeholder zeros and never estimate.** Then run:",
    ),
)
