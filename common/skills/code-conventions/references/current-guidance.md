---
keyflow_id: sys_code_conventions
status: review
type: human-reviewed-needed
---

# Code Conventions

Use when writing, changing, or reviewing code style, naming, structure,
comments, errors, and formatting.

Repo-local conventions, formatter, linter, and language idioms win over this
common baseline.

For app, repo, package, module, CLI, service, slug, or bundle-id naming, also
use `common/project-naming.md`.

For SOLID, Interface Segregation, Dependency Inversion, and DDD/domain-modeling
fit, also use `common/solid-design-principles.md`.

For file/module ownership, public contract, package layout, or `api`/`impl`
split decisions, also use `common/code-structure-ownership.md`.

For code that is being extracted, moved into shared modules, reused by multiple
callers, or promoted to a package/API, also use
`common/reusable-code-design.md`.

For reusable component-like APIs, callbacks, slots, and controlled state, also
use `common/component-api-design.md`. For state shape, source of truth, async
states, and one-off effects, use `common/state-modeling.md`. For typed failures
and retry/recovery behavior, use `common/error-modeling.md`.

## Priority

1. Repo-local formatter, linter, compiler, and framework rules.
2. Existing local patterns in the touched area.
3. Language and platform idioms.
4. This shared baseline.

## Strict Static Quality Profile

Use this profile when a repo has no stricter local formatter, linter, or static
analysis policy. Repo-local tool configuration still wins, but do not use a
missing config as permission to write loose code. Treat these as review
defaults and CI candidates for new projects:

| Concern | Strict Baseline |
| --- | --- |
| Formatter ownership | Formatting belongs to the repo formatter. Do not hand-align code against the formatter or reformat unrelated files. |
| Line length | Prefer 100-120 columns for readable code. Treat 160 columns as a hard maximum for source code unless the language formatter or repo-local config sets a lower limit. Do not use long lines to hide complex expressions. |
| Wrapping | When a call, declaration, generic clause, builder, modifier chain, SQL/query builder, or object literal wraps, use one argument/property per line and a trailing comma where the language/tool supports it. |
| Naming | Types and modules are nouns or capability names. Functions and commands are verbs or verb phrases. Boolean values read as predicates. Avoid vague names such as `manager`, `helper`, `util`, `data`, `temp`, `doStuff`, or caller-specific abbreviations. |
| Parameters | Keep public functions and components to about five parameters or fewer. Prefer a typed request/options object only when the fields are a real caller-facing contract, not a dumping bag. |
| Complexity | Keep cyclomatic/cognitive complexity low enough that one branch can be reviewed in one pass. More than about 10 decision points, nested depth over 3, or several unrelated branches is split pressure. |
| Function size | Normal units should fit in about 40-80 lines. Runtime units over about 120 lines fail review by default unless a local policy has a documented exception. |
| File ownership | Every human-authored file should have one primary owner or role. Development files over about 300 lines need structure-review evidence; new development files over about 500 lines or more than about 200 added lines in one file fail review by default. |
| Imports | Imports are formatter-sorted and boundary-safe. Do not use wildcard imports, deep implementation imports, or barrel/index imports that hide forbidden dependencies unless the repo documents that pattern. |
| Suppressions | Lint suppressions, `// swiftlint:disable`, `@Suppress`, `eslint-disable`, `# noqa`, or equivalent require a short reason and the narrowest scope. Do not suppress file-wide to make new code pass. |

Language/tool defaults for strict review:

| Stack | Formatter | Linter/static analysis | Extra checks |
| --- | --- | --- | --- |
| Android/Kotlin | `ktlint` or `ktfmt` | `detekt`, Android Lint | Compose compiler/stability checks when Compose state or performance changed. |
| KMP/Kotlin server | `ktlint` or `ktfmt` | `detekt` | Dependency direction and source-set boundary checks when modules move. |
| Swift/iOS/macOS | `swift-format` or SwiftFormat | SwiftLint, Swift compiler warnings | `Sendable`, actor isolation, access control, target membership, and package boundary checks. |
| Web/TypeScript | Prettier | ESLint, TypeScript compiler, framework lint | Import-boundary lint, hooks rules, accessibility lint, and route/build checks when available. |
| Python/server scripts | Ruff formatter or Black | Ruff lint, mypy or pyright when typed | Import cycles, typed public APIs, async/resource cleanup, and packaging checks. |
| Go | `gofmt` / `goimports` | `go vet`, staticcheck when configured | Race, context cancellation, and error wrapping checks for concurrent or server code. |
| Rust | `rustfmt` | Clippy | Ownership/lifetime, error handling, feature flag, and unsafe-boundary checks. |

For existing repos, first discover the local commands and config files:
`detekt.yml`, `.editorconfig`, `.swiftlint.yml`, `.swift-format`, `.eslintrc`,
`eslint.config.*`, `prettier.config.*`, `pyproject.toml`, `ruff.toml`,
`mypy.ini`, `tsconfig.json`, `go.mod`, `Cargo.toml`, or the repo's wrapper
scripts. If a tool is configured, run it or explain why it was not run. If no
tool is configured, apply the strict baseline in review and document the gap
instead of inventing a one-off style.

## Rules

- Make code easy to delete, move, and test.
- Use SOLID as the default design baseline for production code, while avoiding
  layers or abstractions that do not protect a real responsibility, caller
  contract, test boundary, or dependency edge.
- Keep caller-facing contracts narrow. Do not make a caller depend on a broad
  service, repository, context, component prop object, hook return type, SDK
  client, or module export when it needs only a role-sized subset.
