---
keyflow_id: doc_tao_agent_os_rename_migration
status: review
type: human-reviewed-needed
---

# Tao Agent OS Rename Migration

Record of the rebrand to Tao Agent OS.

This file lives in the repository on purpose. A Claude session's memory directory
is derived from the project path, so renaming the folder makes the old session
memory unreachable. Anything a later session needs has to travel with the repo.

## Naming

| Use | Value |
|---|---|
| Display name | `Tao Agent OS` |
| Repository | `taehwandev/tao-agent-os` |
| Local folder | `~/git/tao-agent-os` |
| State directory | `~/.tao/` |
| Launcher | `~/.tao/bin/tao-hook` |
| Root pointer | `~/.tao/tao-root` |
| Environment | `TAO_ROOT`, `TAO_HOME`, `TAO_LAUNCHER`, `TAO_STATE_HOME`, and the rest of the `TAO_*` set |
| Placeholders | `<TAO_ROOT>`, `<TAO_LAUNCHER>` |
| Bridge marker | `<!-- tao-runtime-bridge:start -->` |
| Site | `tao.thdev.app` |

`道` means the way, the path. The project preserves a way of working across
agents, so the name states what it does. Display long, run short: prose says
"Tao Agent OS", commands say `tao`.

## What was done

Three commits on `fix/cross-project-gate`:

1. **Folder rename** — the checkout moved to `~/git/tao-agent-os`, followed by a
   setup rerun for this repo and the eleven other projects that reference it.
2. **Display name** — 627 prose occurrences across 247 files, plus 23 GitHub URLs
   that still pointed at the pre-rename repository slug and only resolved through
   GitHub's redirect.
3. **Identifiers** — every remaining token: the `AGENTPLAYBOOK_*` environment set
   became `TAO_*` across 23 distinct variables, the state directory became
   `.tao`, the launcher became `tao-hook`, the root pointer became `tao-root`,
   the bridge marker became `tao-runtime-bridge`, the permission identifier
   became `TaoAgentOSPython`, the launcher's fallback discovery roots were
   repointed, and five files and directories were renamed.

The 592-test suite passed unchanged at every step.

## Counting note

The original plan estimated 723 display-name occurrences. Measurement found 648
in prose and 568 more inside path strings. A repo-wide substitution would have
corrupted every path, so the work was split by directory under an explicit
exclusion contract that held paths, environment tokens, and lowercase
identifiers constant until they were renamed deliberately in their own step.

Worth keeping in mind for any future rename: count the token in each syntactic
role separately before estimating the work.

## Host-side migration

The repository no longer contains the old name, but a machine that installed an
earlier version still has the old state directory and launcher. To migrate:

```bash
# 1. Close every agent session first. A running session holds the launcher path
#    it read at startup and cannot pick up the new one until it restarts.

# 2. Move the state directory and rename the launcher and root pointer.
mv ~/.agentplaybook ~/.tao
mv ~/.tao/bin/agentplaybook-hook ~/.tao/bin/tao-hook
mv ~/.tao/agentplaybook-root ~/.tao/tao-root

# 3. Regenerate every runtime bridge, hook, and permission entry.
python3 ~/git/tao-agent-os/scripts/setup-agent-hooks.py --skip-graphify \
  --target ~/git/tao-agent-os
for d in ~/git/*/; do
  python3 ~/git/tao-agent-os/scripts/setup-agent-hooks.py --skip-graphify --target "$d"
done

# 4. Move each project's local state directory.
for d in ~/git/*/.agentplaybook; do
  [ -e "$d" ] && mv "$d" "$(dirname "$d")/.tao"
done
```

Verify:

```bash
cat ~/.tao/tao-root                                  # must print ~/git/tao-agent-os
cd ~/git/tao-agent-os && python3 -m unittest discover -s tests   # 592 pass
grep -rl "agentplaybook\|AGENTPLAYBOOK" ~/.claude/settings.json ~/.claude/CLAUDE.md \
  ~/.codex/rules ~/.gemini/config/config.json 2>/dev/null        # must return nothing
```

A transitional symlink at the old state-directory path pointing to `~/.tao` keeps
an already-running session alive across the move. It has to be deleted once those
sessions restart, or the old name survives in the one place that still resolves.

## Still open

- Domain `tao.thdev.app`: the documentation now references the new host, but the
  DNS record and the GitHub Pages CNAME do not exist yet, so published links are
  ahead of reality until someone creates them. Neither step can be done by an
  agent.
- Legacy allow-entries in the runtime permission stores still name the old
  absolute path — 82 in the Codex rules file, 81 in the AGY config. They are
  allow rules, so a stale one never matches and never blocks; they are dead
  weight rather than breakage. Setup does not prune them.
- Blog series (5 files under `~/Documents/KeyFlowVault/writing`) refers to the
  project by the old name. The published parts are a historical record; decide
  per file whether to update or leave.
- `CLAUDE_CODE_SESSION_ID` is occasionally absent at a turn boundary, which makes
  `start` write an unstamped preflight and the edit gate deny until `start`
  reruns. Fails closed, cause unreproduced.

## Observed gap

`setup-agent-hooks.py` reports `ok` for a permission target when the expected
entries are present, without checking whether the absolute paths inside them
still resolve. During this rename that was harmless, because the entries point at
the stable launcher rather than at the repository. A future move that does change
those paths would still report `ok` while leaving them stale.
