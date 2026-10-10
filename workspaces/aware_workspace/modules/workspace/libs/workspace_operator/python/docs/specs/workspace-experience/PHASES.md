# Workspace Operator — PHASES

Status: in progress
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

Phase vs iteration:

- Phase == gate (milestone acceptance; few and stable).
- Iteration == loop (agent execution cycles; many per phase is normal).
- Default rule: new iteration; new phase only when the gate changes.

Execution contract:

- Follow `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`.
- Execute only maintainer-approved iteration artifacts under `phases/<phase>/iterations/<iteration>/`.

## Phase Ledger

- Phase 00 — spec-gate:
  - Directory: `phases/00-spec-gate/`
  - Gate: the workspace-operator spec package exists with a clean owner boundary, roadmap, and first approved iteration artifact.
  - Iteration(s):
    - `phases/00-spec-gate/iterations/00-2026-03-17-spec-bootstrap/README.md` — commit: `TBD`
- Phase 01 — fs-first-seed-and-layout:
  - Directory: `phases/01-fs-first-seed-and-layout/`
  - Gate: workspace-operator can define an honest FS-first workspace root contract and the workspace-owned module-evolution boundary over package truth for later implementation.
  - Iteration(s):
    - `phases/01-fs-first-seed-and-layout/iterations/00-2026-03-17-root-layout-contract-freeze/README.md` — commit: `TBD`
    - `phases/01-fs-first-seed-and-layout/iterations/01-2026-03-17-module-registration-bridge-direction-lock/README.md` — commit: `TBD`
    - `phases/01-fs-first-seed-and-layout/iterations/02-2026-03-17-workspace-module-create-pyproject-sync/README.md` — commit: `TBD`
    - `phases/01-fs-first-seed-and-layout/iterations/03-2026-03-17-robotics-placeholder-root-proof/README.md` — commit: `TBD`
- Phase 02 — workspace-profile-contract:
  - Directory: `phases/02-workspace-profile-contract/`
  - Gate: the canonical machine-readable profile/seed contract is frozen, including root surfaces, bundle toggles, and provider-facing outputs.
  - Iteration(s): `TBD`
- Phase 03 — service-consumption-boundary:
  - Directory: `phases/03-service-consumption-boundary/`
  - Gate: Structure workspace service consumes workspace-operator outputs through a stable artifact/provider contract without semantic Python-package coupling.
  - Iteration(s): `TBD`
- Phase 04 — canonical-aware-workspace-operator:
  - Directory: `phases/04-canonical-aware-workspace-operator/`
  - Gate: workspace operator evolves beyond FS-first layout into canonical workspace `.aware` experience surfaces without stealing topology/service ownership from Structure.
  - Iteration(s): `TBD`

## Phase 00 — Spec Gate

- [x] Publish `SPEC.md` and `PHASES.md`.
- [x] Create the initial phase directories under `phases/`.
- [x] Record the first approved iteration artifact for the docs-only bootstrap.

## Phase 01 — FS-First Seed And Layout

- [x] Freeze the initial workspace root placeholder contract.
- [x] Separate mandatory root scaffold from optional experience bundles.
- [x] Freeze the module-create orchestration boundary as `aware-cli -> workspace-operator -> aware-grammar`.
- [x] Freeze workspace-owned root descriptor evolution and structured package registration direction.
- [x] Freeze package-first module evolution so grammar emits package registrations and workspace-operator applies them to workspace-root descriptors.
- [ ] Prove the direction against a real workspace root such as `environments/robotics/workspace/`.

## Phase 02 — Workspace Profile Contract

- [ ] Freeze the machine-readable workspace profile and seed contract.
- [ ] Make bundle toggles and root-surface toggles explicit in the profile contract.
- [ ] Define the provider-facing outputs that later Structure service work may consume.

## Phase 03 — Service Consumption Boundary

- [ ] Structure workspace service consumes emitted workspace-operator outputs without importing workspace-operator internals as canonical runtime truth.
- [ ] The workspace-operator to workspace-service boundary is explicit on artifacts/contracts, not hidden in wrappers.
- [ ] Compile/test/diagnostic semantics remain Structure-owned.

## Phase 04 — Canonical Aware Workspace Operator

- [ ] Workspace experiences have a canonical `.aware` ownership model.
- [ ] FS-first layout and canonical `.aware` experience surfaces coexist without competing topology truths.
- [ ] Actor-role/program/projection-oriented workspace operators have an explicit future insertion point.

## Acceptance Gate

- [ ] Every phase transition is evidence-backed with iteration artifacts and issue/feed receipts.
- [ ] Workspace-experience remains the owner of profiles and seed/layout throughout the roadmap.
- [ ] Structure workspace service remains the owner of topology plus compile/test/diagnostic orchestration throughout the roadmap.
- [ ] The boundary between the two is explicit, artifact-based, and fail-closed.