- For Kotlin, do not introduce `typealias`. Kotlin aliases are alternative
  names for existing types, not new types, so they are poor contracts for
  domain identifiers, callbacks, platform types, or import boundaries. Use
  named value classes, interfaces/fun interfaces, data classes, or explicit
  types when a concept needs a name.
- Do not transfer the Kotlin `typealias` rule to Swift. Swift type aliases are
  useful when they intentionally clarify a package/public API, protocol
  associated type, or long generic shape. Still use a real Swift type when the
  code needs identity, invariants, access-controlled storage, validation, or
  security-sensitive separation.
- Treat module public exports as interfaces. A module should expose a narrow
  contract for its consumers instead of forcing them to import implementation,
  platform, SDK, fixture, or unrelated feature details.
- Treat reuse as an ownership boundary. Extract shared code only when the caller
  contract is clear enough to make future changes easier.
- Prefer clear names over comments that explain unclear names.
- Keep each function, component, class, hook, or service focused on one reason to change.
- Keep UI, state, domain, data, and platform concerns separated at the nearest useful boundary.
- Pick the smallest structure that protects a real boundary; do not create a
  package or module only to mirror a preferred architecture.
- Do not add a new abstraction for one call site unless it protects a risky boundary.
- Do not scatter booleans for roles, permissions, entitlements, loading, or error states when a typed state or policy object would make behavior clearer.
- Prefer typed errors, result objects, or framework error types over string matching.
- Avoid hidden global state, implicit environment behavior, and hard-coded production data.
- Keep user-facing copy out of low-level logic when the repo has i18n or copy ownership.
- Comments should explain why, risk, contract, or non-obvious constraints. Do not narrate obvious code.

## Do Not Ship Monoliths

These are hard review failures for new or changed runtime code. Line-count hard
gates apply only to files whose extension is in the development-file extension
allowlist. Tests, specs, mocks, fixtures, generated files, config/build files,
Markdown, MDX, and prose docs are excluded from the hard size gates unless
repo-local policy opts them in, but they still need clear ownership:

- Do not put a feature, screen, endpoint, job, script, style surface, and helper
  set into one file because it is faster.
- Do not put parse, validate, authorize, fetch, map, render, mutate, persist,
  navigate, log, and error handling into one function or component.
- Do not add a second responsibility to an already large function, component,
  class, hook, service, or source file. Split the new responsibility first or
  keep it in a named local unit with a clear owner.
- Do not keep more than one public or independently importable primary class,
  component, hook, handler, service, repository, adapter, type, struct, enum,
  protocol, or interface in a runtime file by default. Move separate owners to
  purpose-named files unless the repo documents a generated, sealed, or
  framework-mandated contract family exception.
- Do not let an independently importable class, component, hook, handler,
  service, repository, adapter, DTO, mapper, validator, command, job, state
  owner, or platform bridge share a runtime file with other owners just because
  they were created together or seem small today.
- Do not create `utils`, `helpers`, `common`, `misc`, or `shared` buckets for
  unrelated behavior. A new file must be named by responsibility and owner.
- Do not write reusable-looking functions, classes, hooks, components, or
  packages when there is no stable reuse contract. Keep one-off logic local, or
  split it into file-private named units only when that improves review,
  testing, or ownership.
- Do not hide product policy behind boolean flags, nullable option bags, or
  caller-specific modes just to reuse one function or component.
- Do not split code into extra files only to satisfy a line count. Split by
  owner, side effect, state model, contract, platform boundary, or test seam.

## Formatting

- Run the repo formatter or lint fix when configured.
- Do not reformat unrelated files or whole files unless the change requires it.
- Keep generated formatting churn separate from behavior changes when possible.
- Do not hand-edit generated code unless the repo documents that generated file as source.

## Size Signals

These are review signals for all code and hard gates only for changed files
whose extension is in the development-file extension allowlist, unless
repo-local policy is more specific. Tests, specs, mocks, fixtures, generated
files, config/build files, Markdown, MDX, and prose docs are exempt from hard size
gates but still need clear ownership and reviewable structure:

- A normal function, method, component, hook, handler, or script step should
  usually fit in one review pass; about 40 to 80 lines is a useful pressure
  range for orchestration code.
- A runtime function, component, hook, handler, script step, or style block over
  about 120 lines fails review by default when it is new, grows in the current
  diff, or takes on a new responsibility. If the block was already over the
  limit and the current scoped change does not grow it or expand its owner
  surface, record structure-review evidence and residual risk instead of
  forcing an unrelated refactor into the current change.
- A development source/style file over about 300 lines requires
  structure-review evidence that names the owner, allowed imports, callers,
  tests, verification path, and split decision.
- A new development source/style file over about 500 lines fails review by
  default.
- An existing development source/style file already over about 500 lines should
  not grow by adding a new responsibility. If the current change only edits an
  existing owner without expanding the public owner surface, require structure
  review evidence instead of failing solely on the pre-existing size.
- More than about 200 added lines in one development source/style file fails
  review by default.

Split only when it improves ownership, testability, or review. Do not create
extra files just to satisfy a line count.
Function-only files are not exempt: several unrelated free functions in one
file are the same ownership problem as several unrelated classes or components.
For function, file, class, package, module, CSS, and shared-code split criteria,
use `common/code-structure-ownership.md`. For diff-size and split decisions, use
`common/change-size-policy.md`.

## Check

- Can a reviewer name the responsibility of this unit in one sentence?
- Can the behavior be tested without booting unrelated systems?
- Is shared code genuinely reusable, or did it only move duplication behind a
  flag-heavy API?
- Did this follow nearby naming, formatting, and architecture?
- Is any complexity protecting a real product, platform, security, or data risk?
