---
keyflow_id: sys_stack_discovery
status: review
type: human-reviewed-needed
---

# Stack Discovery

Use before running project commands, adding dependencies, editing build config,
or writing framework-specific code in an unfamiliar repo.

## Default

Do not guess the package manager, framework, language version, test runner, or
project command. Discover them from repo files first, then use repo-local
instructions and scripts.

## Inspect First

Look for the files that define the stack:

- repo instructions: `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`,
  `CODEX.md`, `.agents/README.md`, `CONTRIBUTING.md`
- JavaScript/TypeScript: `package.json`, `packageManager`, lockfiles,
  `tsconfig.json`, `jsconfig.json`, bundler/framework config, `.nvmrc`,
  `.node-version`
- package manager lockfiles: `pnpm-lock.yaml`, `package-lock.json`,
  `yarn.lock`, `bun.lockb`, `bun.lock`
- Python: `pyproject.toml`, lockfiles, `requirements*.txt`, `.python-version`
- Python package managers: `uv.lock`, `poetry.lock`, `Pipfile.lock`,
  `requirements*.txt`
- Swift/Apple: `Package.swift`, `Package.resolved`, `Podfile`, Xcode
  project/workspace, scheme docs, app or extension targets
- Android/JVM: `settings.gradle*`, `build.gradle*`, `gradle.properties`,
  `gradle/wrapper/gradle-wrapper.properties`
- build/task runners: `Makefile`, `justfile`, `Taskfile.yml`, `mise.toml`,
  `lefthook.yml`
- Rust: `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`
- Go: `go.mod`, `go.sum`, `go.work`
- containers or CI: `Dockerfile`, compose files, CI workflow files

Prefer the lockfile, wrapper, and repo scripts over global defaults.

## Decide Commands

- Use the package manager implied by the lockfile or `packageManager` field.
- Use scripts or wrappers from the repo before ad hoc commands.
- Check framework and runtime versions before using version-specific APIs.
- Check test, lint, build, and format command names before inventing commands.
- For monorepos, identify the affected workspace before running broad commands.
- Inspect env examples or setup docs for required variables, but do not print
  secret values from local env files.

## Platform Routing Signals

- Android files or Gradle Android plugins: load Android cards.
- Swift packages, Xcode projects, workspaces, `Podfile`, or Apple app targets:
  load Swift cards first, then the matching platform cards.
- iOS, UIKit, SwiftUI app targets, widgets, or app extensions: load iOS cards.
- React, browser UI, routing, forms, or frontend bundlers: load Web cards.
- API servers, database access, jobs, queues, or webhooks: load Server cards.
- Desktop shell, tray/menu, IPC, file/clipboard, updater, or native packaging:
  load Application cards.
- macOS Swift apps often need both Swift cards and Application cards: Swift for
  package, state, design-system, and architecture boundaries; Application for
  windows, panels, menu bar/tray, commands, OS resources, and packaging.

Use these signals to select cards from `index.md`; do not treat them as a
replacement for repo-local instructions.

## Stop If

- Multiple package managers or lockfiles conflict and repo docs do not resolve
  the conflict.
- The expected manifest, wrapper, or workspace cannot be found.
- Running the likely command would install dependencies, write outside the repo,
  hit the network, or change external state without approval.

## Report

When stack discovery affects the work, report the discovered package manager,
framework/runtime, workspace, and command source.
