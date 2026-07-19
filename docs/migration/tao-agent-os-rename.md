---
keyflow_id: doc_tao_agent_os_rename_migration
status: review
type: human-reviewed-needed
---

# Tao Agent OS Rename Migration

Handoff notes for the rebrand from AgentPlaybook to Tao Agent OS.

This file lives in the repository on purpose. A Claude session's memory directory
is derived from the project path, so renaming the folder makes the old session
memory unreachable. Anything a later session needs has to travel with the repo.

## Naming

| Use | Value |
|---|---|
| Display name | `Tao Agent OS` |
| Repository | `taehwandev/tao-agent-os` (renamed already) |
| Local folder | `~/git/tao-agent-os` |
| CLI | `tao` |
| State directory | `~/.tao/` |
| Launcher | `~/.tao/bin/tao-hook` |
| Environment | `TAO_HOME`, `TAO_ROOT` |
| Placeholders | `<TAO_ROOT>`, `<TAO_LAUNCHER>` |
| Site | `tao.thdev.app` |

`道` means the way, the path. The project preserves a way of working across
agents, so the name states what it does. Display long, run short: prose says
"Tao Agent OS", commands say `tao`.

## Phases

Phase 1 and 2 are independent. Do not merge them: phase 2 needs code changes
that do not exist yet, and running it early breaks every installed runtime.

### Phase 1 — folder rename (ready now)

Renames the checkout only. The state directory keeps its current name, so the
launcher, permission entries, and gates keep working once setup reruns.

Run from `~/git`, never from inside the checkout — the shell's working directory
disappears mid-command otherwise.

```bash
cd ~/git

# 1. Close every agent session that has this repo open first.
#    A running session holds a stale cwd and will fail confusingly.

# 2. Rename the checkout.
mv AgentPlaybook tao-agent-os

# 3. Repoint the launcher and regenerate every absolute permission entry.
#    Setup writes install-time absolute paths, so all 211 entries
#    (Claude 78, AGY 78, Codex 55) are stale until this runs.
python3 ~/git/tao-agent-os/scripts/setup-agent-hooks.py --skip-graphify \
  --target ~/git/tao-agent-os

# 4. Repoint every other project that references the old path.
for d in ~/git/*/; do
  python3 ~/git/tao-agent-os/scripts/setup-agent-hooks.py --skip-graphify --target "$d"
done
```

Verify:

```bash
cat ~/.agentplaybook/agentplaybook-root          # must print the new path
cd ~/git/tao-agent-os && python3 -m unittest discover -s tests   # 592 pass
grep -rl "git/AgentPlaybook" ~/git/*/.claude ~/git/*/.agentplaybook 2>/dev/null
# the grep must return nothing
```

Known references to the old path at the time of writing: `~/git/Spill` (8 files)
and the repo itself (20 files).

### Phase 2 — state directory and identifiers (needs code first)

`~/.agentplaybook` → `~/.tao`, `AGENTPLAYBOOK_*` → `TAO_*`, launcher renamed to
`tao-hook`. This cannot be a plain `mv`: the code looks for the current names in
518 places, and the gates resolve the launcher path from
`support/stable_launcher.py`.

Order that avoids a broken window:

1. Teach the code both names — new name preferred, old name accepted as fallback.
2. Ship and verify that fallback.
3. Move the directory and rerun setup.
4. Remove the fallback in a later change.

Skipping the fallback means every machine is broken between steps 3 and 4.

## Display-name rebrand

Separate from both phases and safe to do at any time: `AgentPlaybook` →
`Tao Agent OS` in prose, roughly 723 occurrences across 254 files. It touches no
path, environment variable, or placeholder, so nothing breaks.

Do not rename `AGENTPLAYBOOK_*` or `~/.agentplaybook` as part of this. Those are
phase 2.

## Already done

- GitHub repository renamed to `taehwandev/tao-agent-os`
- `git remote` updated to the new URL
- `fix/cross-project-gate` pushed — gates now resolve the project from the edited
  file rather than the working directory, and the Stop gate checks every project
  a session touched

## Prompt for the next session

Paste this after the folder rename. A new session starts with no memory of this
work, and its memory directory is keyed to the new path, so the old one is gone.

```text
~/git/tao-agent-os 로 폴더 rename을 마쳤다.
docs/migration/tao-agent-os-rename.md 를 먼저 읽고 이어서 진행해줘.

확인부터:
1. cat ~/.agentplaybook/agentplaybook-root 가 새 경로를 가리키는지
2. python3 -m unittest discover -s tests 가 592개 통과하는지
3. ~/git/*/.claude 와 ~/git/*/.agentplaybook 에 git/AgentPlaybook 참조가 남았는지
   남아 있으면 그 프로젝트마다 setup-agent-hooks.py --target 로 재설치

다음 작업:
- 표시 이름 AgentPlaybook -> Tao Agent OS 교체 (약 723회 / 254파일).
  경로, AGENTPLAYBOOK_* 환경변수, ~/.agentplaybook 은 건드리지 말 것.
  이건 문서의 Phase 2이고 코드 폴백을 먼저 넣어야 한다.
- 파일 종류로 나눠 병렬 처리:
  W1 README.md, index.md, AGENTS.md, docs/, templates/
  W2 common/skills/, workflows/skills/
  W3 scripts/, tests/ 의 표시 문자열만
- 통합 review/finish 와 커밋은 부모가 담당

작업 전에 반드시:
~/.agentplaybook/bin/agentplaybook-hook start --project "$(pwd)" --rules "$(pwd)"
--command <route> --request "<요청>"
게이트가 start 없는 편집을 차단하고, finish 없는 종료도 차단한다.
```

## Still open

- Domain `agentplaybook.thdev.app` → `tao.thdev.app`: needs a DNS record and a
  GitHub Pages CNAME change, neither of which an agent can do
- Blog series (5 files under `~/Documents/KeyFlowVault/writing`) refers to the
  project by the old name. The published parts are a historical record; decide
  per file whether to update or leave
- `CLAUDE_CODE_SESSION_ID` is occasionally absent at a turn boundary, which makes
  `start` write an unstamped preflight and the edit gate deny until `start`
  reruns. Fails closed, cause unreproduced
