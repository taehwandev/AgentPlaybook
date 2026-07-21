---
keyflow_id: sys_android_feature_package_structure
status: review
type: human-reviewed-needed
---

# Android Feature Package Structure

Use when deciding whether a feature flow needs additional packages or when
auditing an existing package layout. This card complements module and file
ownership guidance; it does not prescribe a repository-wide directory tree.

## Three-Step Gate

1. **Flow root** — identify the smallest package that owns the user-visible
   flow, its state, and its immediate collaborators.
2. **Candidate classification** — propose a package only when it represents a
   stable owner, dependency boundary, or independently testable responsibility.
   Classify the flow as compact or complex; compact flows usually stay together.
3. **Audit and collapse** — check callers, imports, visibility, and test seams.
   Collapse a split that only groups types or creates empty indirection.

Do not create default `model/`, `ui/`, `mapper/`, `di/`, or other type-based
packages without an ownership or boundary reason. A package boundary note
should state the owner, allowed callers, dependency direction, and the evidence
that keeps the split useful.

## Boundary Promotion Ladder

Choose the first boundary that satisfies the need:

```text
private file -> flow package -> feature-local owner -> feature module
-> public UI/module boundary -> shared capability
```

Promote code to a feature module or shared capability only when the smaller
boundary cannot satisfy a real caller, release, dependency, or test boundary.
Shared promotion requires at least two stable callers plus a common contract,
clear owner, and preserved dependency direction; reuse by itself is not enough.

## Verification

- Every new package has a named owner and at least one concrete boundary or
  caller.
- Compact flows do not gain ceremony without a measurable benefit.
- Complex flows preserve dependency direction and expose a focused test seam.
- The boundary note and the nearest package/module verification are updated in
  the same change.
