# Phase 01 — FS-First Seed And Layout

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

## Gate

Workspace-experience has a frozen FS-first root layout contract and a frozen package-first module-evolution boundary that keep workspace FS truth under workspace-operator ownership.

## Goal

Freeze the first real workspace-operator product surface: FS-first workspace seed/layout, mandatory root metadata, canonical placeholder roots, the explicit separation from optional experience bundles, and the package-first module-create boundary that keeps root descriptor evolution out of CLI and grammar.

## Scope In

- workspace root scaffold policy
- placeholder roots `modules/`, `apis/`, `services/`, and `experiences/`
- distinction between root layout and optional bundles
- module-create orchestration boundary
- package-first module evolution contract
- root descriptor evolution ownership
- structured package registration direction
- robotics workspace as the first proof target for later implementation
- robotics or equivalent workspace-root proof targets

## Scope Out

- Structure workspace-service execution features
- canonical `.aware` workspace operator authoring
- module/API/service creation flows beyond declaring the root layout
- adding `profiles/` as a mandatory day-0 root

## Acceptance (Gate Checklist)

- [x] The root placeholder contract is explicit and profile-driven.
- [x] The root scaffold separates mandatory workspace files from optional experience bundles.
- [x] The phase explicitly keeps `profiles/` out of the mandatory Phase 01 root.
- [x] The module-create orchestration boundary is explicit.
- [x] Module create is defined as a workspace-owned transaction over package registrations rather than module-path heuristics.
- [x] Root descriptor evolution is workspace-operator-owned and non-manual.
- [ ] At least one real workspace root proves the contract without manual patching.

## Iterations

- `iterations/00-2026-03-17-root-layout-contract-freeze/README.md`
- `iterations/01-2026-03-17-module-registration-bridge-direction-lock/README.md`
- `iterations/02-2026-03-17-workspace-module-create-pyproject-sync/README.md`
- `iterations/03-2026-03-17-robotics-placeholder-root-proof/README.md`
