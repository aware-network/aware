# Iteration 00 — Root Layout Contract Freeze

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`
Approval: `User-directed in-thread on 2026-03-17`

Phase: `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
Issue: `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-root-layout-contract-v0.md`
LOCK: This iteration may freeze the Phase 01 root-layout contract in docs only. It must not change bootstrap code, mutate `environments/robotics/workspace/`, or widen into Structure workspace-service implementation.

## Goal

Define the first honest FS-first workspace root contract for `workspace-operator` so later implementation writes the right roots and bundles instead of guessing them.

## Scope In

- `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-root-layout-contract-v0.md`
- `docs/issues/2026/03/17/issues-2026-03-17.md`
- `docs/feed/2026/03/17.md`
- `libs/workspace-operator/docs/specs/workspace-operator/SPEC.md`
- `libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/iterations/00-2026-03-17-root-layout-contract-freeze/README.md`

## Scope Out

- `libs/workspace-operator/aware_workspace_operator/**`
- `environments/robotics/workspace/**`
- `modules/structure/runtime/aware_structure/workspace/**`
- bootstrap reporter/CLI behavior changes

## Expected Deltas

- freeze the mandatory root metadata tier
- freeze the canonical placeholder roots `modules/`, `apis/`, `services/`, and `experiences/`
- separate placeholder roots from optional experience bundles
- state explicitly that `profiles/` is not a mandatory Phase 01 root

## Patch Order (declarative)

1. Open a dedicated Phase 01 issue and bind the docs-only scope.
2. Update `SPEC.md` with the concrete FS-first root tiers and fail-closed rules.
3. Update the phase ledger and Phase 01 README to reflect the contract freeze.
4. Record the iteration artifact and sync issue/day/feed receipts.
5. Run docs proofs and capture receipts.

## Proofs (commands)

1. `rg -n "Canonical FS-First Root Contract|Tier 1|Tier 2|Tier 3|profiles/ is not a mandatory Phase 01 root" libs/workspace-operator/docs/specs/workspace-operator/SPEC.md`
2. `rg -n "optional experience bundles|profiles/|mandatory root metadata" libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
3. `rg -n "modules/.*, apis/.*, services/.*, and experiences/|workspace root" environments/robotics/docs/specs/robotics-environment-foundation/SPEC.md environments/robotics/docs/specs/robotics-environment-foundation/phases/01-workspace-bootstrap/iterations/00-2026-03-17-cli-bootstrap-root-scaffold/README.md`

## Proof Receipts

- `rg -n "Canonical FS-First Root Contract|Tier 1|Tier 2|Tier 3|profiles/ is not a mandatory Phase 01 root" libs/workspace-operator/docs/specs/workspace-operator/SPEC.md` -> hit the frozen root-tier section and the explicit Phase 01 `profiles/` rule.
- `rg -n "optional experience bundles|profiles/|mandatory root metadata" libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md libs/workspace-operator/docs/specs/workspace-operator/PHASES.md` -> hit the phase gate and roadmap anchors for root-metadata versus optional-bundle separation.
- `rg -n "modules/.*, apis/.*, services/.*, and experiences/|workspace root" environments/robotics/docs/specs/robotics-environment-foundation/SPEC.md environments/robotics/docs/specs/robotics-environment-foundation/phases/01-workspace-bootstrap/iterations/00-2026-03-17-cli-bootstrap-root-scaffold/README.md` -> confirmed robotics already points to the same canonical root set and the next placeholder-doc implementation handoff.

## Exit Checks

- [x] The Phase 01 contract names the mandatory placeholder roots explicitly.
- [x] The contract separates mandatory root metadata, placeholder roots, and optional bundles.
- [x] The contract explicitly keeps `profiles/` out of the mandatory Phase 01 root.
- [x] Day/index/feed receipts are synced after proofs.

## Roadblock Rules

Mark `Roadblock` and stop if:

- freezing the root contract would force immediate bootstrap code changes in the same loop
- robotics or the workspace spec already lock a conflicting root set
- the contract would steal Structure workspace-service ownership

## Sign-Off

- Start: `2026-03-17T11:18:00Z`
- End: `TBD`
- Proofs: `TBD`
- Commit: `TBD`
- Handoff: `Next loop should implement the frozen placeholder roots and ownership docs in bootstrap, using environments/robotics/workspace as the first proof target.`
