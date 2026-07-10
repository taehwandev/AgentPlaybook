---
keyflow_id: sys_dependency_policy
status: stable
type: human-reviewed-needed
---

# Dependency Policy

Use before adding, replacing, upgrading, or removing libraries, SDKs, build
plugins, packages, services, or runtime tools.

## Default

Use the repo's existing dependencies and platform APIs first. Add a dependency
only when it removes real risk or cost that local code should not own.

## Before Adding

Check:

- Is there an existing dependency or platform API that already solves this?
- Is the problem core domain logic, UI convenience, integration glue, or build tooling?
- Is the package actively maintained and compatible with the repo's license constraints?
- What is the bundle size, binary size, startup, memory, or build-time cost?
- Does it introduce native code, permissions, network calls, telemetry, codegen, or postinstall scripts?
- Does it affect security, auth, payments, cryptography, parsing, sandboxing, or file access?
- Can the dependency be wrapped behind a small adapter if replacement risk is meaningful?

## Rules

- Prefer proven libraries for complex standards, parsing, crypto, payments, auth, protocols, and platform-specific engines.
- Do not add a library for trivial formatting, one helper function, or a single small component.
- Keep dependency updates separate from feature work unless the feature cannot be implemented without the update.
- Pin or lock versions according to the repo's package manager.
- Review transitive risk when a dependency touches build scripts, native code, secrets, network, or user data.
- Document required setup, environment variables, and provider configuration without documenting secret values.

## Supply Chain Check

- Check license compatibility before adding runtime, SDK, or generated-code
  dependencies.
- Prefer packages with clear provenance, releases, changelogs, maintainers, and
  reproducible install behavior.
- Treat build plugins, postinstall scripts, native binaries, codegen tools, and
  SDKs with telemetry as elevated risk.
- Review lockfile changes for unexpected package graph churn.
- Check known vulnerability or advisory output when the package manager or repo
  provides it.
- Avoid abandoned, typosquatted, or unusually broad packages when a smaller trusted
  dependency or platform API is enough.

## Removal Or Replacement

- Confirm no runtime, build, test, generated, or platform packaging path still uses it.
- Remove config, lockfile entries, generated clients, and docs that only existed for it.
- Verify the nearest build or package command.

## Check

- What local complexity does this dependency remove?
- What new supply-chain, security, size, or maintenance risk does it add?
- Is the dependency boundary narrow enough to replace later?
- Is the install/update verified in the same package manager the repo uses?
