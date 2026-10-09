# Phase 02 — Workspace Profile Contract

State: `Planned`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

## Gate

Workspace-experience has a frozen machine-readable profile and seed contract that declares root surfaces, bundle toggles, and provider-facing outputs.

## Goal

Turn the FS-first seed/layout direction into an explicit profile contract so later callers and downstream services consume declared workspace shape rather than CLI flag folklore.

## Scope In

- profile identifiers and defaults
- root-surface toggles
- bundle toggles and artifact outputs
- provider-facing workspace seed metadata

## Scope Out

- Structure workspace-service runtime implementation
- canonical `.aware` workspace operator semantics
- compile/test/diagnostic backend transport

## Acceptance (Gate Checklist)

- [ ] Profile fields and defaults are explicit.
- [ ] Emitted artifacts and contracts are frozen enough for downstream consumers.
- [ ] The bootstrap report and provider-facing metadata align to the same contract.

## Iterations

- `TBD`
