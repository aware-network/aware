# Iteration 00 — Spec Bootstrap

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`
Approval: `User-directed in-thread on 2026-03-17`

Phase: `libs/workspace-operator/docs/specs/workspace-operator/phases/00-spec-gate/README.md`
Issue: `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-spec-bootstrap-v0.md`
LOCK: This iteration may create the workspace-operator spec package, define the owner boundary, and establish the phase plan. It must not widen into runtime implementation, robotics workspace mutation, or Structure workspace-service code changes.

## Goal

Bootstrap the owner spec for `workspace-operator` so later workspace seed/layout and canonical workspace operator work lands against an explicit contract instead of drifting between experience and service lanes.

## Scope In

- `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-spec-bootstrap-v0.md`
- `docs/issues/2026/03/17/issues-2026-03-17.md`
- `docs/feed/2026/03/17.md`
- `libs/workspace-operator/docs/specs/workspace-operator/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/SPEC.md`
- `libs/workspace-operator/docs/specs/workspace-operator/PHASES.md`
- `libs/workspace-operator/docs/specs/workspace-operator/iterations/PROTOCOL.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/00-spec-gate/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/00-spec-gate/iterations/00-2026-03-17-spec-bootstrap/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/01-fs-first-seed-and-layout/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/02-workspace-profile-contract/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/03-service-consumption-boundary/README.md`
- `libs/workspace-operator/docs/specs/workspace-operator/phases/04-canonical-aware-workspace-operator/README.md`

## Scope Out

- `libs/workspace-operator/aware_workspace_operator/**`
- `modules/structure/runtime/aware_structure/workspace/**`
- `environments/robotics/workspace/**`
- any compile/test/diagnostic implementation changes

## Expected Deltas

- create a code-owned spec package under `libs/workspace-operator/docs/specs/workspace-operator/`
- freeze the owner split between workspace-operator and Structure workspace service
- define the first four forward phases for workspace-operator evolution
- capture the bootstrap in a dedicated issue/day/feed rail

## Patch Order (declarative)

1. Open a dedicated issue and bind the spec package scope.
2. Create `README.md`, `SPEC.md`, `PHASES.md`, and `iterations/PROTOCOL.md`.
3. Create the Phase 00 gate and the forward phase READMEs.
4. Sync the day index and daily feed with the claim and direction lock.
5. Run simple docs proofs and append receipts.

## Proofs (commands)

1. `find libs/workspace-operator/docs/specs/workspace-operator -type f | sort`
2. `rg -n 'profiles|seed/layout|compile/test/diagnostic orchestration|Python-package coupling|workspace \.aware experiences' libs/workspace-operator/docs/specs/workspace-operator`

## Proof Receipts

- `find libs/workspace-operator/docs/specs/workspace-operator -type f | sort` -> listed the expected 10 spec-package files.
- `rg -n 'profiles|seed/layout|compile/test/diagnostic orchestration|Python-package coupling|workspace \.aware experiences' libs/workspace-operator/docs/specs/workspace-operator` -> hit the expected owner-boundary and phase anchors in `README.md`, `SPEC.md`, `PHASES.md`, and phase READMEs.

## Exit Checks

- [x] The spec package exists in canonical protocol shape.
- [x] The owner split is explicit and non-overlapping.
- [x] Forward phases are named and bounded.
- [x] Claim/update receipts are appended after proofs run.

## Roadblock Rules

Mark `Roadblock` and stop if:

- the direction would force compile/test/diagnostic orchestration ownership into `workspace-operator`
- the spec would overlap active Structure workspace-service implementation ownership instead of defining a clean boundary
- the package cannot be created without first mutating runtime code

## Sign-Off

- Start: `2026-03-17T11:00:00Z`
- End: `TBD`
- Proofs: `TBD`
- Commit: `TBD`
- Handoff: `After proofs, sync issue/day/feed receipts and use Phase 01 to freeze the concrete workspace root placeholder and profile contract.`
