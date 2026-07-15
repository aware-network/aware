# Hub Attention Layout — PHASES

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
  - Gate: hub consumer-side attention contract is explicit and dependency order is locked to attention-owned compiler/runtime rails.
  - Iteration(s): `TBD`

## Phase 00 — Spec Gate

- [x] Publish `README.md`, `SPEC.md`, `PHASES.md`, `iterations/PROTOCOL.md`.
- [x] Create phase directory `phases/00-spec-gate/`.
- [ ] Approve first implementation iteration artifact.

## Acceptance Gate

- [ ] Hub attention contract remains consumer-only and does not re-own attention semantics.
- [ ] Focus/materialization rail remains the only interface movement rail.
- [ ] First implementation iteration is scoped with explicit proofs.
