# Phase 00 — Spec Gate

State: `In Progress`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

## Gate

`workspace-operator` has a real owner spec package that locks profiles/seed/layout ownership and the service boundary to Structure workspace service.

## Goal

Create the initial spec package, freeze the owner direction, and record the first approved iteration artifact so future work does not keep relitigating where workspace seed/layout truth belongs.

## Scope In

- `libs/workspace-operator/docs/specs/workspace-operator/`
- `docs/issues/2026/03/17/fb-2026-03-17-workspace-operator-spec-bootstrap-v0.md`
- `docs/issues/2026/03/17/issues-2026-03-17.md`
- `docs/feed/2026/03/17.md`

## Scope Out

- implementation changes to `aware_workspace_operator`
- Structure workspace-service code changes
- robotics workspace scaffold mutation
- commit/quality/operator behavior changes

## Acceptance (Gate Checklist)

- [x] The spec package exists with canonical entrypoints.
- [x] The owner boundary is explicit and non-overlapping with Structure workspace service.
- [x] The phase plan covers FS-first seed/layout, profile contract, service consumption boundary, and canonical `.aware` workspace operators.
- [x] The first approved iteration artifact exists and records the bounded docs-only scope.

## Iterations

- `iterations/00-2026-03-17-spec-bootstrap/README.md`
