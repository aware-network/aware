# Attention Layout Workspace — Runtime Via Aware Grammar — PHASES

Status: in progress
Owner: `codex-019ca6f9-7806-7170-b79f-b9a14c1f1f33`

Phase vs iteration:

- Phase == gate (milestone acceptance; few and stable).
- Iteration == loop (agent-owned execution cycle; many per phase is normal).
- Default rule: new iteration; new phase only when the gate changes.

Execution contract:

- Follow `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`.
- Execute only approved iteration artifacts under `phases/<phase>/iterations/<iteration>/`.

## Phase Ledger

- Phase 00 — spec-gate:
  - Directory: `phases/00-spec-gate/`
  - Gate: anchor workspace + sample-local spec governance + first proof contract are published.
  - Iteration(s):
    - `phases/00-spec-gate/iterations/00-2026-03-04-attention-anchor-bootstrap/README.md` — commit: `5d1118bd908df0e5f264a3e709f1a15b383dd64c`
- Phase 01 — grammar-token-contracts:
  - Directory: `phases/01-grammar-token-contracts/` (TBD)
  - Gate: layout/section grammar token surface is explicit and fail-closed.
  - Iteration(s): `TBD`
- Phase 02 — lowering-ir-contracts:
  - Directory: `phases/02-lowering-ir-contracts/` (TBD)
  - Gate: grammar lowers to typed IR contracts deterministically.
  - Iteration(s): `TBD`

## Phase 00 — Spec Gate

- [x] Publish anchor workspace docs/spec package.
- [x] Publish first anchor source file.
- [x] Publish first proof test contract consuming anchor source.

## Phase 01 — Grammar Token Contracts

- [ ] Freeze `layout` and `section` token contract.
- [ ] Define fail-closed grammar diagnostics.

## Phase 02 — Lowering/IR Contracts

- [ ] Freeze grammar->IR lowering contract.
- [ ] Define deterministic typed IR boundaries.

## Acceptance Gate

- [ ] Anchor remains upstream gate for grammar/lowering implementation.
- [ ] Every phase has explicit iteration artifacts + commit evidence.
