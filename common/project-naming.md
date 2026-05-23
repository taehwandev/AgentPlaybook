---
keyflow_id: sys_project_naming
status: review
type: human-reviewed-needed
---

# Project Naming

Use when naming apps, repos, packages, modules, services, CLIs, slugs,
directories, bundle ids, or generated project scaffolds.

Naming is surface-specific. Do not force every project name into one casing
style.

## Name Surfaces

For a new project, separate these values before creating files or config:

- Display name: user-facing product or app name.
- Repository name: Git remote, folder, and documentation path.
- Package or bundle id: package manager, app store, signing, or runtime id.
- Module or import name: language-specific code identifier.
- CLI or service id: command, daemon, deployment, queue, job, or API slug.

## Defaults

- User-facing app or product display name: `TitleCase`, `PascalCase`, or normal
  branded words with spaces when the platform allows them.
- `.app`, launcher, menu bar, app store, installer, window title, and marketing
  surfaces use the display name, not a lowercase slug.
- Repos, directories, workspace names, deployment ids, service ids, route slugs,
  and docs paths use lowercase `kebab-case`.
- CLI command names use lowercase `kebab-case`; subcommands and flags follow the
  CLI framework or repo convention.
- Environment variable names use uppercase `SNAKE_CASE`.
- Bundle ids, Android application ids, package namespaces, domains, and reverse
  DNS identifiers use lowercase platform-safe identifiers.
- Code module, package, crate, namespace, schema, table, queue, topic, and import
  names follow the language, package manager, or repo-local convention.

## Examples

```text
Display name: Atlas Notes
Repo/folder: atlas-notes
CLI: atlas-notes
Bundle id: com.example.atlasnotes
Env prefix: ATLAS_NOTES
```

```text
Display name: ShellCrew
Repo/folder: shellcrew
CLI: shellcrew
Bundle id: com.example.shellcrew
Env prefix: SHELLCREW
```

## Rules

- Pick a canonical display name and a canonical slug; do not derive one
  inconsistently in different files.
- Preserve brand capitalization in user-facing copy when the repo or product
  already has it.
- Prefer lowercase ASCII slugs for portable filesystem, URL, package manager,
  and CI behavior.
- Do not rename published packages, bundle ids, database identifiers, URLs,
  queues, or integrations only to satisfy casing preference.
- When a rename touches released surfaces, define aliases, migration,
  compatibility, redirect, signing, or store-update behavior first.
- Keep sample names and placeholders clearly fake; do not imply a real product,
  domain, or provider account.

## Check

- Is this name user-facing branding or a machine identifier?
- Which names are already published, installed, imported, linked, or persisted?
- Does the platform require a specific casing or character set?
- Are repo, package, bundle id, CLI, service, and environment names documented
  together?
- Will changing this name break imports, install paths, deep links, callbacks,
  update channels, logs, dashboards, or support docs?
