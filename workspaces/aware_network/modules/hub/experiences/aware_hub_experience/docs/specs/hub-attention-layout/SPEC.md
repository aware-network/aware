# Hub Attention Layout — SPEC

Status: draft
Owner: `codex-019c2411-ab35-7821-974a-249a299a9451`

## Goal

Define how Hub experience is mounted through canonical attention layout rails so pane materialization remains commit-driven and focus-scoped.

## Canonical Direction

Non-negotiable invariants:

- Attention owns layout/section/focus-scope contracts.
- Hub must consume `ThreadLayout -> LayoutSection -> SectionFocusScope -> FocusScope` rails only.
- Interface behavior remains render-only over materialized focus selection.
- No direct custom navigation rail, no view routing bypass, no side state model.

## Current Truth (Repo State)

Exists today:

- Attention layout compiler spec package:
  - `modules/attention/docs/specs/layout-compiler/SPEC.md`
  - `modules/attention/docs/specs/layout-compiler/phases/01-grammar-token-and-ir-contract-freeze/README.md`
- Orchestrator-attention IPC proof confirms projection-commit/materialization boundary.

Missing today:

- Hub-specific consumer contract that binds experience intent to attention ownership without assumptions.
- Approved implementation iteration that wires hub layout consumption end-to-end.

## Scope

In scope:

- Hub consumer-side attention layout contract.
- Explicit dependency boundaries to attention compiler/runtime ownership.

Out of scope:

- Attention grammar/IR/runtime implementation (owned by attention module).
- Interface UI design details.
- Program bind closure and advanced layout features.

## Integration Contract

Boundaries:

- Attention module remains producer of layout/section/focus contract artifacts.
- Hub experience is a consumer of those artifacts.
- Orchestrator/interface layers materialize from committed focus state only.

## Data / Identity / Mutation Rules

Fail-closed rules:

- Do not attach hub semantics directly to UI state.
- Do not introduce direct thread-to-focus ownership in hub contracts.
- Stable IDs must come from canonical generated formulas; no ad-hoc derivation.

## Evidence And Testing Contract

Required proofs for implementation iterations (later phases):

- Attention compile proof:
  - `aware-cli compile module attention`
- Boundary proof:
  - `uv run pytest -q modules/orchestrator/runtime/tests/test_thread_attention_module_proof.py`
- IPC/materialization proof:
  - `cd modules/orchestrator/representation && FLUTTER_SUPPRESS_ANALYTICS=true flutter test test/orchestrator_attention_ipc_live_test.dart`

## Work Governance

- Phases ledger: `PHASES.md`
- Iterations protocol: `iterations/PROTOCOL.md`
- Phase directories: `phases/<phase_order>-<phase_slug>/README.md`
- Active iteration artifacts: `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
