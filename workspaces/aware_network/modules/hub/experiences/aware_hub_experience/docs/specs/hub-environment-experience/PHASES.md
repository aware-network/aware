# Hub Environment Experience — PHASES

Status: draft
Owner: `codex-019c2411-ab35-7821-974a-249a299a9451`

Phase vs iteration:

- Phase == gate (milestone acceptance; few and stable).
- Iteration == loop (agent execution cycle; many per phase is normal).
- Default rule: new iteration; new phase only when the gate changes.

Execution contract:

- Follow `iterations/PROTOCOL.md`.
- Execute only maintainer-approved iteration artifacts under `phases/<phase>/iterations/<iteration>/`.

## Phase Ledger

- Phase 00 — spec-gate:
  - Directory: `phases/00-spec-gate/`
  - Gate: Hub environment experience contract is explicit, no-side-rail invariants are locked, and implementation can begin under approved iterations.
  - Iteration(s): `TBD`

## Phase 00 — Spec Gate

- [x] Publish `README.md`, `SPEC.md`, `PHASES.md`, `iterations/PROTOCOL.md`.
- [x] Create phase directory `phases/00-spec-gate/`.
- [ ] Approve first implementation iteration artifact.

## Acceptance Gate

- [ ] Hub is explicitly modeled as environment experience (not interface rail).
- [ ] No custom DTO/endpoint strategy remains in this spec contract.
- [ ] First implementation iteration is scoped with issue + ownership evidence.
