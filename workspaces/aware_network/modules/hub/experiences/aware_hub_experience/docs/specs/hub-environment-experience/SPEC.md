# Hub Environment Experience — SPEC

Status: draft
Owner: `codex-019c2411-ab35-7821-974a-249a299a9451`

## Goal

Define Hub as a product-owned environment experience that is instantiated and rendered through canonical experience + commit rails.

## Canonical Direction

Non-negotiable invariants:

- Hub is an environment, not a separate interface application contract.
- Hub is modeled through experience sources and compiled artifacts.
- Interface only renders pane views selected by canonical focus scope state.
- No custom model contract or endpoint strategy for Hub behavior.

## Current Truth (Repo State)

Exists today:

- Experience rails and specs are active:
  - `modules/experience/docs/README.md`
  - `modules/experience/docs/specs/environment-experience/README.md`
- Environment authoring anchor exists:
  - `modules/experience/runtime/samples/e2e/home_story_workspace/experiences/home_story/environments.aware`

Missing today:

- Product-owned `aware-hub` experience package contracts.
- Explicit hub-focused projection ownership contract (OCG first; OPG/repository later).

## Scope

In scope:

- `aware-hub` environment experience contract and phase gates.
- Ownership boundaries for hub projection experience declarations.

Out of scope:

- Attention layout compiler internals.
- Runtime materialization implementation.
- Interface representation implementation.

## Integration Contract

Boundaries:

- Experience owns hub environment-experience declarations and compile-time contracts.
- Attention owns layout/section/focus topology contracts (tracked in companion spec package).
- Interface consumes committed/materialized focus state and must not own hub navigation semantics.

## Data / Identity / Mutation Rules

Fail-closed rules:

- Hub selection/navigation state must be represented by attention/focus objects only.
- UI state must not become a source of truth.
- Any mutation path must be commit-backed; no local speculative hub state rail.

## Evidence And Testing Contract

Required proofs for implementation iterations (later phases):

- Compile proof:
  - `aware-cli compile module experience`
- Experience runtime proofs (targeted set to be declared per iteration).
- Integration proof with attention layout contracts once bridge phase opens.

## Work Governance

- Phases ledger: `PHASES.md`
- Iterations protocol: `iterations/PROTOCOL.md`
- Phase directories: `phases/<phase_order>-<phase_slug>/README.md`
- Active iteration artifacts: `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
